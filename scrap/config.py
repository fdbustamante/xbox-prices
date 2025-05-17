"""
Configuración para el scraping de precios de juegos de Xbox.
"""
import os
import logging

# Configuración de archivos
OUTPUT_FILENAME = "public/xbox_pc_games.json"

# Configuración de Telegram (prioriza variables de entorno por sobre configuración local)
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
DEBUG = os.environ.get('TELEGRAM_DEBUG', 'False').lower() == 'true'

# Si no hay variables de entorno, intenta importar del archivo de configuración local
if not BOT_TOKEN or not CHAT_ID:
    try:
        from telegram_config import BOT_TOKEN as CONFIG_BOT_TOKEN
        from telegram_config import CHAT_ID as CONFIG_CHAT_ID
        from telegram_config import DEBUG as CONFIG_DEBUG
        
        # Solo usa la configuración del archivo si no se establecieron variables de entorno
        if not BOT_TOKEN:
            BOT_TOKEN = CONFIG_BOT_TOKEN
        if not CHAT_ID:
            CHAT_ID = CONFIG_CHAT_ID
        if os.environ.get('TELEGRAM_DEBUG') is None:
            DEBUG = CONFIG_DEBUG
            
        print("Usando configuración de Telegram desde archivo local")
    except ImportError:
        print("ADVERTENCIA: No se encontró archivo de configuración de Telegram ni variables de entorno. Las notificaciones estarán desactivadas.")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("xbox_prices_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)