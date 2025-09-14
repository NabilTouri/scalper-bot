# bot_trading_project/trading/position_manager.py

from typing import Dict
from trading.broker_connector import BrokerConnector
from utils.logger import logger
from alpaca.rest import Position

class PositionManager:
    def __init__(self, connector: BrokerConnector):
        self.connector = connector
        self.positions: Dict[str, Position] = {} # {symbol: position_object}
        logger.info("PositionManager inizializzato.")

    async def refresh_positions(self):
        """Aggiorna la lista delle posizioni aperte."""
        live_positions = await self.connector.get_positions()
        self.positions = {p.symbol: p for p in live_positions}
        logger.debug(f"Aggiornate posizioni: {len(self.positions)} posizioni aperte.")
        return self.positions

    def get_position(self, symbol: str):
        """Restituisce la posizione per un simbolo specifico."""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Verifica se il bot ha una posizione aperta per un simbolo."""
        return symbol in self.positions
    
    def get_num_open_positions(self) -> int:
        """Restituisce il numero di posizioni aperte."""
        return len(self.positions)
    
    async def close_position(self, symbol: str):
        """Chiude una posizione aperta per un simbolo."""
        if not self.has_position(symbol):
            logger.warning(f"Nessuna posizione aperta per {symbol} da chiudere.")
            return False
        
        position = self.get_position(symbol)
        side = 'sell' if position.side == 'long' else 'buy'
        qty = abs(int(position.qty)) # Quantità da chiudere

        logger.info(f"Chiusura posizione per {symbol}: {side} {qty}")
        order = await self.connector.place_order(symbol, qty, side, order_type='market')
        if order:
            logger.info(f"Ordine di chiusura posizione {symbol} piazzato. ID: {order.id}")
            # La posizione verrà rimossa da self.positions con il prossimo refresh_positions
            return True
        return False