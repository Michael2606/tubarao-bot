import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

HEADERS = {"User-Agent": "Mozilla/5.0"}
BINANCE_URL = "https://api.binance.com/api/v3/klines"
OKX_URL = "https://www.okx.com/api/v5/market/candles"

bot = Bot(token=TELEGRAM_TOKEN)

def get_binance_data(symbol):
    params = {"symbol": symbol, "interval": "1h", "limit": 100}
    response = requests.get(BINANCE_URL, headers=HEADERS, params=params)
    return response.json()

def get_okx_data(instId):
    params = {"instId": instId, "bar": "1H", "limit": 100}
    response = requests.get(OKX_URL, headers=HEADERS, params=params)
    return response.json()

def analisar_rsi(candles, is_okx=False):
    closes = [float(c[4]) if not is_okx else float(c[4]) for c in candles[-14:]]
    diffs = [closes[i+1] - closes[i] for i in range(len(closes) - 1)]
    ganhos = [d if d > 0 else 0 for d in diffs]
    perdas = [-d if d < 0 else 0 for d in diffs]

    media_ganho = sum(ganhos) / 13
    media_perda = sum(perdas) / 13
    rs = media_ganho / media_perda if media_perda != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

def gerar_sinal(nome, preco, rsi):
    if rsi < 30:
        situacao = "🎯 SINAL DE SWING TRADE\n🦈 Situação: COMPRA"
        alvo = preco * 1.04
        stop = preco * 0.96
    elif rsi > 70:
        situacao = "🎯 SINAL DE SWING TRADE\n🦈 Situação: VENDA"
        alvo = preco * 0.96
        stop = preco * 1.04
    else:
        return None

    return f"""{situacao}
💸 Preço: R${preco:,.2f}
🎯 Alvo (TP): R${alvo:,.2f}
🛑 Stop (SL): R${stop:,.2f}
📍Contexto: RSI em {rsi:.2f}. O ativo está em região de {'sobrecompra' if rsi > 70 else 'sobrevenda'}.
"""

def enviar_sinal(msg):
    bot.send_message(chat_id=CHANNEL_ID, text=msg)

def main():
    sinais = []

    # BTC/BRL (Binance)
    btc_data = get_binance_data("BTCBRL")
    btc_price = float(btc_data[-1][4])
    btc_rsi = analisar_rsi(btc_data)
    sinal_btc = gerar_sinal("BTC", btc_price, btc_rsi)
    if sinal_btc:
        sinais.append(f"📊 BTC/BRL (Binance)\n{sinal_btc}")

    # ETH/BRL (Binance)
    eth_data = get_binance_data("ETHBRL")
    eth_price = float(eth_data[-1][4])
    eth_rsi = analisar_rsi(eth_data)
    sinal_eth = gerar_sinal("ETH", eth_price, eth_rsi)
    if sinal_eth:
        sinais.append(f"📊 ETH/BRL (Binance)\n{sinal_eth}")

    # SOL/BRL (Binance)
    sol_data = get_binance_data("SOLBRL")
    sol_price = float(sol_data[-1][4])
    sol_rsi = analisar_rsi(sol_data)
    sinal_sol = gerar_sinal("SOL", sol_price, sol_rsi)
    if sinal_sol:
        sinais.append(f"📊 SOL/BRL (Binance)\n{sinal_sol}")

    # XRP/BRL (OKX)
    xrp_data = get_okx_data("XRP-BRL")
    xrp_price = float(xrp_data['data'][0][4])
    xrp_rsi = analisar_rsi(xrp_data['data'], is_okx=True)
    sinal_xrp = gerar_sinal("XRP", xrp_price, xrp_rsi)
    if sinal_xrp:
        sinais.append(f"📊 XRP/BRL (OKX)\n{sinal_xrp}")

    if sinais:
        hoje = datetime.now().strftime("%d/%m/%Y")
        header = f"📅 SINAIS DO DIA – {hoje}\n\n"
        mensagem = header + "\n".join(sinais)
        enviar_sinal(mensagem)

if __name__ == "__main__":
    main()
