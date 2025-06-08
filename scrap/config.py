"""
Configuración para el scraping de precios de juegos de Xbox.
Define constantes globales y configuraciones para la aplicación.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple

# --- Paths y archivos ---
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
OUTPUT_FILENAME = str(PUBLIC_DIR / "xbox_pc_games.json")
LOG_FILENAME = str(BASE_DIR / "xbox_prices_scraper.log")
HTML_DEBUG_DIR = BASE_DIR / "debug_html"

# --- Parámetros generales ---
MAX_JUEGOS = int(os.environ.get('MAX_JUEGOS', '4000'))
MAX_RETRY_ATTEMPTS = 3
REQUEST_TIMEOUT = 30  # segundos


def ensure_dirs_exist() -> None:
    """
    Asegura que los directorios necesarios existan.
    """
    for d in (PUBLIC_DIR, HTML_DEBUG_DIR):
        d.mkdir(parents=True, exist_ok=True)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configura y devuelve un logger con formato y handlers para archivo y consola.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    logger_instance = logging.getLogger("xbox_scraper")
    logger_instance.setLevel(level)
    if not logger_instance.handlers:
        file_handler = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger_instance.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger_instance.addHandler(console_handler)
    return logger_instance


def load_telegram_config() -> Tuple[Optional[str], Optional[str], bool]:
    """
    Carga la configuración de Telegram desde variables de entorno o archivo local.
    Prioriza variables de entorno. Si no existen, intenta importar de telegram_config.py.
    """
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    debug_env = os.environ.get('TELEGRAM_DEBUG')
    debug = debug_env.lower() in ('true', '1', 't', 'yes') if debug_env else False
    if not bot_token or not chat_id:
        try:
            from telegram_config import BOT_TOKEN as CONFIG_BOT_TOKEN
            from telegram_config import CHAT_ID as CONFIG_CHAT_ID
            from telegram_config import DEBUG as CONFIG_DEBUG
            if not bot_token:
                bot_token = CONFIG_BOT_TOKEN
            if not chat_id:
                chat_id = CONFIG_CHAT_ID
            if debug_env is None:
                debug = CONFIG_DEBUG
            logger.warning("Usando configuración de Telegram desde archivo local.")
        except ImportError:
            logger.warning("No se encontró archivo de configuración de Telegram ni variables de entorno. Las notificaciones estarán desactivadas.")
            bot_token, chat_id, debug = None, None, False
    return bot_token, chat_id, debug

# Inicialización de directorios y logger
ensure_dirs_exist()
logger = setup_logging()

# Configuración de Telegram
BOT_TOKEN, CHAT_ID, DEBUG = load_telegram_config()


def get_formatted_datetime(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Devuelve la fecha y hora actual formateada.
    """
    from datetime import datetime
    return datetime.now().strftime(format_str)