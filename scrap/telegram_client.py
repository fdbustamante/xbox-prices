"""
Cliente para enviar notificaciones por Telegram.
"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from scrap.config import BOT_TOKEN, CHAT_ID, logger

async def enviar_mensaje_telegram(mensaje):
    """Envía un mensaje a través de Telegram usando el bot configurado."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("No se puede enviar mensaje a Telegram: token o chat_id no configurados")
        return False
    
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=mensaje, parse_mode="HTML")
        logger.info(f"Mensaje enviado a Telegram correctamente")
        return True
    except TelegramError as e:
        logger.error(f"Error al enviar mensaje a Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al enviar mensaje a Telegram: {e}")
        return False
