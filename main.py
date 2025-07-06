import os
import requests
import datetime
import pytz
from binance.client import Client
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from telegram import Bot

load_dotenv()

API_KEY = os.getenv("API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = Client()
bot = Bot(token=BOT_TOKEN)
scheduler = BlockingScheduler()

def get_price():
    ticker = client.get_symbol_ticker(symbol="BTCBRL")
    return float(ticker["price"])

def get_rsi(interval):
    klines = client.get_klines(symbol="BTCBRL", interval=interval, limit=100)
    closes = [float(k[4]) for k in klines]
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def analyze():
    now = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
    if now.hour == 8:
        signal_type = "Day Trade"
    elif now.hour == 12:
        signal_type = "Swing Trade"
    else:
        return

    interval = Client.KLINE_INTERVAL_1H if signal_type == "Day Trade" else Client.KLINE_INTERVAL_4H
    rsi = get_rsi(interval)
    price = get_price()

    if rsi < 30:
        action = "COMPRA"
        tp = price * 1.012
        sl = price * 0.985
    elif rsi > 70:
        action = "VENDA"
        tp = price * 0.985
        sl = price * 1.012
    else:
        action = "SEGURA"
        tp = sl = price

    message = f"""🟦 BTC/BRL
🎯 {signal_type}
🦈 Situação: {action}
💸 Preço: R${price:,.0f}
🎯 TP: R${tp:,.0f}
🛑 SL: R${sl:,.0f}
📍 RSI {interval} = {rsi:.2f}"""

    bot.send_message(chat_id=CHANNEL_ID, text=message)

@scheduler.scheduled_job('cron', hour='8,12', minute=0)
def scheduled_analysis():
    analyze()

from telegram.ext import CommandHandler, Updater

def preco(update, context):
    price = get_price()
    update.message.reply_text(f"Preço atual do BTC/BRL: R${price:,.0f}")

def start_bot():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("preco", preco))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    start_bot()
    scheduler.start()
