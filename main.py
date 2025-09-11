from scalper_bot.utils.logger import logger
from scalper_bot.engine import start_bot
import asyncio

async def main():
    await start_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Errore critico non gestito: {e}")