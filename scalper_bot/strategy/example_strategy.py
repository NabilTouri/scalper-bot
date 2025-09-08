# bot_trading_project/strategy/example_strategy.py

import pandas as pd
from typing import Dict
from strategy.base_strategy import BaseStrategy
from trading.broker_connector import BrokerConnector
from trading.order_manager import OrderManager
from trading.position_manager import PositionManager
from trading.risk_manager import RiskManager
from utils.helpers import calculate_rsi, calculate_sma # Per indicatori tecnici
from config.settings import SYMBOLS, QUANTITY_PER_TRADE, MAX_POSITIONS

class ExampleStrategy(BaseStrategy):
    def __init__(self, connector: BrokerConnector, order_manager: OrderManager, 
                 position_manager: PositionManager, risk_manager: RiskManager):
        super().__init__("ExampleStrategy")
        self.connector = connector
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.logger = None # Assegnato dal TradingEngine
        self.sma_length = 20
        self.rsi_length = 14
        self.trade_signals = {s: None for s in SYMBOLS} # {symbol: 'buy'/'sell'/None}

    async def initialize(self):
        self.logger.info(f"{self.name} inizializzata.")
        # Esegui qui qualsiasi setup iniziale necessario per la strategia.

    async def on_bar(self, symbol: str, historical_bars: Dict[str, pd.DataFrame]):
        """
        Logica della strategia:
        - Calcola indicatori tecnici sulla base delle barre storiche.
        - Genera segnali di acquisto/vendita.
        - Interagisce con OrderManager e PositionManager per eseguire trade.
        """
        
        df = historical_bars.get(symbol)
        if df.empty or len(df) < max(self.sma_length, self.rsi_length):
            self.logger.debug(f"Dati insufficienti per {symbol} per {self.name}. Saltando...")
            return

        # 1. Calcola gli indicatori tecnici
        df['SMA'] = calculate_sma(df, self.sma_length)
        df['RSI'] = calculate_rsi(df, self.rsi_length)

        # Assicurati che gli indicatori siano calcolati per tutte le barre
        if df['SMA'].isnull().all() or df['RSI'].isnull().all():
            self.logger.debug(f"Indicatori non calcolati correttamente per {symbol}.")
            return

        # 2. Ottieni i valori più recenti
        last_close = df['close'].iloc[-1]
        last_sma = df['SMA'].iloc[-1]
        last_rsi = df['RSI'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        prev_sma = df['SMA'].iloc[-2]

        self.logger.debug(f"[{symbol}] Close: {last_close:.2f}, SMA: {last_sma:.2f}, RSI: {last_rsi:.2f}")

        # 3. Genera segnali di trading (Esempio: incrocio SMA + filtro RSI)
        signal = None
        if prev_close < prev_sma and last_close > last_sma: # Incrocio SMA bullish
            if last_rsi < 70: # Evita ipercomprato
                signal = 'buy'