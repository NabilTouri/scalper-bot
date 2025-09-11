from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.common.exceptions import APIError
from ..config.settings import API_KEY_ID, API_SECRET_KEY
from ..utils.logger import logger
import pandas as pd
import asyncio
from datetime import datetime, timedelta
import pytz


class BrokerConnector:
    def __init__(self, paper: bool = True):
        """
        Initializes the BrokerConnector.
        :param paper: If True, connects to the paper trading environment.
        """
        self.trading_client = TradingClient(API_KEY_ID, API_SECRET_KEY, paper=paper)
        self.data_stream = None
        self.historical_client = StockHistoricalDataClient(API_KEY_ID, API_SECRET_KEY)
        self.stream_task = None
        self.is_streaming = False
        self.simulation_task = None
        self.use_simulation = False
        logger.info(f"BrokerConnector initialized for {'paper' if paper else 'live'} trading.")

    def is_market_open(self):
        """Check if the market is currently open"""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False

    async def connect_stream(self, data_handler, symbols):
        """Connects to the real-time data stream for stocks."""
        logger.info(f"Subscribing to bars for symbols: {symbols}")

        # Check if market is open
        market_open = self.is_market_open()
        logger.info(f"Market is {'OPEN' if market_open else 'CLOSED'}")

        if not market_open:
            logger.warning("Market is closed. Starting simulation mode with historical data.")
            self.use_simulation = True
            await self._start_simulation_mode(data_handler, symbols)
            return

        try:
            # Try multiple feed options
            feeds_to_try = ['iex', 'sip']  # IEX is free, SIP requires subscription

            for feed in feeds_to_try:
                try:
                    logger.info(f"Trying to connect with {feed} feed...")
                    self.data_stream = StockDataStream(API_KEY_ID, API_SECRET_KEY, feed=feed)

                    # Test the connection by trying to subscribe
                    self.data_stream.subscribe_bars(data_handler, *symbols)
                    logger.info(f"Successfully subscribed to {feed} feed for: {symbols}")
                    break

                except Exception as e:
                    logger.warning(f"Failed to connect with {feed} feed: {e}")
                    self.data_stream = None
                    continue

            if self.data_stream is None:
                raise ValueError("Failed to create StockDataStream with any available feed")

            logger.info(f"Data stream object created: {type(self.data_stream)}")
            logger.info("Starting data stream...")
            self.is_streaming = True

            # Run the stream in a separate task
            self.stream_task = asyncio.create_task(self._run_stream())

            # Wait a bit for the stream to establish connection
            await asyncio.sleep(3)

            logger.info("Data stream started successfully")

        except Exception as e:
            logger.error(f"Error in Alpaca data stream setup: {e}")
            logger.info("Falling back to simulation mode...")
            self.use_simulation = True
            self.is_streaming = False
            await self._start_simulation_mode(data_handler, symbols)

    async def _start_simulation_mode(self, data_handler, symbols):
        """Start simulation mode using historical data"""
        logger.info("Starting simulation mode...")
        self.simulation_task = asyncio.create_task(self._simulate_live_data(data_handler, symbols))
        self.is_streaming = True

    async def _simulate_live_data(self, data_handler, symbols):
        """Simulate live data using latest available bars"""
        logger.info("Running data simulation...")

        while self.is_streaming:
            try:
                for symbol in symbols:
                    # Get the latest bar for each symbol
                    latest_bar_request = StockLatestBarRequest(symbol_or_symbols=[symbol])
                    latest_bars = self.historical_client.get_stock_latest_bar(latest_bar_request)

                    if symbol in latest_bars:
                        bar = latest_bars[symbol]

                        # Create a mock bar object that mimics the streaming bar
                        class MockBar:
                            def __init__(self, bar_data, symbol):
                                self.symbol = symbol
                                self.open = float(bar_data.open)
                                self.high = float(bar_data.high)
                                self.low = float(bar_data.low)
                                self.close = float(bar_data.close)
                                self.volume = int(bar_data.volume)
                                self.timestamp = bar_data.timestamp
                                self.vwap = getattr(bar_data, 'vwap', None)

                        mock_bar = MockBar(bar, symbol)
                        await data_handler(mock_bar)

                # Wait 30 seconds before next update (simulate bar frequency)
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error in simulation mode: {e}")
                await asyncio.sleep(5)

    async def _run_stream(self):
        """Internal method to run the data stream"""
        try:
            if self.data_stream is not None:
                logger.info("Attempting to start real-time data stream...")

                # Add timeout to prevent hanging
                try:
                    await asyncio.wait_for(self.data_stream.run(), timeout=10.0)
                except asyncio.TimeoutError:
                    logger.error("Data stream startup timed out")
                    raise

            else:
                logger.error("Data stream is None in _run_stream")
        except Exception as e:
            logger.error(f"Error in data stream execution: {e}")
            logger.info("Switching to simulation mode due to streaming error...")
            self.is_streaming = False
            # Don't raise the exception, let it fall back to simulation
            if not self.use_simulation:
                self.use_simulation = True
                # We can't easily restart here, so just log the issue

    async def disconnect_stream(self):
        """Disconnects from the data stream."""
        logger.info("Disconnecting from data stream...")

        self.is_streaming = False

        # Cancel the simulation task if running
        if self.simulation_task and not self.simulation_task.done():
            self.simulation_task.cancel()
            try:
                await self.simulation_task
            except asyncio.CancelledError:
                logger.info("Simulation task cancelled successfully")

        # Cancel the stream task if it exists
        if self.stream_task and not self.stream_task.done():
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                logger.info("Stream task cancelled successfully")

        # Close the data stream if it exists
        if self.data_stream is not None:
            try:
                await self.data_stream.close()
                logger.info("Data stream closed successfully")
            except Exception as e:
                logger.error(f"Error closing data stream: {e}")

        self.data_stream = None
        self.stream_task = None
        self.simulation_task = None
        self.use_simulation = False

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

    def place_order(self, symbol: str, qty: float, side: OrderSide, order_type: OrderType = OrderType.MARKET,
                    time_in_force: TimeInForce = TimeInForce.GTC, limit_price: float = None, stop_price: float = None,
                    sl_price: float = None, tp_price: float = None):
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