import os
import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import ApplicationBuilder, CommandHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Setup do bot
application = ApplicationBuilder().token(TOKEN).build()

# Função de ping na Binance
def ping_binance():
    try:
        response = requests.get("https://api.binance.com/api/v3/ping")
        if response.status_code == 200:
            print("✅ Binance OK")
        else:
            print(f"❌ Binance status: {response.status_code}")
    except Exception as e:
        print(f"💥 Erro ao pingar Binance: {e}")

# Comando de teste no bot
async def start(update, context):
    await update.message.reply_text("BOT 5.890.899 ATIVO FDP 🚀")

application.add_handler(CommandHandler("start", start))

# Agendador que pinga a cada 20 minutos
scheduler = BackgroundScheduler()
scheduler.add_job(ping_binance, "interval", minutes=20)
scheduler.start()

# Rodando o bot
if __name__ == "__main__":
    print("🤖 BOT INICIADO...")
    application.run_polling()
