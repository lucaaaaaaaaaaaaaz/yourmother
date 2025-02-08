const axios = require("axios");
const { Telegraf } = require("telegraf"); // Biblioteca para enviar mensagens no Telegram

// Configurações
const apikey = "sk_live_637c217ee28e4fc19b79c244876797b6"; // Sua chave da API da Solana FM
const solanafmBaseUrl = "https://api.solana.fm";
const walletAddress = "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"; // Endereço da carteira a ser monitorada
const telegramBotToken = "8111108757:AAEGDutj4RjR5yKLff2Y_dbbqWfW15QH8Ss"; // Token do seu bot no Telegram
const telegramChatId = "1024065103"; // ID do chat no Telegram para enviar notificações

// Inicializa o bot do Telegram
const bot = new Telegraf(telegramBotToken);

// Variável para armazenar as transações já processadas
const processedTransactions = new Set();

// Função para enviar notificação no Telegram
const sendTelegramNotification = async (message) => {
  try {
    await bot.telegram.sendMessage(telegramChatId, message);
    console.log("Notificação enviada no Telegram:", message);
  } catch (error) {
    console.error("Erro ao enviar notificação no Telegram:", error);
  }
};

// Função principal para monitorar transações
const monitorTransactions = async () => {
  try {
    console.log("Iniciando monitoramento de transações...");

    while (true) {
      // Busca as transações mais recentes
      const response = await axios.get(`${solanafmBaseUrl}/v0/accounts/${walletAddress}/transactions`, {
        params: {
          utcFrom: Math.floor(Date.now() / 1000) - 60, // Últimos 60 segundos
          utcTo: Math.floor(Date.now() / 1000),
        },
        headers: {
          ApiKey: apikey,
        },
      });
console.log(response.data)
      const transactions = response.data.result;

      // Processa cada transação
      for (const transaction of transactions) {
        const transactionHash = transaction.transactionHash;

        // Verifica se a transação já foi processada
        if (!processedTransactions.has(transactionHash)) {
          processedTransactions.add(transactionHash); // Marca como processada

          // Verifica os logs da transação
          const logs = transaction.logs || [];
          const hasTargetLog = logs.some((log) =>
            log.includes("Program logged: Instruction: InitializePermissionlessConstantProductPoolWithConfig")
          );

          // Se a transação contiver a frase desejada, envia uma notificação no Telegram
          if (hasTargetLog) {
            const message = `Nova transação detectada!\nHash: ${transactionHash}\nLink: https://explorer.solana.com/tx/${transactionHash}`;
            await sendTelegramNotification(message);
          }
        }
      }

      // Aguarda 10 segundos antes de verificar novamente
      await new Promise((resolve) => setTimeout(resolve, 10000));
    }
  } catch (error) {
    console.error("Erro ao monitorar transações:", error);
  }
};

// Inicia o monitoramento
monitorTransactions();