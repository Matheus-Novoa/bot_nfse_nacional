import logging
from logging.handlers import RotatingFileHandler
import sys
from config import obter_dados_config
from telegram import Bot


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(filename)s %(lineno)d %(message)s"
LOG_FILE = "logs/bot_nfse.log"
dados_config = obter_dados_config()

TELEGREM_TOKEN = dados_config['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = dados_config['TELEGRAM_CHAT_ID']
bot = Bot(token=TELEGREM_TOKEN)


async def enviar_log_telegram(mensagem):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem)


def get_logger(name: str) -> logging.Logger:
    """
    Configura e retorna um logger com handlers para console e arquivo.

    Args:
        name (str): O nome do logger, geralmente __name__ do módulo que o utiliza.

    Returns:
        logging.Logger: Uma instância configurada do logger.
    """
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
