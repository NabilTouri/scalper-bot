# bot_trading_project/utils/helpers.py

import pandas as pd
import pandas_ta as ta # Usiamo pandas_ta per semplicità di installazione

# Esempio: Calcola RSI
def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return ta.rsi(df['close'], length=length)

# Esempio: Calcola Moving Average
def calculate_sma(df: pd.DataFrame, length: int = 20) -> pd.Series:
    return ta.sma(df['close'], length=length)

# Aggiungi altre funzioni di utilità o indicatori tecnici qui