import requests
import time
from telegram import Bot
from PIL import Image
import imagehash
from io import BytesIO

# Variáveis de ambiente
TELEGRAM_TOKEN = "8111108757:AAEGDutj4RjR5yKLff2Y_dbbqWfW15QH8Ss"
TELEGRAM_CHAT_ID = "1024065103"
SOLANA_ADDRESS = "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"  # Endereço Solana específico
IMAGE_URL = "https://raw.githubusercontent.com/lucaaaaaaaaaaaaaz/yourmother/refs/heads/main/Image.png"  # URL da imagem hospedada

bot = Bot(token=TELEGRAM_TOKEN)
processed_signatures = set()  # Armazena transações já processadas

def send_telegram_message(message):
    """ Envia mensagem para o Telegram """
    print(f"Enviando mensagem: {message}")
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def get_image_hash(image_url):
    """ Gera um hash da imagem """
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    return imagehash.average_hash(image)

def images_are_similar(hash1, hash2, threshold=5):
    """ Compara dois hashes de imagem e retorna True se forem semelhantes """
    return hash1 - hash2 < threshold

def monitor_transactions():
    """ Monitora transações do endereço no Solana """
    print("[✔] Iniciando monitoramento de transações...")
    reference_hash = get_image_hash(IMAGE_URL)  # Hash da imagem de referência
    
    while True:
        print("[✔] Verificando novas transações...")

        # Busca as últimas transações do endereço específico
        response = requests.post("https://api.mainnet-beta.solana.com", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [SOLANA_ADDRESS, {"limit": 200}]  # Busca apenas 200 transações para evitar spam
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

                # Verifica se o endereço específico está envolvido na transação
                if SOLANA_ADDRESS not in accounts:
                    continue  # Ignora transações que não envolvem o endereço específico
                
                # Verifica logs para encontrar a instrução específica
                instructions = tx_details["result"].get("meta", {}).get("logMessages", [])
                print(f"Logs encontrados: {instructions}")  # Mostra todos os logs

                # Verifique se a imagem específica está no log
                for instruction in instructions:
                    if "image.png" in instruction:  # Busca pela string que representa a imagem
                        # Aqui você pode adicionar a lógica para baixar e comparar a imagem
                        # Suponha que você tenha uma URL para a imagem na transação
                        transaction_image_url = "https://raw.githubusercontent.com/lucaaaaaaaaaaaaaz/yourmother/refs/heads/main/Image.png"  # Substitua pelo URL real
                        transaction_image_hash = get_image_hash(transaction_image_url)
                        
                        if images_are_similar(reference_hash, transaction_image_hash):
                            message = (
                                f"🚀 Imagem semelhante detectada na transação!\n\n"
                                f"🔗 Transação: https://solscan.io/tx/{signature}\n"
                                f"🔍 Log: {instruction}"
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
