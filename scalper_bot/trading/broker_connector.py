from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.common.exceptions import APIError
from ..config.settings import API_KEY_ID, API_SECRET_KEY
from ..utils.logger import logger
import pandas as pd

class BrokerConnector:
    def __init__(self, paper: bool = True):
        """
        Initializes the BrokerConnector.
        :param paper: If True, connects to the paper trading environment.
        """
        self.trading_client = TradingClient(API_KEY_ID, API_SECRET_KEY, paper=paper)
        self.data_stream = StockDataStream(API_KEY_ID, API_SECRET_KEY)
        self.historical_client = StockHistoricalDataClient(API_KEY_ID, API_SECRET_KEY)
        logger.info(f"BrokerConnector initialized for {'paper' if paper else 'live'} trading.")

    async def connect_stream(self, data_handler, symbols):
        """Connects to the real-time data stream for stocks."""
        logger.info(f"Subscribing to bars for symbols: {symbols}")
        self.data_stream.subscribe_bars(data_handler, *symbols)
        logger.info("Starting data stream...")
        try:
            await self.data_stream.run()
        except Exception as e:
            logger.error(f"Error in Alpaca data stream: {e}")
            await self.disconnect_stream()
            raise

    async def disconnect_stream(self):
        """Disconnects from the data stream."""
        if self.data_stream:
            logger.info("Disconnecting from data stream...")
            await self.data_stream.close()

    def get_account_info(self):
        """Retrieves account information."""
        try:
            account = self.trading_client.get_account()
            logger.info(f"Account Info: Status={account.status}, Equity=${account.equity}, Cash=${account.cash}")
            return account
        except APIError as e:
            logger.error(f"Error retrieving account info: {e}")
            return None

    def get_historical_bars(self, symbol: str, timeframe, start=None, end=None, limit=None) -> pd.DataFrame:
        """Retrieves historical bars."""
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit
        )
        try:
            bars = self.historical_client.get_stock_bars(request_params)
            return bars.df
        except APIError as e:
            logger.error(f"Error retrieving historical bars for {symbol}: {e}")
            return pd.DataFrame()

    def place_order(self, symbol: str, qty: float, side: OrderSide, order_type: OrderType = OrderType.MARKET, time_in_force: TimeInForce = TimeInForce.GTC, limit_price: float = None, stop_price: float = None, sl_price: float = None, tp_price: float = None):
        """Places an order."""
        try:
            order_data = None
            if order_type == OrderType.MARKET:
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force
                )
            elif order_type == OrderType.LIMIT:
                order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    time_in_force=time_in_force,
                    limit_price=limit_price
                )
            
            if not order_data:
                logger.error(f"Unsupported order type: {order_type}")
                return None

            # Add stop-loss and take-profit if specified
            if sl_price or tp_price:
                order_data.order_class = 'bracket'
                if sl_price:
                    order_data.stop_loss = StopLossRequest(stop_price=sl_price)
                if tp_price:
                    order_data.take_profit = TakeProfitRequest(limit_price=tp_price)

            order = self.trading_client.submit_order(order_data=order_data)
            logger.info(f"Order placed: {order.symbol} {order.side} {order.qty} {order.type}. ID: {order.id}")
            return order
        except APIError as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return None

    def cancel_order(self, order_id: str):
        """Cancels an order."""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order {order_id} cancelled.")
            return True
        except APIError as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_open_orders(self):
        """Retrieves all open orders."""
        try:
            orders = self.trading_client.get_orders(status='open')
            return orders
        except APIError as e:
            logger.error(f"Error retrieving open orders: {e}")
            return []

    def get_positions(self):
        """Retrieves all open positions."""
        try:
            positions = self.trading_client.get_all_positions()
            return positions
        except APIError as e:
            logger.error(f"Error retrieving positions: {e}")
            return []