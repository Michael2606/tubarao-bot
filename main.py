import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
import asyncio

# Carregar variáveis do .env
load_dotenv()

# Recupera as variáveis do .env
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

if TOKEN is None:
    print("Caralho! Não encontrou o BOT_TOKEN, faz a porra do .env direito!")
    exit(1)

# Configuração de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Função de obtenção do preço de BTC/BRL
def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCBRL"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                price = float(data['price'])
                print(f"Preço Atual de BTC/BRL: R${price:,.2f}")  # Exibe o preço no console
                return price
            else:
                print("Erro: 'price' não encontrado na resposta da API. Caralho, que merda!")
                return "Erro: 'price' não encontrado na resposta da API"
        else:
            print(f"Erro ao acessar a API. Status {response.status_code}. Merda!")
            return f"Erro: Status {response.status_code} ao acessar a API"
    except Exception as e:
        print(f"Erro: {str(e)}")
        return f"Erro: {str(e)}"

# Função para obter o RSI da Binance (indicador de sobrecompra/sobrevenda)
def get_rsi():
    try:
        url = "https://api.binance.com/api/v3/indicator/rsi?symbol=BTCBRL&interval=1h"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'rsi' in data:
                rsi = float(data['rsi'])
                print(f"RSI Atual de BTC/BRL: {rsi}")  # Exibe o RSI no console
                return rsi
            else:
                print("Erro: 'rsi' não encontrado na resposta da API.")
                return "Erro: 'rsi' não encontrado na resposta da API"
        else:
            print(f"Erro ao acessar a API para RSI. Status {response.status_code}.")
            return f"Erro: Status {response.status_code} ao acessar a API para RSI"
    except Exception as e:
        print(f"Erro: {str(e)}")
        return f"Erro: {str(e)}"

# Função de comando start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Bot funcionando!')
    print("Bot funcionando, porra!")  # Exibe no console que o bot está funcionando

# Função de comando price
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    price = get_btc_price()
    if isinstance(price, float):
        await update.message.reply_text(f"🟦 BTC/BRL: R${price:,.2f}\nBot funcionando e online!")
    else:
        await update.message.reply_text(price)  # Caso haja erro ao pegar o preço

# Função para enviar os sinais (compra, venda ou esperar) com base no RSI
def send_signals():
    price = get_btc_price()
    rsi = get_rsi()

    if isinstance(price, float) and isinstance(rsi, float):
        # Decisão de Ação com base no RSI:
        if rsi < 30:  # Se o RSI estiver abaixo de 30 (sobrevendido), é hora de comprar
            action = "COMPRA"
            tp = price * 1.02  # TP de 2% para Day Trade
            sl = price * 0.98  # SL de 2% para Day Trade
        elif rsi > 70:  # Se o RSI estiver acima de 70 (sobrecomprado), é hora de vender
            action = "VENDA"
            tp = price * 0.98  # TP de -2% para Day Trade (vender no topo)
            sl = price * 1.02  # SL de 2% para proteger a venda
        else:  # RSI entre 30 e 70, zona neutra, esperar
            action = "ESPERAR"
            tp = price * 1.02  # TP de 2% para Swing Trade
            sl = price * 0.98  # SL de 2% para Swing Trade

        # Formatar o sinal de acordo com a ação (COMPRA, VENDA, ESPERAR)
        signal = f"""
        🟦 BTC/BRL
        🎯 Ação: {action}
        💸 Preço: R${price:,.2f}
        🎯 TP: R${tp:,.2f}
        🛑 SL: R${sl:,.2f}
        📍 RSI: {rsi} - {action} agora!
        """

        # Enviar os sinais para o canal
        send_signal_to_channel(signal)
        print(f"Sinal {action} Enviado: {signal}")  # Exibe o sinal no console

# Função de envio de sinal para o canal
def send_signal_to_channel(signal):
    bot = Application.builder().token(TOKEN).build()
    bot.bot.send_message(chat_id=CHANNEL_ID, text=signal)
    print(f"Sinal enviado para o canal: {signal}")  # Exibe no console que o sinal foi enviado

# Função para configurar e agendar o envio dos sinais
def schedule_signals():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_signals, 'interval', minutes=20)  # Checa o preço a cada 20 minutos
    scheduler.start()

    # Enviar sinais de compra, venda ou esperar nas horas certas
    scheduler.add_job(lambda: send_signals(), 'cron', hour=8, minute=0)  # Envia o Day Trade às 8:00 AM
    scheduler.add_job(lambda: send_signals(), 'cron', hour=12, minute=0)  # Envia o Swing Trade às 12:00 PM

# Criação do Flask para manter o bot funcionando
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot rodando, caralho!"

# Função para rodar o Flask e o Bot juntos
def run():
    # Criando o loop assíncrono e configurando para o bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Iniciar o bot e o servidor Flask
    from threading import Thread
    bot_thread = Thread(target=main)
    bot_thread.start()
    
    app.run(host='0.0.0.0', port=8080)  # Porta pública do Render

# Função principal
def main():
    # Criando o bot usando a versão 20.x do python-telegram-bot
    application = Application.builder().token(TOKEN).build()

    # Adicionando comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))  # Comando /price

    # Iniciando o bot
    print("Bot rodando, aguardando comandos... Fica esperto, porra!")  # Exibe no console quando o bot começar
    schedule_signals()  # Agendar os sinais
    application.run_polling()

if __name__ == '__main__':
    run()  # Rodar o bot com Flask e asyncio
