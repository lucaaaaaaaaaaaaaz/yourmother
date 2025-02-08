import requests
import time
from telegram import Bot

# Configurações do Telegram
TELEGRAM_TOKEN = "8111108757:AAEGDutj4RjR5yKLff2Y_dbbqWfW15QH8Ssm"
TELEGRAM_CHAT_ID = "1024065103"

# Endereço de interesse na Solana
SOLANA_ADDRESS = "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"

# Inicializa o bot do Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# Lista para armazenar assinaturas já processadas
processed_signatures = set()

def send_telegram_message(message):
    """Envia mensagem no Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("🔔 Alerta enviado no Telegram!")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")

def get_latest_transactions():
    """Obtém as últimas transações do endereço monitorado."""
    response = requests.post("https://api.mainnet-beta.solana.com", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [SOLANA_ADDRESS, {"limit": 50}]  # Ajustável
    })

    if response.status_code == 200:
        return response.json().get("result", [])
    return []

def get_transaction_details(signature):
    """Obtém detalhes de uma transação específica."""
    response = requests.post("https://api.mainnet-beta.solana.com", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, "jsonParsed"]
    })

    if response.status_code == 200:
        return response.json().get("result", {})
    return {}

def monitor_transactions():
    print("🚀 Monitoramento iniciado...")
    
    while True:
        transactions = get_latest_transactions()

        for tx in transactions:
            signature = tx["signature"]

            # Ignorar se já analisamos essa transação
            if signature in processed_signatures:
                continue
            
            # Adiciona ao histórico de transações processadas
            processed_signatures.add(signature)

            # Obtém detalhes da transação
            tx_details = get_transaction_details(signature)
            log_messages = tx_details.get("meta", {}).get("logMessages", [])

            # Verifica se a instrução desejada está nos logs
            for log in log_messages:
                if "InitializePermissionlessConstantProductPoolWithConfig" in log:
                    message = f"🚨 Nova pool detectada!\n🔗 Tx: https://solana.fm/tx/{signature}\n📜 Instrução: {log}"
                    send_telegram_message(message)
                    break  # Para evitar múltiplos alertas da mesma transação

        # Aguarda um tempo antes de verificar novamente
        time.sleep(10)  # Ajustável para um monitoramento mais rápido/lento

if __name__ == "__main__":
    monitor_transactions()
