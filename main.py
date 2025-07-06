import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# Carregar variáveis do .env
load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

if TOKEN is None:
    print("Porra, não encontrei o BOT_TOKEN! Faz a porra do .env direito!")
    exit(1)

# Configuração de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Função para pegar o preço do BTC/BRL
def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCBRL"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            price = float(data['price'])
            return price
        else:
            print(f"Erro ao acessar a API Binance. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao pegar o preço: {str(e)}")
        return None

# Função para pegar o RSI
def get_rsi():
    try:
        url = "https://api.binance.com/api/v3/indicator/rsi?symbol=BTCBRL&interval=1h"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rsi = float(data['rsi'])
            return rsi
        else:
            print(f"Erro ao acessar a API para RSI. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao pegar o RSI: {str(e)}")
        return None

# Comando de inicialização /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Bot funcionando! Fica esperto, porra!')

# Comando para pegar o preço do BTC/BRL
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    price = get_btc_price()
    if price:
        await update.message.reply_text(f"🟦 BTC/BRL: R${price:,.2f}")
    else:
        await update.message.reply_text("Erro ao pegar o preço. Tenta de novo mais tarde.")

# Função de envio de sinais
def send_signals():
    price = get_btc_price()
    rsi = get_rsi()
    if price is None or rsi is None:
        return

    if rsi < 30:  # Sinal de compra
        action = "COMPRA"
        tp = price * 1.02  # TP 2% para Day Trade
        sl = price * 0.98  # SL 2% para Day Trade
    elif rsi > 70:  # Sinal de venda
        action = "VENDA"
        tp = price * 0.98  # TP de -2% para Day Trade
        sl = price * 1.02  # SL 2% para proteger
    else:  # Esperar
        action = "ESPERAR"
        tp = price * 1.02  # TP 2% para Swing Trade
        sl = price * 0.98  # SL 2% para Swing Trade

    signal = f"""
    🟦 BTC/BRL
    🎯 Ação: {action}
    💸 Preço: R${price:,.2f}
    🎯 TP: R${tp:,.2f}
    🛑 SL: R${sl:,.2f}
    📍 RSI: {rsi} - {action} agora!
    """

    send_signal_to_channel(signal)

# Função para enviar o sinal para o canal do Telegram
def send_signal_to_channel(signal):
    application = Application.builder().token(TOKEN).build()
    application.bot.send_message(chat_id=CHANNEL_ID, text=signal)

# Função para agendar os sinais de compra/venda
def schedule_signals():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_signals, 'interval', minutes=20)  # Checa o preço a cada 20 minutos
    scheduler.start()

    scheduler.add_job(lambda: send_signals(), 'cron', hour=8, minute=0)  # Day Trade às 8:00
    scheduler.add_job(lambda: send_signals(), 'cron', hour=12, minute=0)  # Swing Trade às 12:00

# Função principal
def main():
    # Criando o bot usando a versão 20.x do python-telegram-bot
    application = Application.builder().token(TOKEN).build()

    # Adicionando comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))

    # Iniciando o bot
    print("Bot rodando, aguardando comandos... Fica esperto, porra!")  # Exibe no console
    schedule_signals()  # Agendar os sinais
    application.run_polling()  # Rodar o bot

if __name__ == '__main__':
    main()  # Rodar o bot sem Flask
