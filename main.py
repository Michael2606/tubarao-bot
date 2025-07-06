import logging
import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
import requests
import time
from datetime import datetime
import pytz

# Carregar as variáveis do .env
load_dotenv()

# Recupera as variáveis do .env
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

if TOKEN is None:
    print("Erro: BOT_TOKEN não encontrado no arquivo .env")
    exit(1)

# Seu ID de usuário do Telegram (coloquei o seu ID real aqui)
ADM_USER_ID = 7932105748  # Seu ID

# Configuração de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Função de envio de sinais
def send_signal_to_channel(signal):
    bot = Bot(TOKEN)
    bot.send_message(chat_id=CHANNEL_ID, text=signal)

# Função de obtenção do preço de BTC/BRL com verificação aprimorada
def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCBRL"
        response = requests.get(url)
        
        # Verificando se a resposta é válida
        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                return float(data['price'])
            else:
                return "Erro: 'price' não encontrado na resposta da API"
        else:
            return f"Erro: Status {response.status_code} ao acessar a API"
    except Exception as e:
        return f"Erro: {str(e)}"

# Comando /Price para verificar o preço e confirmar se o bot está online
def price(update, context):
    if update.message.from_user.id == ADM_USER_ID:  # Verifica se é o ADM
        price = get_btc_price()
        # Responde apenas com o preço, sem informações do usuário
        if isinstance(price, float):
            update.message.reply_text(f"🟦 BTC/BRL: R${price:,.2f}\nBot funcionando e online!")
        else:
            update.message.reply_text(price)  # Responde com erro caso algo dê errado
    else:
        update.message.reply_text('Você não tem permissão para usar esse comando.')

# Função de análise de mercado
def analyze_market():
    # Usando a API pública da Binance para obter o preço atual de BTC/BRL
    price = get_btc_price()

    # Obtendo os dados históricos de 1h para calcular RSI
    url_candles = "https://api.binance.com/api/v3/klines?symbol=BTCBRL&interval=1h&limit=100"
    response_candles = requests.get(url_candles)
    candles = response_candles.json()
    
    # Extraindo os preços de fechamento dos candles
    closes = [float(candle[4]) for candle in candles]

    # Calculando o RSI manualmente
    rsi = calculate_rsi(closes)

    # Análise para definir o TP e SL de forma dinâmica
    support = min(closes[-5:])
    resistance = max(closes[-5:])

    tp = resistance
    sl = support

    # Lógica de envio de sinais com base no RSI
    if rsi < 30:
        signal = (f"🟦 BTC/BRL\n"
                  f"🎯 Day Trade\n"
                  f"🦈 Situação: COMPRA\n"
                  f"💸 Preço: R${price:,.0f}\n"
                  f"🎯 TP: R${tp:,.0f}\n"
                  f"🛑 SL: R${sl:,.0f}\n"
                  f"📍 RSI 1h abaixo de 30, candlestick mostrando fundo sólido.\n\n"
                  f"🧱 Swing Trade\n"
                  f"🦈 Situação: COMPRA\n"
                  f"💸 Preço: R${price:,.0f}\n"
                  f"🎯 TP: R${tp:,.0f}\n"
                  f"🛑 SL: R${sl:,.0f}\n"
                  f"📍 RSI abaixo de 30 com possibilidade de recuperação.")
        send_signal_to_channel(signal)
    elif rsi > 70:
        signal = (f"🟦 BTC/BRL\n"
                  f"🎯 Day Trade\n"
                  f"🦈 Situação: VENDA\n"
                  f"💸 Preço: R${price:,.0f}\n"
                  f"🎯 TP: R${sl:,.0f}\n"
                  f"🛑 SL: R${tp:,.0f}\n"
                  f"📍 RSI 1h acima de 70, risco de reversão para baixa.\n\n"
                  f"🧱 Swing Trade\n"
                  f"🦈 Situação: VENDA\n"
                  f"💸 Preço: R${price:,.0f}\n"
                  f"🎯 TP: R${sl:,.0f}\n"
                  f"🛑 SL: R${tp:,.0f}\n"
                  f"📍 Tendência de reversão após forte alta, risco de queda.")
        send_signal_to_channel(signal)
    else:
        signal = (f"🟦 BTC/BRL\n"
                  f"🎯 Day Trade\n"
                  f"🦈 Situação: ESPERAR\n"
                  f"💸 Preço: R${price:,.0f}\n"
                  f"🎯 TP: R${tp:,.0f}\n"
                  f"🛑 SL: R${sl:,.0f}\n"
                  f"📍 RSI entre 30 e 70, mercado sem tendência clara.\n\n"
                  f"🧱 Swing Trade\n"
                  f"🦈 Situação: ESPERAR\n"
                  f"💸 Preço: R${price:,.0f}\n"
                  f"🎯 TP: R${tp:,.0f}\n"
                  f"🛑 SL: R${sl:,.0f}\n"
                  f"📍 Tendência lateral. Aguardando direção clara.")
        send_signal_to_channel(signal)

# Função de cálculo do RSI manualmente
def calculate_rsi(prices, period=14):
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change >= 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100  # Se não houver perda, RSI será 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Função de enviar os sinais uma vez por dia
def send_daily_signals():
    # Horário de Brasília
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)

    if now.hour == 8 and now.minute == 0:  # Enviar sinal de Day Trade às 8h
        analyze_market()
        print("Sinal de Day Trade enviado.")
    elif now.hour == 12 and now.minute == 0:  # Enviar sinal de Swing Trade às 12h
        analyze_market()
        print("Sinal de Swing Trade enviado.")
    else:
        print(f"Aguardando horário para enviar sinal... {now.strftime('%H:%M')}")

# Função principal
def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Comando start
    dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text('Bot funcionando!')))
    
    # Comando price
    dispatcher.add_handler(CommandHandler("price", price))  # Aqui adicionamos o comando /Price

    # Inicia o bot
    updater.start_polling()

    # Rodar a análise a cada 1 minuto
    while True:
        send_daily_signals()
        time.sleep(60)  # Espera 1 minuto antes de verificar novamente

if __name__ == '__main__':
    main()
