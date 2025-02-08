import requests
import time
from telegram import Bot

# Configurações
TELEGRAM_TOKEN = "8111108757:AAEGDutj4RjR5yKLff2Y_dbbqWfW15QH8Ss"
TELEGRAM_CHAT_ID = "1024065103"
SOLANA_ADDRESS = "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"

bot = Bot(token=TELEGRAM_TOKEN)
processed_signatures = set()  # Armazena transações já analisadas

def send_telegram_message(message):
    """ Envia mensagem para o Telegram """
    print(f"Enviando mensagem: {message}")
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def monitor_transactions():
    """ Monitora transações do endereço no Solana """
    print("[✔] Iniciando monitoramento de transações...")

    while True:
        print("[✔] Verificando novas transações...")

        # Busca as últimas 50 transações do endereço monitorado
        response = requests.post("https://api.mainnet-beta.solana.com", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [SOLANA_ADDRESS, {"limit": 50}]
        })

        if response.status_code == 200:
            transactions = response.json().get("result", [])

            for tx in transactions:
                signature = tx['signature']
                if signature in processed_signatures:
                    continue  # Ignora transações já analisadas

                processed_signatures.add(signature)  # Marca como processada
                print(f"[✔] Nova transação detectada: {signature}")

                # Obtém detalhes completos da transação
                tx_details = requests.post("https://api.mainnet-beta.solana.com", json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [signature, "json"]
                }).json()

                if not tx_details.get("result"):
                    continue

                # Obtém contas envolvidas
                accounts = tx_details["result"]["transaction"]["message"].get("accountKeys", [])

                # Verifica se o endereço monitorado está na transação
                if SOLANA_ADDRESS not in accounts:
                    continue  # Ignora transações que não envolvem o endereço monitorado

                # Obtém mudanças de saldo de tokens (se houver)
                post_balances = tx_details["result"]["meta"].get("postTokenBalances", [])

                # Verifica se o endereço está em mudanças de saldo
                address_involved = any(
                    SOLANA_ADDRESS in (acc.get("owner", ""), acc.get("account", ""))
                    for acc in post_balances
                )

                # Se o endereço não estiver envolvido, ignora a transação
                if not address_involved:
                    continue

                print(f"[✔] Transação relevante detectada para {SOLANA_ADDRESS}")

                # Verifica logs para encontrar a instrução específica
                instructions = tx_details["result"]["meta"].get("logMessages", [])
                for instruction in instructions:
                    if "InitializePermissionlessConstantProductPoolWithConfig" in instruction:
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

        print("[⏳] Aguardando 15 segundos antes de verificar novamente...")
        time.sleep(15)

if __name__ == "__main__":
    monitor_transactions()
