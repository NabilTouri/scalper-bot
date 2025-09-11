import os
from dotenv import load_dotenv
from alpaca.data import TimeFrame

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Credenziali API Alpaca
API_KEY_ID = os.getenv("APCA_API_KEY_ID")
API_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

# Impostazioni di trading
SYMBOLS = ["SPY", "QQQ"]  # Esempio di simboli da tradare
TIMEFRAME = TimeFrame.Minute  # Esempio di timeframe
TRADE_ENABLED = True # Abilita/Disabilita il trading reale

# Impostazioni di Rischio
MAX_POSITIONS = 2  # Numero massimo di posizioni aperte contemporaneamente
QUANTITY_PER_TRADE = 10  # Quantità fissa di azioni per trade (semplificato)
STOP_LOSS_PERCENT = 0.01  # 1% di stop loss
TAKE_PROFIT_PERCENT = 0.02 # 2% di take profit
MAX_DAILY_DRAWDOWN_PERCENT = 0.05 # 5% di drawdown massimo giornaliero

# Impostazioni Telegram (opzionale)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
