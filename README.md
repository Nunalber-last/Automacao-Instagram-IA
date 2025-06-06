# Instagram Podcast Automation Bot

Este projeto é uma automação completa para criadores de conteúdo em áudio (como podcasts) que desejam transformar seus episódios em publicações impactantes no Instagram. Ele usa IA para transcrever, resumir, gerar imagens e postar automaticamente com legenda e hashtags.

## Funcionalidades

- Corta automaticamente áudios longos em partes menores  
- Transcreve áudio usando **Whisper** da OpenAI  
- Resume o conteúdo com linguagem cativante via **ChatGPT**  
- Gera hashtags relevantes e em português  
- Cria imagens com o **DALL·E 3**  
- Converte imagens para JPG se necessário  
- Posta no Instagram via **Instabot**  
- Adiciona tempo de espera entre postagens para evitar bloqueios  

## Pré-requisitos

- Python 3.9 ou superior  
- Conta OpenAI com acesso à API (Whisper, GPT e DALL·E)  
- Conta Instagram válida (usuário/senha)  
- FFMPEG instalado no sistema  

## Instalação

Clone o repositório:

```bash
git clone https://github.com/seu-usuario/nome-do-repositorio.git
cd nome-do-repositorio
```

Crie e ative um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
source venv/bin/activate  # no Windows: venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

##Configuração do arquivo .env
Crie um arquivo .env na raiz do projeto com o seguinte conteúdo:

```env
API_KEY_OPENAI=sua-chave-openai
USER_INSTAGRAM=seu-usuario
PASSWORD_INSTAGRAM=sua-senha
```

##Estrutura esperada de diretórios
```plaintext
.
├── Audio/
│   ├── audio_podcast.mp3
│   └── cortes/
├── Imagens/
├── main.py
├── .env
├── logs/
```
O áudio principal deve estar em Audio/audio_podcast.mp3. O script cortará automaticamente em 3 partes (cada uma com cerca de 25:35).

##Como usar?
1. Execute o script:
```bash
python main.py
```
O processo automatizado irá:
- Cortar o áudio (opcional)
- Transcrever cada parte com Whisper
- Resumir para uma legenda do Instagram
- Gerar hashtags com GPT
- Criar prompt visual e gerar imagem com DALL·E
- Converter imagem para JPG
- Postar automaticamente no Instagram

##Tecnologias utilizadas
- OpenAI API (GPT, Whisper, DALL·E)
- Instabot (voce pode escolhe um alternativo);
- FFMPEG;
- Python Dotenv.
