import openai
from dotenv import load_dotenv
import os
import subprocess
import requests
from PIL import Image
import shutil
import time
import random
import logging
import sys

# Configuração para UTF-8 no console do Windows
if os.name == 'nt':
    os.system('chcp 65001')

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("instagram_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Função para ler arquivos de texto
def ferramenta_ler_arquivo(nome_arquivo):
    try:
        with open(nome_arquivo, "r", encoding='utf-8') as arquivo:
            return arquivo.read()
    except IOError as e:
        logger.error(f"Erro no carregamento de arquivo: {e}")
        return None

# <<< INÍCIO DA FUNÇÃO DE CONVERSÃO PNG PARA JPG >>>
def ferramenta_converter_png_para_jpg(caminho_imagem, nome_arquivo):
    """
    Converte uma imagem PNG para JPG
    
    Args:
        caminho_imagem (str): Caminho completo para o arquivo PNG
        nome_arquivo (str): Nome base do arquivo (sem extensão)
    
    Returns:
        str: Caminho do arquivo JPG convertido ou None em caso de erro
    """
    try:
        logger.info(f"Convertendo {caminho_imagem} para JPG...")
        
        # Verifica se o arquivo PNG existe
        if not os.path.exists(caminho_imagem):
            logger.error(f"Erro: Arquivo {caminho_imagem} não encontrado.")
            return None
        
        # Abre a imagem PNG
        img_png = Image.open(caminho_imagem)
        
        # Se a imagem tiver canal alpha (transparência), converte para RGB
        if img_png.mode in ('RGBA', 'LA', 'P'):
            # Cria um fundo branco para substituir a transparência
            rgb_img = Image.new('RGB', img_png.size, (255, 255, 255))
            if img_png.mode == 'P':
                img_png = img_png.convert('RGBA')
            rgb_img.paste(img_png, mask=img_png.split()[-1] if img_png.mode == 'RGBA' else None)
            img_png = rgb_img
        elif img_png.mode != 'RGB':
            img_png = img_png.convert('RGB')
        
        # Define o caminho do arquivo JPG
        # Remove a extensão .png e adiciona .jpg
        caminho_jpg = caminho_imagem.rsplit('.', 1)[0] + ".jpg"
        
        # Salva a imagem como JPG com qualidade alta
        img_png.save(caminho_jpg, "JPEG", quality=95, optimize=True)
        
        logger.info(f"Imagem convertida e salva em: {caminho_jpg}")
        
        # Fecha a imagem para liberar memória
        img_png.close()
        
        return caminho_jpg
        
    except Exception as e:
        logger.error(f"Erro ao converter imagem {caminho_imagem} para JPG: {e}")
        return None
# <<< FIM DA FUNÇÃO DE CONVERSÃO PNG PARA JPG >>>

# <<< INÍCIO DA FUNÇÃO DE POSTAGEM NO INSTAGRAM COM INSTABOT >>>
def postar_instagram(caminho_imagem, texto, user, password):
    """
    Posta uma imagem no Instagram usando Instabot
    
    Args:
        caminho_imagem (str): Caminho completo para o arquivo de imagem JPG
        texto (str): Texto para a legenda da postagem
        user (str): Nome de usuário do Instagram
        password (str): Senha do Instagram
    
    Returns:
        bool: True se a postagem foi bem-sucedida, False caso contrário
    """
    try:
        logger.info(f"Preparando para postar no Instagram como {user} usando Instabot...")
        
        # Verifica se o arquivo de imagem existe
        if not os.path.exists(caminho_imagem):
            logger.error(f"Erro: Arquivo de imagem {caminho_imagem} não encontrado.")
            return False
            
        # Verifica se a imagem é JPG (o Instagram requer JPG)
        if not caminho_imagem.lower().endswith('.jpg'):
            logger.error(f"Erro: A imagem deve estar no formato JPG. Formato atual: {os.path.splitext(caminho_imagem)[1]}")
            return False
            
        # Verifica se as credenciais foram fornecidas
        if not user or not password:
            logger.error("Erro: Credenciais do Instagram não fornecidas.")
            return False
        
        # Cria um arquivo de log da postagem
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_file = os.path.join(log_dir, f"instagram_post_log_{timestamp}.txt")
        
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Usuário: {user}\n")
            f.write(f"Imagem: {caminho_imagem}\n")
            f.write(f"Legenda:\n{texto}\n")
        
        logger.info(f"Log da postagem salvo em: {log_file}")
        
        # Verifica se o módulo imghdr está disponível
        try:
            import imghdr
            logger.info("Módulo imghdr encontrado, usando Instabot normalmente")
        except ImportError:
            logger.info("Módulo imghdr não encontrado, criando módulo temporário")
            # Cria um módulo imghdr temporário
            sys.modules['imghdr'] = type('imghdr', (), {
                'what': lambda file, h=None: 'jpeg'
            })
        
        # Importa o Instabot após resolver a questão do imghdr
        try:
            from instabot import Bot
            logger.info("Instabot importado com sucesso")
        except ImportError:
            logger.error("Erro: Instabot não está instalado. Execute 'pip install instabot'")
            return False
        
        # Remove a pasta config se existir (para evitar problemas de sessão)
        if os.path.exists("config"):
            logger.info("Removendo pasta config antiga...")
            shutil.rmtree("config")
        
        # Inicializa o bot
        bot = Bot()
        
        # Tenta fazer login
        logger.info(f"Fazendo login no Instagram como {user}...")
        login_success = bot.login(username=user, password=password)
        
        if not login_success:
            logger.error("Falha no login do Instagram. Verifique suas credenciais.")
            return False
        
        # Tenta fazer o upload da imagem
        logger.info(f"Enviando imagem {caminho_imagem} para o Instagram...")
        upload_success = bot.upload_photo(caminho_imagem, caption=texto)
        
        if not upload_success:
            logger.error("Falha ao fazer upload da imagem para o Instagram.")
            return False
        
        logger.info("Postagem realizada com sucesso!")
        
        # Atualiza o log com o status de sucesso
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("Status: Publicado com sucesso\n")
            
        return True
            
    except Exception as e:
        logger.error(f"Erro ao postar no Instagram com Instabot: {e}")
        return False
# <<< FIM DA FUNÇÃO DE POSTAGEM NO INSTAGRAM COM INSTABOT >>>

# Função acessória para cortar o tamanho do arquivo
def cortar_audio(caminho_original, pasta_saida):
    logger.info("Cortando áudio em 3 partes...")

    duracao_parte = "00:25:35"
    pontos_de_inicio = ["00:00:00", "00:25:35", "00:51:10"]

    os.makedirs(pasta_saida, exist_ok=True)

    arquivos_cortados = []

    for i, inicio in enumerate(pontos_de_inicio, start=1):
        nome_saida = os.path.join(pasta_saida, f"parte{i}.mp3")
        comando = [
            "ffmpeg",
            "-i", caminho_original,
            "-ss", inicio,
            "-t", duracao_parte,
            "-acodec", "copy",
            nome_saida
        ]
        # Verifica se o arquivo de saída já existe
        if not os.path.exists(nome_saida):
            logger.info(f"Cortando {caminho_original} para {nome_saida}...")
            subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            logger.info(f"Arquivo {nome_saida} já existe. Pulando corte.")
        arquivos_cortados.append(nome_saida)

    return arquivos_cortados

# Função para transcrição de áudio usando OpenAI Whisper
def openai_whisper_transcrever(caminho_audio, nome_arquivo, modelo_whisper, client):
    logger.info(f"Transcrevendo {nome_arquivo} com Whisper...")

    with open(caminho_audio, "rb") as audio:
        resposta = client.audio.transcriptions.create(
            model=modelo_whisper,
            file=audio
        )

    transcricao = resposta.text
    
    # Salva a transcrição em arquivo de texto
    with open(f"texto_completo_{nome_arquivo}.txt", "w", encoding='utf-8') as arquivo_texto:
        arquivo_texto.write(transcricao)
    
    return transcricao

# Função para gerar resumo para Instagram usando GPT
def openai_gpt_resumir_texto(transcricao_completa, nome_arquivo, client):
    logger.info(f"Resumindo {nome_arquivo} com GPT...")
    
    prompt_sistema = """
    Você é um influenciador digital especializado em criptomoedas, blockchain e tecnologias descentralizadas, com uma comunidade engajada no Instagram.

    Características da sua persona: 
    - Você tem conhecimento técnico profundo, mas consegue explicar conceitos complexos de forma acessível
    - Seu tom é entusiasmado e visionário sobre o futuro das criptomoedas e Web3
    - Você está sempre atualizado sobre as últimas tendências, projetos e desenvolvimentos do mercado
    - Você mantém uma postura educativa, mas também compartilha análises e opiniões próprias

    Ao criar legendas para o Instagram:
    - Use linguagem neutra e inclusiva
    - Mantenha um tom conversacional e autêntico
    - Inclua uma introdução cativante que desperte curiosidade
    - Adicione um call-to-action claro para ouvir o conteúdo completo
    - Limite o texto a 1-2 parágrafos concisos para otimizar o engajamento no Instagram
    - Ocasionalmente, inclua emojis relevantes para tornar o texto mais dinâmico (🚀💰💎⛓️)

    Seu objetivo é transformar transcrições técnicas em legendas atraentes que convertam seguidores em ouvintes do seu conteúdo de áudio.
    """
    
    prompt_usuario = f"Rescreva a transcrição abaixo para que possa ser postada como uma legenda do Instagram. Ela deve resumir o texto para chamada na rede social. Não inclua hashtags, pois elas serão geradas separadamente.\n\n{transcricao_completa}"
    
    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role": "system",
                "content": prompt_sistema
            },
            {
                "role": "user",
                "content": prompt_usuario
            }
        ],
        temperature=0.6
    )
    
    resumo_instagram = resposta.choices[0].message.content
    
    with open(f"resumo_instagram_{nome_arquivo}.txt", "w", encoding='utf-8') as arquivo_texto:
        arquivo_texto.write(resumo_instagram)
    
    return resumo_instagram

# Função para gerar hashtags específicas
def openai_gpt_criar_hashtag(resumo_instagram, nome_arquivo, client):
    logger.info(f"Gerando hashtags para {nome_arquivo} com GPT...")
    
    prompt_sistema = """
    Assuma que você é um digital influencer digital e que está construindo conteúdos das áreas de tecnologia em uma plataforma de áudio (podcast).

    Os textos produzidos devem levar em consideração uma persona que consumirá os conteúdos gerados. Leve em consideração:

    - Seus seguidores são pessoas super conectadas da área de tecnologia, que amam consumir conteúdos relacionados aos principais temas da área de computação.
    - Você deve utilizar o gênero neutro na construção do seu texto
    - Os textos serão utilizados para convidar pessoas do instagram para consumirem seu conteúdo de áudio
    - O texto deve ser escrito em português do Brasil.
    - A saída deve conter 5 hashtags.
    - As hashtags devem ser específicas para o mercado de criptomoedas e blockchain.
    """

    # Correção na definição do prompt do usuário
    prompt_usuario = f'Aqui está um resumo de um texto "{resumo_instagram}". Por favor, gere 5 hashtags que sejam relevantes para este texto e que possam ser publicadas no Instagram. Por favor, faça isso em português do Brasil.'
    
    resposta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": prompt_sistema
            },
            {
                "role": "user",
                "content": prompt_usuario
            }
        ],
        temperature=0.6
    )
    
    hashtags = resposta.choices[0].message.content
    
    with open(f"hashtag_{nome_arquivo}.txt", "w", encoding='utf-8') as arquivo_texto:
        arquivo_texto.write(hashtags)
    
    return hashtags

# Função para gerar texto descritivo para imagem
def openai_gpt_gerar_texto_imagem(resumo_instagram, nome_arquivo, client):
    logger.info(f"Gerando texto descritivo para imagem de {nome_arquivo}...")
    
    prompt_sistema = """
    Você é um assistente que cria textos curtos e descritivos para modelos de geração de imagem.
    - A saída deve ser uma única frase curta, como um tweet, descrevendo visualmente o conteúdo.
    - A frase deve capturar a essência do texto fornecido, focando em elementos visuais e realistas.
    - Não inclua hashtags.
    - O texto deve ser em português.
    - Seja criativo e evite descrições genéricas.
    """

    prompt_usuario = f'Baseado no seguinte resumo de um conteúdo sobre criptomoedas: "{resumo_instagram}". Crie uma descrição visual curta e realista (estilo tweet, em português) para ser usada como prompt em um gerador de imagens como DALL-E. Foque em elementos concretos deixando a imagem menos bagunçada e fisicamente organizada. Busque imagens mais tendencias a cativação do ouvinte/leitor.'
    
    resposta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario}
        ],
        temperature=0.7 # Um pouco mais de criatividade
    )

    texto_para_imagem = resposta.choices[0].message.content

    with open(f"prompt_imagem_{nome_arquivo}.txt", "w", encoding='utf-8') as arquivo_texto:
        arquivo_texto.write(texto_para_imagem)

    return texto_para_imagem

# <<< INÍCIO DA FUNÇÃO DE GERAÇÃO DE IMAGEM ATUALIZADA >>>
def openai_dalle_gerar_imagem(resolucao, prompt_especifico, nome_arquivo_base, client, pasta_imagens, qtd_imagens=1):
    logger.info(f"Criando imagem para {nome_arquivo_base} com Dall-E 3...")
    
    try:
        # Chamada atualizada para a API DALL-E 3
        resposta = client.images.generate(
            model="dall-e-3",
            prompt=prompt_especifico, # Usa o prompt específico gerado
            n=qtd_imagens,
            size=resolucao,
            quality="standard", # ou "hd" para maior qualidade
            response_format="url" # Pede a URL da imagem
        )
        
        # Pega a URL da primeira imagem gerada
        url_imagem = resposta.data[0].url
        logger.info(f"URL da imagem gerada: {url_imagem}")

        # Define o caminho para salvar a imagem
        caminho_imagem_salva = os.path.join(pasta_imagens, f"{nome_arquivo_base}_imagem.png")

        # Baixa a imagem da URL
        logger.info(f"Baixando imagem de {url_imagem}...")
        resposta_imagem = requests.get(url_imagem, stream=True)
        resposta_imagem.raise_for_status() # Verifica se houve erro no download

        # Salva a imagem no arquivo local
        with open(caminho_imagem_salva, "wb") as f:
            for chunk in resposta_imagem.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Imagem salva em: {caminho_imagem_salva}")
        return caminho_imagem_salva

    except openai.APIError as e:
        logger.error(f"Erro na API OpenAI DALL-E: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao baixar a imagem: {e}")
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado ao gerar/salvar a imagem: {e}")
        
    return None # Retorna None em caso de erro
# <<< FIM DA FUNÇÃO DE GERAÇÃO DE IMAGEM ATUALIZADA >>>

# Função para aguardar entre postagens para evitar limites do Instagram
def aguardar_entre_postagens(minutos_min=2, minutos_max=5):
    """
    Aguarda um tempo aleatório entre postagens para evitar limites do Instagram
    
    Args:
        minutos_min (int): Tempo mínimo de espera em minutos
        minutos_max (int): Tempo máximo de espera em minutos
    """
    # Calcula um tempo aleatório entre minutos_min e minutos_max
    minutos = random.uniform(minutos_min, minutos_max)
    segundos = int(minutos * 60)
    
    logger.info(f"Aguardando {minutos:.1f} minutos entre postagens para evitar limites do Instagram...")
    
    # Mostra uma contagem regressiva para melhor feedback
    for i in range(segundos, 0, -30):
        if i % 60 == 0:
            logger.info(f"Aguardando mais {i//60} minutos...")
        time.sleep(30)
    
    logger.info("Tempo de espera concluído, continuando com a próxima postagem...")

# Função principal
def main():
    load_dotenv()

    # Inicializa o cliente OpenAI com a chave da API
    api_key = os.getenv("API_KEY_OPENAI")
    if not api_key:
        logger.error("Erro: Chave da API OpenAI não encontrada. Verifique o arquivo .env")
        return
    client = openai.OpenAI(api_key=api_key)
    
    # Carrega credenciais do Instagram do arquivo .env
    usuario_instagram = os.getenv("USER_INSTAGRAM")
    senha_instagram = os.getenv("PASSWORD_INSTAGRAM")
    
    # Verifica se as credenciais do Instagram estão configuradas
    if not usuario_instagram or not senha_instagram:
        logger.warning("AVISO: Credenciais do Instagram não encontradas no arquivo .env")
        logger.warning("Para postar no Instagram, você precisa configurar:")
        logger.warning("- USER_INSTAGRAM: Nome de usuário do Instagram")
        logger.warning("- PASSWORD_INSTAGRAM: Senha do Instagram")
    
    # URL do podcast para incluir na legenda
    url_podcast = "https://www.youtub.com/watch?v=kkb2H83aq8w&t=1s"
    
    caminho_audio_original = "Audio/audio_podcast.mp3"
    pasta_cortes = "Audio/cortes"
    pasta_imagens = "Imagens" # Pasta para salvar as imagens
    modelo_whisper = "whisper-1"
    resolucao_imagem = "1024x1024" # Resolução padrão para DALL-E 3
    
    # Cria as pastas de saída se não existirem
    os.makedirs(pasta_cortes, exist_ok=True)
    os.makedirs(pasta_imagens, exist_ok=True)
    
    # Corta o áudio se necessário (opcional, pode ser feito manualmente antes)
    # arquivos_cortados = cortar_audio(caminho_audio_original, pasta_cortes)
    # logger.info(f"Áudio cortado em: {arquivos_cortados}")
    
    arquivos_processados = [] 
    
    logger.info("Iniciando processo...")
    
    # Contador de postagens bem-sucedidas
    postagens_sucesso = 0
    
    for i in range(1, 4):  # Processando as 3 partes
        nome_parte = f"parte{i}"
        caminho_parte_audio = os.path.join(pasta_cortes, f"{nome_parte}.mp3")
        
        # Nomes dos arquivos de texto e imagem
        arquivo_transcricao_txt = f"texto_completo_{nome_parte}.txt"
        arquivo_resumo_txt = f"resumo_instagram_{nome_parte}.txt"
        arquivo_hashtags_txt = f"hashtag_{nome_parte}.txt"
        arquivo_prompt_imagem_txt = f"prompt_imagem_{nome_parte}.txt"
        arquivo_imagem_gerada = os.path.join(pasta_imagens, f"{nome_parte}_imagem.png")
        
        logger.info(f"\n--- Processando Parte {i} ---")
        
        # Verifica se o arquivo de áudio existe para esta parte
        if not os.path.exists(caminho_parte_audio):
            logger.warning(f"Arquivo de áudio {caminho_parte_audio} não encontrado. Pulando parte {i}.")
            continue
        
        # 1. Verifica/Gera Transcrição
        transcricao = ferramenta_ler_arquivo(arquivo_transcricao_txt)
        if not transcricao:
            transcricao = openai_whisper_transcrever(caminho_parte_audio, nome_parte, modelo_whisper, client)
            if not transcricao:
                 logger.error(f"Falha ao transcrever {nome_parte}. Pulando.")
                 continue # Pula se a transcrição falhar
        else:
            logger.info(f"Transcrição carregada de {arquivo_transcricao_txt}")

        # 2. Verifica/Gera Resumo
        resumo_instagram = ferramenta_ler_arquivo(arquivo_resumo_txt)
        if not resumo_instagram:
            resumo_instagram = openai_gpt_resumir_texto(transcricao, nome_parte, client)
            if not resumo_instagram:
                 logger.error(f"Falha ao resumir {nome_parte}. Pulando.")
                 continue
        else:
            logger.info(f"Resumo carregado de {arquivo_resumo_txt}")

        # 3. Verifica/Gera Hashtags
        hashtags = ferramenta_ler_arquivo(arquivo_hashtags_txt)
        if not hashtags:
            hashtags = openai_gpt_criar_hashtag(resumo_instagram, nome_parte, client)
            if not hashtags:
                 logger.error(f"Falha ao gerar hashtags para {nome_parte}. Pulando.")
                 continue
        else:
            logger.info(f"Hashtags carregadas de {arquivo_hashtags_txt}")
            
        # 4. Verifica/Gera texto para Imagem
        prompt_imagem = ferramenta_ler_arquivo(arquivo_prompt_imagem_txt)
        if not prompt_imagem:
            prompt_imagem = openai_gpt_gerar_texto_imagem(resumo_instagram, nome_parte, client)
            if not prompt_imagem:
                 logger.error(f"Falha ao gerar prompt de imagem para {nome_parte}. Pulando.")
                 continue
        else:
            logger.info(f"Texto de imagem carregado de {arquivo_prompt_imagem_txt}")
            
        # 5. Verifica/Gera Imagem com DALL-E
        caminho_imagem_final = None
        if os.path.exists(arquivo_imagem_gerada):
            logger.info(f"Imagem PNG carregada de {arquivo_imagem_gerada}")
            caminho_imagem_final = arquivo_imagem_gerada
        else:
            if prompt_imagem: # Só tenta gerar se tiver um prompt
                caminho_imagem_final = openai_dalle_gerar_imagem(resolucao_imagem, prompt_imagem, nome_parte, client, pasta_imagens)
                if not caminho_imagem_final:
                    logger.error(f"Falha ao gerar imagem para {nome_parte}.")
                    # Continua o processo mesmo sem imagem
            else:
                logger.warning(f"Pulando geração de imagem para {nome_parte} por falta de prompt.")
        
        # 6. Converte PNG para JPG
        caminho_imagem_convertida = None
        if caminho_imagem_final and caminho_imagem_final.endswith('.png'):
            caminho_imagem_convertida = ferramenta_converter_png_para_jpg(caminho_imagem_final, nome_parte)
            if caminho_imagem_convertida:
                logger.info(f"Imagem convertida para JPG: {caminho_imagem_convertida}")
            else:
                logger.error(f"Falha ao converter imagem para JPG: {caminho_imagem_final}")
                # Mantém o arquivo PNG original se a conversão falhar
                caminho_imagem_convertida = caminho_imagem_final
        else:
            caminho_imagem_convertida = caminho_imagem_final
            
        # 7. Posta no Instagram usando Instabot (sem confirmação)
        if caminho_imagem_convertida and usuario_instagram and senha_instagram:
            logger.info(f"Preparando para postar no Instagram para a parte {nome_parte}...")
            
            # Monta o texto completo para a postagem
            legenda_imagem = f"Link do Podcast: {url_podcast}\n{resumo_instagram}\n{hashtags}"
            
            # Se não for a primeira postagem, aguarda um tempo para evitar limites do Instagram
            if postagens_sucesso > 0:
                aguardar_entre_postagens(3, 5)  # Aguarda entre 3 e 5 minutos
            
            # Posta diretamente sem confirmação
            sucesso = postar_instagram(
                caminho_imagem_convertida,
                legenda_imagem,
                usuario_instagram,
                senha_instagram
            )
            
            if sucesso:
                postagens_sucesso += 1
                logger.info(f"Postagem {postagens_sucesso} realizada com sucesso!")
            else:
                logger.error(f"Falha na postagem {i}. Tentando continuar com as próximas...")
                
                # Se a postagem falhar, aguarda um tempo maior antes de tentar a próxima
                aguardar_entre_postagens(5, 8)  # Aguarda entre 5 e 8 minutos
        else:
            if not caminho_imagem_convertida:
                logger.warning(f"Pulando postagem no Instagram para {nome_parte}: imagem não disponível.")
            elif not usuario_instagram or not senha_instagram:
                logger.warning(f"Pulando postagem no Instagram para {nome_parte}: credenciais não configuradas.")
        
        # Armazena os resultados desta parte
        arquivos_processados.append({
            "parte": nome_parte,
            "resumo": resumo_instagram,
            "hashtags": hashtags,
            "prompt_imagem": prompt_imagem,
            "caminho_imagem_png": caminho_imagem_final, # Caminho da imagem PNG original
            "caminho_imagem_jpg": caminho_imagem_convertida # Caminho da imagem JPG convertida
        })
        
        logger.info(f"--- Processamento da Parte {i} concluído ---")

    # Imprimir todos os resultados no final
    logger.info("\n=== RESULTADOS FINAIS ===")
    logger.info(f"Total de postagens realizadas com sucesso: {postagens_sucesso} de 3")
    
    for dados_parte in arquivos_processados:
        logger.info(f"\nParte: {dados_parte['parte']}")
        logger.info(f"Resumo: {dados_parte['resumo']}")
        logger.info(f"Hashtags: {dados_parte['hashtags']}")
        logger.info(f"Prompt para Imagem: {dados_parte['prompt_imagem']}")
        logger.info(f"Caminho da Imagem PNG: {dados_parte['caminho_imagem_png']}")
        logger.info(f"Caminho da Imagem JPG: {dados_parte['caminho_imagem_jpg']}")
    logger.info("=========================")
    logger.info("\nProcesso concluído!")

if __name__ == "__main__":
    main()