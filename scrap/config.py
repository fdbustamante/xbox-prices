"""
Configuración para el scraping de precios de juegos de Xbox.
Define constantes globales y configuraciones para la aplicación.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configuración de paths y archivos
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
OUTPUT_FILENAME = str(PUBLIC_DIR / "xbox_pc_games.json")
LOG_FILENAME = str(BASE_DIR / "xbox_prices_scraper.log")
HTML_DEBUG_DIR = BASE_DIR / "debug_html"

# Parámetros de configuración
MAX_JUEGOS = int(os.environ.get('MAX_JUEGOS', '4000'))
MAX_RETRY_ATTEMPTS = 3
REQUEST_TIMEOUT = 30  # segundos

# Configuración de Telegram (prioriza variables de entorno sobre configuración local)
BOT_TOKEN: Optional[str] = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID: Optional[str] = os.environ.get('TELEGRAM_CHAT_ID')
DEBUG: bool = os.environ.get('TELEGRAM_DEBUG', 'False').lower() in ('true', '1', 't', 'yes')

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
def setup_logging(level=logging.INFO):
    """
    Configura y devuelve un logger configurado con formato y handlers.
    
    Args:
        level: Nivel de logging (por defecto INFO)
        
    Returns:
        Logger configurado
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Crear logger
    logger_instance = logging.getLogger("xbox_scraper")
    logger_instance.setLevel(level)
    
    # Evitar duplicación de handlers
    if not logger_instance.handlers:
        # Handler para archivo
        file_handler = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger_instance.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger_instance.addHandler(console_handler)
    
    return logger_instance

# Crear instancia del logger
logger = setup_logging()

def get_formatted_datetime(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Devuelve la fecha y hora actual formateada.
    
    Args:
        format_str: Formato de fecha a utilizar
        
    Returns:
        String con la fecha formateada
    """
    from datetime import datetime
    return datetime.now().strftime(format_str)

def ensure_dirs_exist() -> None:
    """
    Asegura que todos los directorios necesarios existan.
    Crea los directorios si no existen.
    """
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# Crear directorios necesarios al importar el módulo
ensure_dirs_exist()