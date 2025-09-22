from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.live import CryptoDataStream
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, CryptoLatestBarRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.common.exceptions import APIError
from ..config.settings import ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY, SYMBOLS
from ..utils.logger import logger
import pandas as pd
import asyncio
from datetime import datetime, timedelta
import pytz


class Connector:
    def __init__(self, paper: bool = True):
        """
        Initializes the BrokerConnector.
        :param paper: If True, connects to the paper trading environment.
        """
        self.trading_client = TradingClient(ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY, paper=paper)
        self.crypto_stream = CryptoDataStream(ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY)
        self.stream_task = None
    
    def get_account_info(self):
        try:
            account = self.trading_client.get_account()
            return account
        except APIError as e:
            logger.error(f"API Error while fetching account info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching account info: {e}")
            return None

    async def _handler(self, data):
        logger.info(f"Received data: {data}")

    async def stream(self):
        self.crypto_stream.subscribe_bars(self._handler, *SYMBOLS)

        try:
            loop = asyncio.get_event_loop()
            self.stream_task = loop.run_in_executor(None, self.crypto_stream.run)

            await self.stream_task
        except Exception as e:
            logger.error(f"Error occurred while streaming: {e}")
            raise
        

    async def disconnect(self):
        try:
            await self.crypto_stream.close()
            logger.info("Crypto stream closed successfully.")
        except Exception as e:
            logger.error(f"Error closing crypto stream: {e}")

        if self.stream_task and not self.stream_task.done():
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                logger.info("Stream task cancelled successfully.")
            except Exception as e:
                logger.error(f"Error while cancelling stream task: {e}")
        