#!/usr/bin/env python3
import sys
import json
import asyncio
import argparse
import os
from telegram import Bot
from telegram.error import TelegramError
import datetime

# Intenta importar la configuración de Telegram
try:
    from telegram_config import BOT_TOKEN, CHAT_ID, DEBUG
except ImportError:
    print("Error: No se encontró el archivo telegram_config.py")
    print("Por favor, crea este archivo con las siguientes variables:")
    print("BOT_TOKEN = 'tu_token_del_bot'")
    print("CHAT_ID = 'tu_chat_id'")
    print("DEBUG = False")
    sys.exit(1)

if not BOT_TOKEN or not CHAT_ID:
    print("Error: BOT_TOKEN o CHAT_ID no configurados correctamente en telegram_config.py")
    sys.exit(1)

async def test_telegram_notification():
    """Prueba el envío de notificaciones a Telegram."""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Mensaje de prueba
        mensaje = f"""<b>🎮 PRUEBA DE NOTIFICACIÓN XBOX PRICES</b>

<i>Fecha: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>

Este es un mensaje de prueba para verificar la configuración de Telegram.
Si estás viendo este mensaje, la configuración es correcta. 👍

<b>Pasos siguientes:</b>
1. Ejecuta el scraper: <code>python scrap.py</code>
2. Las notificaciones se enviarán cuando se detecten juegos con bajadas de precio.

🌐 <a href="https://fdbustamante.github.io/xbox-prices/">Ver todos los juegos</a>"""
        
        print("Enviando mensaje de prueba a Telegram...")
        await bot.send_message(
            chat_id=CHAT_ID, 
            text=mensaje,
            parse_mode="HTML"
        )
        print("¡Mensaje enviado con éxito! Verifica tu cuenta de Telegram.")
        return True
    except TelegramError as e:
        print(f"Error de Telegram al enviar el mensaje: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print(f"Probando notificación de Telegram con:")
    print(f"- BOT_TOKEN: {BOT_TOKEN[:4]}...{BOT_TOKEN[-4:]} (oculto por seguridad)")
    print(f"- CHAT_ID: {CHAT_ID}")
    
    asyncio.run(test_telegram_notification())
