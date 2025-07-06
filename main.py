from binance.client import Client
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Pega a chave pública (API Key) da Binance
API_KEY = os.getenv("BINANCE_API_KEY")

# Inicializa o cliente Binance (sem a chave secreta, pois não vamos fazer trade)
client = Client(API_KEY)

# Função para pegar o preço do BTC/BRL
def get_btc_price():
    ticker = client.get_symbol_ticker(symbol="BTCBRL")
    return ticker['price']

# Função para enviar os sinais (simulação)
def send_signals():
    price = get_btc_price()
    # Verifica RSI ou outras condições e envia o sinal
    print(f"Enviando Sinal: O preço atual do BTC/BRL é R${price}")
    
    # Exemplo de formato de sinal
    signal = f"""
🟦 BTC/BRL
🎯 Day Trade
🦈 Situação: COMPRA
💸 Preço: R${price}
🎯 TP: R${float(price) * 1.02}  # Exemplo de cálculo de TP
🛑 SL: R${float(price) * 0.98}  # Exemplo de cálculo de SL
📍 RSI 1h acima de 65, candle de rompimento com volume crescente.

🧱 Swing Trade
🦈 Situação: COMPRA
💸 Preço: R${price}
🎯 TP: R${float(price) * 1.05}  # Exemplo de cálculo de TP para swing trade
🛑 SL: R${float(price) * 0.95}  # Exemplo de cálculo de SL para swing trade
📍 Gráfico 4h firme em tendência de alta com RSI subindo.
    """
    print(signal)  # Simulação de envio de sinal (substitua com o envio real para o Telegram)

# Agendando o envio de sinais
def schedule_signals():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_signals, 'interval', minutes=20)  # Checa o preço a cada 20 minutos
    scheduler.start()

# Função principal
def main():
    print("Bot rodando, aguardando comandos... Fica esperto, porra!")
    schedule_signals()  # Agendar os sinais
    try:
        while True:
            pass  # O bot ficará rodando, mas não fará nada até o agendamento ser acionado
    except (KeyboardInterrupt, SystemExit):
        print("Bot parado.")

# Rodando o bot
if __name__ == "__main__":
    main()
