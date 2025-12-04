import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(filename)s %(lineno)d %(message)s"

LOG_FILE = "logs/bot_nfse.json"

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

    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setLevel(logging.INFO)
    # console_formatter = logging.Formatter(LOG_FORMAT)
    # console_handler.setFormatter(console_formatter)
    # logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = jsonlogger.JsonFormatter(LOG_FORMAT, json_ensure_ascii=False)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
