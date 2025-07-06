import os
import requests
import pandas as pd
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=TOKEN)

def get_price():
    url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCBRL'
    response = requests.get(url)
    data = response.json()
    return float(data['price'])

def get_rsi(interval='1h', limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol=BTCBRL&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    closes = [float(candle[4]) for candle in data]
    df = pd.DataFrame(closes, columns=['close'])
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)

def gerar_sinal(rsi, preco, tipo):
    if rsi < 30:
        situacao = "COMPRA"
        tp = preco * 1.012
        sl = preco * 0.985
    elif rsi > 70:
        situacao = "VENDA"
        tp = preco * 0.985
        sl = preco * 1.012
    else:
        situacao = "ESPERAR"
        tp = sl = 0

    if tipo == "day":
        desc = f"📍 RSI 1h em {rsi}. Análise curta para movimentos rápidos."
    else:
        desc = f"📍 RSI 4h em {rsi}. Tendência mais ampla para posição de swing."

    if situacao == "ESPERAR":
        return f"🟦 BTC/BRL\n🎯 {('Day Trade' if tipo == 'day' else 'Swing Trade')}\n🦈 Situação: {situacao}\n💸 Preço: R${preco:,.2f}".replace(",", ".")
    
    return (
        f"🟦 BTC/BRL\n"
        f"🎯 {('Day Trade' if tipo == 'day' else 'Swing Trade')}\n"
        f"🦈 Situação: {situacao}\n"
        f"💸 Preço: R${preco:,.2f}\n"
        f"🎯 TP: R${tp:,.2f}\n"
        f"🛑 SL: R${sl:,.2f}\n"
        f"{desc}"
    ).replace(",", ".")

def send_signals():
    hora = pd.Timestamp.now(tz='America/Sao_Paulo').hour
    preco = get_price()
    if hora == 8:
        rsi = get_rsi('1h')
        mensagem = gerar_sinal(rsi, preco, tipo="day")
        bot.send_message(chat_id=CHAT_ID, text=mensagem)
    elif hora == 12:
        rsi = get_rsi('4h')
        mensagem = gerar_sinal(rsi, preco, tipo="swing")
        bot.send_message(chat_id=CHAT_ID, text=mensagem)
    else:
        print(f"[{hora}h] Ping feito só pra manter o bot acordado.")

def comando_preco(update, context):
    preco = get_price()
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"🟦 Preço atual do BTC/BRL: R${preco:,.2f}".replace(",", "."))

def main():
    from telegram.ext import Updater, CommandHandler
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("preco", comando_preco))
    updater.start_polling()

    scheduler = BlockingScheduler(timezone='America/Sao_Paulo')
    scheduler.add_job(send_signals, 'interval', minutes=20)
    scheduler.start()

if __name__ == '__main__':
    main()
