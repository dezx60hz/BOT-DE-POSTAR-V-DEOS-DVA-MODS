import os
import asyncio
import yt_dlp
import json
import requests
from instagrapi import Client
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# CONFIGURAÇÕES - O Render vai usar o Token que você colocar nas Variáveis de Ambiente
TOKEN = os.getenv('TELEGRAM_TOKEN', '8200558772:AAGHn7JMvE2iIk_nIpaUwsunGaW0im-0FUA')
USER_ACCOUNTS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot Ativo no Render!\n\nComandos:\n/link_instagram <usuario> <senha>\n\nEnvie um link do TikTok ou Instagram para baixar e postar automaticamente.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 Ajuda:\n1. Use /link_instagram para conectar sua conta.\n2. Envie o link do vídeo.\n3. O bot baixa sem marca d'água e posta no seu Insta.")

def download_video(url, output_path):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return {
            'file_path': ydl.prepare_filename(info),
            'description': info.get('description', ''),
            'title': info.get('title', '')
        }

async def link_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 2:
        await update.message.reply_text("❌ Erro! Use: /link_instagram <usuario> <senha>")
        return
    
    username, password = context.args
    cl = Client()
    try:
        msg = await update.message.reply_text("⏳ Tentando login no Instagram... Isso pode demorar.")
        # O Render tem IP fixo, o que ajuda a não dar erro de login
        cl.login(username, password)
        
        session_file = f'session_{user_id}.json'
        cl.dump_settings(session_file)
        
        USER_ACCOUNTS[user_id] = {
            'instagram': {
                'username': username, 
                'password': password, 
                'session': session_file
            }
        }
        await update.message.reply_text("🎉 Instagram vinculado com sucesso!")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro no login: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.effective_user.id
    
    if not url.startswith('http'):
        return

    status_msg = await update.message.reply_text("📥 Baixando vídeo sem marca d'água...")
    
    try:
        os.makedirs('downloads', exist_ok=True)
        # Download via yt-dlp (HD e sem marca d'água)
        info = await asyncio.to_thread(download_video, url, 'downloads')
        video_path = info['file_path']
        
        await status_msg.edit_text("📤 Vídeo baixado! Tentando postar no Instagram...")

        if user_id in USER_ACCOUNTS and 'instagram' in USER_ACCOUNTS[user_id]:
            acc = USER_ACCOUNTS[user_id]['instagram']
            cl = Client()
            
            # Carrega sessão para evitar bloqueios
            if os.path.exists(acc['session']):
                cl.load_settings(acc['session'])
            
            cl.login(acc['username'], acc['password'])
            
            # Posta como Reel
            caption = info['description'] if info['description'] else info['title']
            cl.video_upload(video_path, caption)
            
            await update.message.reply_text("🚀 Postado no Instagram com sucesso!")
        else:
            # Se não tiver conta vinculada, apenas envia o vídeo no Telegram
            with open(video_path, 'rb') as v:
                await update.message.reply_video(v, caption="Aqui está seu vídeo! Vincule seu Instagram para postagem automática.")
        
        # Limpa o arquivo para não encher o disco do Render
        if os.path.exists(video_path):
            os.remove(video_path)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ocorreu um erro: {str(e)}")

def main():
    # Cria a aplicação do bot
    application = Application.builder().token(TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("link_instagram", link_instagram))

    # Mensagens (Links)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot iniciado e aguardando mensagens...")
    application.run_polling()

if __name__ == '__main__':
    main()
