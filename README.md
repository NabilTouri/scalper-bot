# Bot di Day Trading Algoritmico

Questo è un framework per un bot di day trading algoritmico in Python, progettato per operare con Alpaca Markets.

## Struttura del Progetto
Il progetto è modulare, con componenti separati per la gestione dati, strategie, esecuzione ordini e gestione del rischio.

## Installazione

1.  **Clona il repository (se lo stai usando con Git):**
    ```bash
    git clone https://github.com/tuo-utente/bot_trading_project.git
    cd bot_trading_project
    ```
2.  **Crea e attiva l'ambiente virtuale:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```
    *Nota: L'installazione di `TA-Lib` può richiedere dipendenze C/C++. Se riscontri problemi, prova ad installare `pandas-ta` e sostituiscilo nel codice.*

4.  **Configura le API Keys:**
    Crea un file `.env` nella directory principale del progetto e aggiungi le tue API keys di Alpaca (paper trading):
    ```ini
    APCA_API_KEY_ID=LA_TUA_API_KEY_ID_DEMO
    APCA_API_SECRET_KEY=LA_TUA_SECRET_KEY_DEMO
    APCA_API_BASE_URL=https://paper-api.alpaca.markets
    TELEGRAM_BOT_TOKEN=IL_TUO_TOKEN_TELEGRAM
    TELEGRAM_CHAT_ID=IL_TUO_CHAT_ID
    ```
    **NON CONDIVIDERE MAI IL TUO FILE `.env`!**

## Esecuzione del Bot

Per avviare il bot in modalità paper trading:
```bash
python main.py