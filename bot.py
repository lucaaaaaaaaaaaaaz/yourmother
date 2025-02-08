import requests
import time
from telegram import Bot

# Variáveis de ambiente
TELEGRAM_TOKEN = "SEU_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "SEU_CHAT_ID"
SOLANA_ADDRESS = "Eo7WjKq67rjJQSxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"

bot = Bot(token=TELEGRAM_TOKEN)
processed_signatures = set()  # Armazena transações já processadas

def send_telegram_message(message):
    """ Envia mensagem para o Telegram """
    print(f"Enviando mensagem: {message}")
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def monitor_transactions():
    """ Monitora transações do endereço no Solana """
    print("[✔] Iniciando monitoramento de transações...")
    
    while True:
        print("[✔] Verificando novas transações...")

        # Busca as últimas transações do endereço
        response = requests.post("https://api.mainnet-beta.solana.com", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [SOLANA_ADDRESS, {"limit": 150}]  # Busca apenas 150 para evitar spam
        })

        if response.status_code == 200:
            transactions = response.json().get("result", [])
            
            for tx in transactions:
                signature = tx['signature']
                if signature in processed_signatures:
                    continue  # Ignora transações já analisadas

                processed_signatures.add(signature)  # Marca como processada
                print(f"[✔] Nova transação detectada: {signature}")

                # Obtém detalhes da transação
                tx_details = requests.post("https://api.mainnet-beta.solana.com", json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [signature, "json"]
                }).json()

                if not tx_details.get("result"):
                    continue
                
                # Filtra transações que envolvem diretamente o endereço monitorado
                accounts = tx_details["result"].get("transaction", {}).get("message", {}).get("accountKeys", [])
                print(f"Contas envolvidas na transação: {accounts}")  # Mostra as contas envolvidas

                if SOLANA_ADDRESS not in accounts:
                    continue  # Ignora transações que não envolvem nosso endereço
                
                # Verifica logs para encontrar a instrução específica
                instructions = tx_details["result"].get("meta", {}).get("logMessages", [])
                for instruction in instructions:
                    if "Amm: Initialize Permissionless Constant Product Pool With Config" in instruction:
                        message = (
                            f"🚀 Nova pool detectada na Meteora!\n\n"
                            f"🔗 Transação: https://solscan.io/tx/{signature}\n"
                            f"🔍 Instrução: {instruction}"
                        )
                        send_telegram_message(message)
                        print("[✔] Alerta enviado no Telegram!")
                        break  # Sai do loop assim que encontrar a instrução
        else:
            print(f"[✖] Erro ao obter transações: {response.status_code}")
        
        print("[⏳] Aguardando 10 segundos antes de verificar novamente...")
        time.sleep(10)

if __name__ == "__main__":
    monitor_transactions()
