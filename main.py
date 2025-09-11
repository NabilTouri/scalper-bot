from scalper_bot.utils.logger import logger
from scalper_bot.trading.broker_connector import BrokerConnector
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
    broker = BrokerConnector()

    # Controlla lo stato dell'account
    account_info = broker.get_account_info()
    if not account_info:
        logger.error("Impossibile ottenere informazioni sull'account. Uscita.")
        return

    # Check market status
    try:
        clock = broker.trading_client.get_clock()
        logger.info(f"Market is {'OPEN' if clock.is_open else 'CLOSED'}")
        logger.info(f"Next market open: {clock.next_open}")
        logger.info(f"Next market close: {clock.next_close}")
    except Exception as e:
        logger.error(f"Error getting clock info: {e}")

    # Esempio di utilizzo: connettersi allo stream e ricevere dati
    async def simple_data_handler(bar):
        logger.info(f"Nuova barra ricevuta per {bar.symbol}: Open=${bar.open}, Close=${bar.close}, Volume={bar.volume}")

    symbols_to_trade = ["SPY"]  # Esempio di simboli da tradare

    try:
        # Avvia lo stream di dati
        await broker.connect_stream(simple_data_handler, symbols_to_trade)

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
        await broker.disconnect_stream()
        logger.info("Bot terminato.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.critical(f"Errore critico non gestito: {e}")
        sys.exit(1)
