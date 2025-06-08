"""
Cliente para enviar notificaciones por Telegram.
Proporciona funciones para enviar mensajes y verificar la configuración.
"""
import asyncio
from typing import Dict, Any, List
from telegram import Bot
from telegram.error import TelegramError, TimedOut, NetworkError
from telegram.constants import ParseMode

from scrap.config import BOT_TOKEN, CHAT_ID, logger, MAX_RETRY_ATTEMPTS

def _dividir_mensaje_largo(mensaje: str, limite: int = 4000) -> List[str]:
    """
    Divide un mensaje largo en fragmentos más pequeños para cumplir con las limitaciones de Telegram.
    
    Args:
        mensaje: El mensaje a dividir
        limite: Límite de caracteres por mensaje (4000 por defecto)
        
    Returns:
        Lista de fragmentos del mensaje
    """
    # Si el mensaje es lo suficientemente corto, devolverlo tal cual
    if len(mensaje) <= limite:
        return [mensaje]
    
    # Dividir el mensaje en fragmentos
    fragmentos = []
    lineas = mensaje.split('\n')
    fragmento_actual = ""
    
    for linea in lineas:
        # Si agregar esta línea excede el límite, comenzar un nuevo fragmento
        if len(fragmento_actual) + len(linea) + 1 > limite:
            if fragmento_actual:
                fragmentos.append(fragmento_actual)
            fragmento_actual = linea
        else:
            fragmento_actual = f"{fragmento_actual}\n{linea}" if fragmento_actual else linea
    
    # Agregar el último fragmento si existe
    if fragmento_actual:
        fragmentos.append(fragmento_actual)
    
    # Agregar numeración si hay múltiples fragmentos
    if len(fragmentos) > 1:
        for i in range(len(fragmentos)):
            fragmentos[i] = f"[Parte {i+1}/{len(fragmentos)}]\n\n" + fragmentos[i]
    
    return fragmentos

async def enviar_mensaje_telegram(
    mensaje: str,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
    retry_attempts: int = 2
) -> bool:
    """
    Envía un mensaje a través de Telegram usando el bot configurado.
    Si el mensaje excede el límite de caracteres, lo divide en varios mensajes.
    
    Args:
        mensaje: Contenido del mensaje a enviar
        parse_mode: Modo de formato del mensaje ("HTML", "MARKDOWN", "MARKDOWN_V2")
        disable_web_page_preview: Si debe deshabilitar la previsualización de enlaces
        retry_attempts: Número de reintentos en caso de error de red
        
    Returns:
        True si el mensaje se envió correctamente, False en caso contrario
    """
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("No se puede enviar mensaje a Telegram: token o chat_id no configurados")
        return False

    # Mapear el modo de formato a las constantes de telegram
    parse_mode_map = {
        "HTML": ParseMode.HTML,
        "MARKDOWN": ParseMode.MARKDOWN,
        "MARKDOWN_V2": ParseMode.MARKDOWN_V2,
        None: None
    }
    
    # Usar HTML como valor predeterminado si el modo no es válido
    telegram_parse_mode = parse_mode_map.get(parse_mode.upper() if parse_mode else None, ParseMode.HTML)
    
    # Dividir mensajes largos si es necesario
    fragmentos = _dividir_mensaje_largo(mensaje)
    bot = Bot(token=BOT_TOKEN)  # Crear el bot una sola vez

    # Enviar cada fragmento
    for i, fragmento in enumerate(fragmentos):
        for attempt in range(retry_attempts + 1):
            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=fragmento,
                    parse_mode=telegram_parse_mode,
                    disable_web_page_preview=disable_web_page_preview
                )
                logger.info(f"Mensaje {i+1}/{len(fragmentos)} enviado a Telegram correctamente")
                break  # Éxito, salir del bucle de reintento
            except (TimedOut, NetworkError) as e:
                wait_time = 2 ** (attempt + 1)
                if attempt < retry_attempts:
                    logger.warning(f"Error de red al enviar fragmento {i+1}. Reintento {attempt+1}/{retry_attempts} en {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Error de red persistente al enviar fragmento {i+1}: {e}")
                    return False
            except TelegramError as e:
                logger.error(f"Error de Telegram al enviar fragmento {i+1}: {e}")
                return False
            except Exception as e:
                logger.error(f"Error inesperado al enviar fragmento {i+1} a Telegram: {e}", exc_info=True)
                return False
    # Si llegamos aquí, todos los fragmentos se enviaron correctamente
    return True

async def verificar_configuracion_telegram() -> Dict[str, Any]:
    """
    Verifica si la configuración de Telegram es válida y devuelve información.
    
    Returns:
        Diccionario con el resultado de la verificación
    """
    if not BOT_TOKEN:
        return {"success": False, "error": "Token del bot no configurado"}
    
    if not CHAT_ID:
        return {"success": False, "error": "ID del chat no configurado"}
    
    try:
        bot = Bot(token=BOT_TOKEN)
        bot_info = await bot.get_me()
        
        try:
            # Intentar obtener información del chat
            chat = await bot.get_chat(CHAT_ID)
            chat_info = {
                "id": chat.id,
                "type": chat.type,
                "title": getattr(chat, "title", None) or getattr(chat, "username", "Desconocido")
            }
        except TelegramError as e:
            return {
                "success": False, 
                "bot": bot_info.username,
                "error": f"Bot válido, pero no puede acceder al chat: {e}"
            }
            
        return {
            "success": True,
            "bot": {
                "username": bot_info.username,
                "id": bot_info.id,
                "name": bot_info.first_name
            },
            "chat": chat_info
        }
    except TelegramError as e:
        return {"success": False, "error": f"Error de Telegram: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Error inesperado: {e}"}
