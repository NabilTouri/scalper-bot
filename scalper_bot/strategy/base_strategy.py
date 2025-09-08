# bot_trading_project/strategy/base_strategy.py

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = None # Verrà assegnato dal TradingEngine

    @abstractmethod
    async def on_bar(self, symbol: str, historical_bars: Dict[str, pd.DataFrame]):
        """
        Metodo chiamato quando arriva una nuova barra.
        Qui va implementata la logica della strategia per generare segnali di trading.
        """
        pass

    @abstractmethod
    async def initialize(self):
        """
        Metodo chiamato una volta all'avvio del bot per inizializzare la strategia.
        """
        pass