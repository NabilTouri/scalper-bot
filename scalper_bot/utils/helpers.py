import pandas as pd

def calculate_sma(series: pd.Series, length: int) -> pd.Series:
    """
    Calcola la Media Mobile Semplice (SMA).
    :param series: Serie di pandas (es. prezzi di chiusura).
    :param length: Periodo della media mobile.
    :return: Serie di pandas con i valori della SMA.
    """
    return series.rolling(window=length).mean()

def calculate_rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """
    Calcola il Relative Strength Index (RSI).
    :param series: Serie di pandas (es. prezzi di chiusura).
    :param length: Periodo dell'RSI.
    :return: Serie di pandas con i valori dell'RSI.
    """
    delta = series.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi