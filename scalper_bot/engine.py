import asyncio
from .utils.logger import logger
from .config.settings import SYMBOLS, TIMEFRAME
from .trading.broker_connector import BrokerConnector
from .data.data_manager import DataManager
from .strategy.example_strategy import ExampleStrategy
from .trading.order_manager import OrderManager
from .trading.position_manager import PositionManager
from .trading.risk_manager import RiskManager

class TradingEngine:
    def __init__(self):
        logger.info("Inizializzazione del Trading Engine...")
        self.broker = BrokerConnector(paper=True)
        self.data_manager = DataManager(self.broker)
        self.position_manager = PositionManager(self.broker)
        self.risk_manager = RiskManager(self.broker, self.position_manager)
        self.order_manager = OrderManager(self.broker)
        self.strategy = ExampleStrategy(
            self.broker, self.order_manager, self.position_manager, self.risk_manager
        )
        self.strategy.logger = logger # Assegna il logger alla strategia
        self.is_running = True

    async def run(self):
        """Avvia il motore di trading."""
        logger.info("Avvio del Trading Engine.")
        
        # 1. Controlla l'account e inizializza i dati
        account_info = await self.risk_manager.update_account_info()
        if not account_info:
            logger.critical("Impossibile ottenere informazioni sull'account. Uscita.")
            return

        await self.data_manager.initialize_historical_data()
        await self.strategy.initialize()

        # 2. Avvia lo stream di dati in un task separato
        stream_task = asyncio.create_task(
            self.broker.connect_stream(self.on_bar, SYMBOLS)
        )
        
        logger.info("Trading Engine avviato. In attesa dei dati di mercato...")

        try:
            # Mantieni il motore in esecuzione
            while self.is_running:
                await asyncio.sleep(1)
                # Controlli periodici (es. drawdown)
                if await self.risk_manager.check_daily_drawdown():
                    logger.critical("Drawdown massimo raggiunto. Arresto del bot.")
                    self.is_running = False

        except asyncio.CancelledError:
            logger.info("Trading Engine fermato.")
        finally:
            # 3. Ferma lo stream e cancella gli ordini
            stream_task.cancel()
            await self.broker.disconnect_stream()
            await self.order_manager.cancel_all_open_orders()
            logger.info("Pulizia completata. Bot terminato.")

    async def on_bar(self, bar):
        """Callback per ogni nuova barra ricevuta dallo stream."""
        if not self.is_running:
            return

        try:
            # Aggiorna i dati storici con la nuova barra
            updated_symbol = await self.data_manager.on_bar_update(bar)
            
            # Aggiorna posizioni e ordini
            await self.position_manager.refresh_positions()
            await self.order_manager.refresh_open_orders()

            # Esegui la logica della strategia
            if updated_symbol:
                await self.strategy.on_bar(updated_symbol, self.data_manager.bars)

        except Exception as e:
            logger.error(f"Errore durante l'elaborazione della barra: {e}", exc_info=True)

async def start_bot():
    engine = TradingEngine()
    try:
        await engine.run()
    except KeyboardInterrupt:
        logger.info("Fermato manualmente dall'utente.")
    except Exception as e:
        logger.critical(f"Errore critico non gestito nel Trading Engine: {e}", exc_info=True)