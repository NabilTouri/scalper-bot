from scalper_bot.utils.logger import logger
from scalper_bot.trading.connector import Connector
import asyncio
import signal
import sys

# Global variable to handle graceful shutdown
shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Shutdown signal received...")
    shutdown_event.set()

async def main():
    logger.info("Avvio del bot...")

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Inizializza il connettore del broker
    connector = Connector()

    # Controlla lo stato dell'account
    account_info = connector.get_account_info()
    if not account_info:
        logger.error("Impossibile ottenere informazioni sull'account. Uscita.")
        return
    else:
        logger.info(f"Account Info: Status = {account_info.status.value}, Equity = ${account_info.equity}, Cash = ${account_info.cash}")


    try:
        # Avvia lo stream di dati
        await connector.stream()

        # Keep the bot running and listening for data
        logger.info("Bot running... Press Ctrl+C to stop")
        while not shutdown_event.is_set():
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Fermato manualmente dall'utente.")
    except Exception as e:
        logger.error(f"Error during streaming: {e}")
    finally:
        # Disconnetti lo stream quando il bot si ferma
        logger.info("Shutting down bot...")
        await connector.disconnect()
        logger.info("Bot terminato.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.critical(f"Errore critico non gestito: {e}")
        sys.exit(1)