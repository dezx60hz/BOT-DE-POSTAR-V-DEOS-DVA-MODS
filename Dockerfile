FROM python:3.11-slim

# Instala o FFmpeg e dependências do sistema
RUN apt-get update && apt-get install -y ffmpeg libmagic1 && apt-get clean

WORKDIR /app
COPY . /app

# Instala as bibliotecas do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para iniciar o bot
CMD ["python", "main.py"]
