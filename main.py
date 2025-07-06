import logging
import os
import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import pandas_ta as ta
from binance.client import Client
import pytz
from datetime import datetime

# Carregar variáveis do .env
load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Configuração do cliente da Binance
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Configuração do bot
bot = Bot(token=TOKEN)

# Configuração de logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Função para pegar o preço do BTC/BRL
def get_btc_price():
    ticker = client.get_symbol_ticker(symbol="BTCBRL")
    return float(ticker['price'])

# Função para calcular o RSI
def calculate_rsi():
    # Pegando os dados de 1h para o cálculo
    df = pd.DataFrame(client.get_historical_klines("BTCBRL", Client.KLINE_INTERVAL_1HOUR, "1 day ago UTC"))
    df = df.iloc[:, [0, 4]]  # Usando apenas as colunas de tempo e fechamento
    df.columns = ['timestamp', 'close']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Calculando o RSI
    df['RSI'] = ta.rsi(df['close'], length=14)
    return df['RSI'].iloc[-1]

# Função para enviar o sinal para o canal do Telegram
def send_signal(signal):
    bot.send_message(chat_id=CHANNEL_ID, text=signal)

# Função para verificar se é hora de enviar o sinal
def check_signal():
    price = get_btc_price()
    rsi = calculate_rsi()

    if rsi < 30:
        action = "COMPRA"
        tp = price * 1.02  # Exemplo de cálculo de TP
        sl = price * 0.98  # Exemplo de cálculo de SL
    elif rsi > 70:
        action = "VENDA"
        tp = price * 0.98
        sl = price * 1.02
    else:
        action = "ESPERAR"
        tp = None
        sl = None

    # Formatação da mensagem
    message = f"🟦 BTC/BRL\n🎯 Day Trade\n🦈 Situação: {action}\n💸 Preço: R${price}\n"
    if tp:
        message += f"🎯 TP: R${tp}\n"
    if sl:
        message += f"🛑 SL: R${sl}\n"
    message += f"📍 RSI 1h: {rsi}\n"

    # Enviar o sinal
    send_signal(message)

# Função agendada para enviar sinais às 8h e 12h
def schedule_signals():
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Brazil/East"))
    scheduler.add_job(check_signal, 'cron', hour=8, minute=0)  # Envia o sinal de Day Trade às 8h
    scheduler.add_job(check_signal, 'cron', hour=12, minute=0)  # Envia o sinal de Swing Trade às 12h
    scheduler.start()

# Função para iniciar o bot e o agendamento
def main():
    logging.info("Bot rodando, aguardando comandos... Fica esperto, porra!")
    
    # Rodando o agendador
    schedule_signals()
    
    # Configuração do Updater
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Adicionando o comando /preco
    dispatcher.add_handler(CommandHandler("preco", lambda update, context: update.message.reply_text(f"Preço atual do BTC/BRL: R${get_btc_price()}")))

    # Iniciar o polling do bot
    updater.start_polling()

if __name__ == '__main__':
    main()
