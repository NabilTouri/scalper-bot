# bot_trading_project/trading/risk_manager.py

from typing import Optional
from scalper_bot.trading.connector import BrokerConnector
from trading.position_manager import PositionManager
from config.settings import (
    STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT, MAX_DAILY_DRAWDOWN_PERCENT,
    QUANTITY_PER_TRADE
)
from utils.logger import logger
from alpaca_trade_api.rest import Account, Position

class RiskManager:
    def __init__(self, connector: BrokerConnector, position_manager: PositionManager):
        self.connector = connector
        self.position_manager = position_manager
        self.account: Optional[Account] = None
        self.initial_equity: float = 0.0 # Equità all'inizio della giornata di trading
        logger.info("RiskManager inizializzato.")

    async def update_account_info(self):
        """Aggiorna le informazioni del conto e imposta l'equità iniziale."""
        self.account = await self.connector.get_account_info()
        if self.account:
            if self.initial_equity == 0.0: # Imposta solo all'inizio del bot o della giornata
                self.initial_equity = float(self.account.equity)
                logger.info(f"Equità iniziale impostata: ${self.initial_equity}")
        return self.account

    def calculate_position_size(self, current_price: float, risk_per_trade_percent: float = 0.01) -> int:
        """Calcola la dimensione della posizione basandosi sul rischio per trade e sul capitale."""
        if not self.account or self.initial_equity == 0:
            logger.warning("Account info non disponibile per calcolare la dimensione della posizione. Usando default.")
            return QUANTITY_PER_TRADE # Ritorna una quantità fissa se non ci sono dati account

        # Rischio per trade in valuta (es. 1% del capitale)
        risk_amount = float(self.account.equity) * risk_per_trade_percent

        # Calcola quante azioni si possono comprare con questo rischio
        # Se il tuo stop loss è del 1% del prezzo dell'azione, allora puoi rischiare 1% del capitale per comprare X azioni.
        # Questo è un calcolo semplificato. In pratica, bisognerebbe considerare lo stop loss in $ per azione.
        # Per ora, usiamo una quantità fissa definita in settings.py
        return QUANTITY_PER_TRADE
    
    async def apply_stop_loss_and_take_profit(self, position: Position, current_price: float):
        """Applica logica di stop loss e take profit a una posizione aperta."""
        entry_price = float(position.avg_entry_price)
        current_profit_loss_percent = (current_price - entry_price) / entry_price
        
        if position.side == 'short':
            current_profit_loss_percent *= -1 # Inverti per posizioni short

        # Check Stop Loss
        if current_profit_loss_percent < -STOP_LOSS_PERCENT:
            logger.warning(f"STOP LOSS per {position.symbol}! Prezzo attuale: {current_price}, Entry: {entry_price}, Perdita: {current_profit_loss_percent:.2%}")
            await self.position_manager.close_position(position.symbol)
            return True
        
        # Check Take Profit
        if current_profit_loss_percent > TAKE_PROFIT_PERCENT:
            logger.info(f"TAKE PROFIT per {position.symbol}! Prezzo attuale: {current_price}, Entry: {entry_price}, Guadagno: {current_profit_loss_percent:.2%}")
            await self.position_manager.close_position(position.symbol)
            return True
        
        return False

    async def check_daily_drawdown(self) -> bool:
        """Controlla se il drawdown giornaliero massimo è stato raggiunto."""
        if not self.account or self.initial_equity == 0.0:
            return False # Non possiamo controllare senza dati

        current_equity = float(self.account.equity)
        drawdown = (self.initial_equity - current_equity) / self.initial_equity
        
        if drawdown > MAX_DAILY_DRAWDOWN_PERCENT:
            logger.critical(f"DRAWDOWN MASSIMO GIORNALIERO RAGGIUNTO! Equity: ${current_equity}, Iniziale: ${self.initial_equity}, Drawdown: {drawdown:.2%}")
            return True # Indica che il bot dovrebbe fermarsi
        return False