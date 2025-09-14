import logging
import sys

# Configurazione base del logger
logger = logging.getLogger("scalper_bot")
logger.setLevel(logging.INFO)

# Formattatore per i log con dettagli di origine file e linea
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d')

# Handler per scrivere i log sulla console
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# (Opzionale) Handler per scrivere i log su un file
file_handler = logging.FileHandler("bot.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
