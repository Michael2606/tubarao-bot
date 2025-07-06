import os
import requests
import logging
import telegram
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler
from binance.client import Client
from dotenv import load_dotenv
from datetime import datetime
import pytz
import numpy as np

# ⚙️ Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📈 Setup Binance API
client = Client()

# 🎯 Função para pegar o RSI
def get_rsi(symbol, interval, period=14):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=period + 1)
    closes = [float(kline[4]) for kline in klines]

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

# 💸 Pegar preço atual do BTC/BRL
def get_btc_brl_price():
    ticker = client.get_symbol_ticker(symbol="BTCBRL")
    return float(ticker["price"])

# 🧠 Lógica do sinal (usada nos dois agendamentos)
def gerar_sinal(tipo):
    symbol = "BTCBRL"
    intervalo = "1h" if tipo == "day" else "4h"
    rsi = get_rsi(symbol, interval=intervalo)
    preco = get_btc_brl_price()

    if rsi < 30:
        acao = "COMPRA"
        tp = preco * 1.012  # alvo
        sl = preco * 0.985  # stop
        contexto = f"RSI {intervalo} em sobrevenda, possível reversão. Volume deve confirmar entrada."
    elif rsi > 70:
        acao = "VENDA"
        tp = preco * 0.985
        sl = preco * 1.012
        contexto = f"RSI {intervalo} em sobrecompra, atenção a correção. Sinal de exaustão visível."
    else:
        acao = "ESPERAR"
        tp = preco
        sl = preco
        contexto = f"RSI {intervalo} neutro. Aguardar movimento mais claro para operar com segurança."

    return f"""🟦 BTC/BRL
🎯 {"Day Trade" if tipo == "day" else "Swing Trade"}
🦈 Situação: {acao}
💸 Preço: R${preco:,.0f}
🎯 TP: R${tp:,.0f}
🛑 SL: R${sl:,.0f}
📍 {contexto}""".replace(",", ".")

# 📬 Enviar sinal pro Telegram
async def send_sinal(tipo):
    mensagem = gerar_sinal(tipo)
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=mensagem)

# ⏰ Funções agendadas
def schedule_signals():
    scheduler = BackgroundScheduler(timezone=pytz.timezone("America/Sao_Paulo"))
    scheduler.add_job(lambda: app.create_task(send_sinal("day")), 'cron', hour=8, minute=0)
    scheduler.add_job(lambda: app.create_task(send_sinal("swing")), 'cron', hour=12, minute=0)
    scheduler.start()

# 💬 Comando /preco
async def preco(update, context):
    preco = get_btc_brl_price()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"📊 Preço do BTC/BRL agora: R${preco:,.2f}".replace(",", "."))

# 🚀 Main
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("preco", preco))
    schedule_signals()
    print("Bot rodando, aguardando comandos... Fica esperto, porra!")
    app.run_polling()
