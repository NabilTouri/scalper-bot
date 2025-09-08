from scalper_bot.utils.logger import logger
from scalper_bot.trading.broker_connector import BrokerConnector
import asyncio

async def main():
    logger.info("Avvio del bot...")

    # Inizializza il connettore del broker
    broker = BrokerConnector()

    # Controlla lo stato dell'account
    account_info = broker.get_account_info()
    if not account_info:
        logger.error("Impossibile ottenere informazioni sull'account. Uscita.")
        return

    # Esempio di utilizzo: connettersi allo stream e ricevere dati
    # In un'applicazione reale, il data_handler sarebbe una funzione più complessa
    async def simple_data_handler(bar):
        logger.info(f"Nuova barra ricevuta per {bar.symbol}: {bar}")

    symbols_to_trade = ["SPY"] # Esempio di simboli da tradare

    try:
        # Avvia lo stream di dati
        # In un'applicazione completa, questo verrebbe eseguito in un loop o come task di background
        await broker.connect_stream(simple_data_handler, symbols_to_trade)
    except KeyboardInterrupt:
        logger.info("Fermato manualmente dall'utente.")
    finally:
        # Disconnetti lo stream quando il bot si ferma
        await broker.disconnect_stream()
        logger.info("Bot terminato.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Errore critico non gestito: {e}")
