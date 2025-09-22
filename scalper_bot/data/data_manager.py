import pandas as pd
from typing import Dict, List
from scalper_bot.trading.connector import BrokerConnector
from config.settings import SYMBOLS, TIMEFRAME
from utils.logger import logger

class DataManager:
    def __init__(self, connector: BrokerConnector):
        self.connector = connector
        self.bars: Dict[str, pd.DataFrame] = {symbol: pd.DataFrame() for symbol in SYMBOLS}
        logger.info("DataManager inizializzato.")

    async def initialize_historical_data(self, limit: int = 100):
        """Carica i dati storici iniziali per tutti i simboli."""
        logger.info(f"Caricamento {limit} candele storiche a {TIMEFRAME} per {SYMBOLS}...")
        for symbol in SYMBOLS:
            df = await self.connector.get_historical_bars(symbol, TIMEFRAME, limit=limit)
            if not df.empty:
                self.bars[symbol] = df
                logger.info(f"Caricate {len(df)} candele storiche per {symbol}.")
            else:
                logger.warning(f"Nessun dato storico trovato per {symbol}.")

    async def on_bar_update(self, bar_data):
        """Gestisce l'arrivo di una nuova barra in tempo reale dallo stream."""
        symbol = bar_data.symbol
        if symbol not in self.bars:
            self.bars[symbol] = pd.DataFrame() # Inizializza se è un nuovo simbolo

        # Converte la barra in un formato DataFrame row e la aggiunge
        new_row = pd.DataFrame([{
            'open': bar_data.open,
            'high': bar_data.high,
            'low': bar_data.data_low, # Usa data_low per compatibilità con l'API
            'close': bar_data.close,
            'volume': bar_data.volume,
            'trade_count': bar_data.trade_count,
            'vwap': bar_data.vwap
        }], index=[bar_data.timestamp.tz_convert('America/New_York')])
        
        # Aggiunge la nuova riga al DataFrame, assicurandosi che non ci siano duplicati sull'indice
        # Questo sovrascrive l'eventuale barra incompleta precedente o aggiunge la nuova
        self.bars[symbol] = pd.concat([self.bars[symbol], new_row[~new_row.index.isin(self.bars[symbol].index)]]).sort_index()

        # Rimuovi le barre più vecchie se il DataFrame diventa troppo grande (opzionale)
        max_bars_to_keep = 200 # Mantiene le ultime 200 barre
        if len(self.bars[symbol]) > max_bars_to_keep:
            self.bars[symbol] = self.bars[symbol].iloc[-max_bars_to_keep:]
            
        logger.debug(f"Nuova barra {symbol} {bar_data.timestamp}: {bar_data.close}")
        # Qui potresti notificare la strategia che ci sono nuovi dati
        return symbol # Restituisce il simbolo per poter notificare la strategia
    
    def get_latest_bars(self, symbol: str, num_bars: int = 100) -> pd.DataFrame:
        """Restituisce le ultime N barre per un simbolo."""
        if symbol in self.bars and not self.bars[symbol].empty:
            return self.bars[symbol].tail(num_bars)
        return pd.DataFrame()