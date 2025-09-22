# bot_trading_project/trading/order_manager.py

from scalper_bot.trading.connector import BrokerConnector
from config.settings import TRADE_ENABLED
from utils.logger import logger

class OrderManager:
    def __init__(self, connector: BrokerConnector):
        self.connector = connector
        self.open_orders = {} # {order_id: order_object}
        logger.info("OrderManager inizializzato.")

    async def place_market_order(self, symbol: str, qty: int, side: str):
        """Piazza un ordine di mercato."""
        if not TRADE_ENABLED:
            logger.warning(f"Trading disabilitato. Ordine {side} {qty} {symbol} non piazzato (simulato).")
            return None
        
        logger.info(f"Piazzamento ordine di mercato: {side} {qty} {symbol}")
        order = await self.connector.place_order(symbol, qty, side, order_type='market')
        if order:
            self.open_orders[order.id] = order
        return order
    
    async def place_limit_order(self, symbol: str, qty: int, side: str, limit_price: float):
        """Piazza un ordine limite."""
        if not TRADE_ENABLED:
            logger.warning(f"Trading disabilitato. Ordine {side} {qty} {symbol} @ {limit_price} non piazzato (simulato).")
            return None

        logger.info(f"Piazzamento ordine limite: {side} {qty} {symbol} @ {limit_price}")
        order = await self.connector.place_order(symbol, qty, side, order_type='limit', limit_price=limit_price)
        if order:
            self.open_orders[order.id] = order
        return order
    
    async def cancel_all_open_orders(self):
        """Cancella tutti gli ordini aperti."""
        orders = await self.connector.get_open_orders()
        if orders:
            logger.info(f"Cancellazione di {len(orders)} ordini aperti...")
            for order in orders:
                await self.connector.cancel_order(order.id)
            self.open_orders.clear()
            logger.info("Tutti gli ordini aperti sono stati cancellati.")
        else:
            logger.info("Nessun ordine aperto da cancellare.")

    async def refresh_open_orders(self):
        """Aggiorna lo stato degli ordini aperti."""
        open_orders_list = await self.connector.get_open_orders()
        self.open_orders = {order.id: order for order in open_orders_list}
        logger.debug(f"Aggiornata lista ordini aperti: {len(self.open_orders)} ordini.")
        return self.open_orders