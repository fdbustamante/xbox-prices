"""
Script para enviar notificaciones de juegos de Xbox a Telegram, leyendo desde el archivo JSON generado por el scraper.
"""
import sys
import os
import json
import asyncio
import datetime
from typing import Optional

from scrap.config import OUTPUT_FILENAME, DEBUG, logger
from scrap.data_manager import (
    filtrar_juegos_por_precio, filtrar_juegos_nuevos,
    generar_mensaje_telegram, generar_mensaje_telegram_nuevos,
    filtrar_juegos_por_mayor_descuento, generar_mensaje_telegram_top_descuentos
)
from scrap.telegram_client import enviar_mensaje_telegram


def calcular_descuento(juego: dict) -> None:
    """Calcula y asigna el porcentaje de descuento a un juego si no está presente."""
    if juego.get('precio_descuento_num') is None:
        precio_anterior = juego.get('precio_anterior_num')
        precio_actual = juego.get('precio_num')
        if precio_anterior and precio_actual and precio_anterior > 0:
            descuento = (1 - (precio_actual / precio_anterior)) * 100
            juego['precio_descuento_num'] = round(descuento, 1)
        else:
            juego['precio_descuento_num'] = None


def ordenar_por_descuento(juegos: list) -> None:
    """Ordena la lista de juegos in-place por mayor descuento."""
    juegos.sort(key=lambda j: j.get('precio_descuento_num') or 0, reverse=True)


async def notificar_bajadas_precio(juegos: list, fecha_actual: str) -> bool:
    """Envía notificación de bajadas de precio a Telegram."""
    if not juegos and not DEBUG:
        return True
    try:
        mensaje = generar_mensaje_telegram(juegos, fecha_actual, DEBUG)
        logger.info("Enviando notificación de bajadas de precio a Telegram...")
        return await enviar_mensaje_telegram(mensaje)
    except Exception as e:
        logger.error(f"Error al enviar notificación de bajadas de precio: {e}")
        return False


async def notificar_top_descuentos(juegos: list, fecha_actual: str) -> bool:
    """Envía notificación de top descuentos a Telegram."""
    if not juegos and not DEBUG:
        return True
    try:
        mensaje = generar_mensaje_telegram_top_descuentos(juegos, fecha_actual, DEBUG)
        logger.info("Enviando notificación de top descuentos a Telegram...")
        return await enviar_mensaje_telegram(mensaje)
    except Exception as e:
        logger.error(f"Error al enviar notificación de top descuentos: {e}")
        return False


async def notificar_juegos_nuevos(juegos: list, fecha_actual: str) -> bool:
    """Envía notificación de juegos nuevos a Telegram."""
    if not juegos and not DEBUG:
        return True
    try:
        mensaje = generar_mensaje_telegram_nuevos(juegos, fecha_actual, DEBUG)
        logger.info("Enviando notificación de juegos nuevos a Telegram...")
        return await enviar_mensaje_telegram(mensaje)
    except Exception as e:
        logger.error(f"Error al enviar notificación de juegos nuevos: {e}")
        return False


async def enviar_notificaciones_desde_json(json_path: str, fecha_actual: Optional[str] = None) -> bool:
    """
    Lee el archivo JSON de juegos y envía notificaciones a Telegram:
    - Juegos que bajaron de precio
    - Top descuentos
    - Juegos nuevos
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        juegos = json.load(f)

    # Si el archivo es un dict con clave 'juegos', usar esa lista
    if isinstance(juegos, dict) and 'juegos' in juegos:
        juegos = juegos['juegos']

    # Filtrar juegos que bajaron de precio y calcular descuentos
    juegos_bajaron_precio = filtrar_juegos_por_precio(juegos, "decreased")
    for juego in juegos_bajaron_precio:
        calcular_descuento(juego)
    ordenar_por_descuento(juegos_bajaron_precio)

    # Filtrar juegos nuevos
    juegos_nuevos = filtrar_juegos_nuevos(juegos)

    # Top descuentos
    juegos_con_descuento = filtrar_juegos_por_mayor_descuento(juegos)

    notificacion_exitosa = True
    if not await notificar_bajadas_precio(juegos_bajaron_precio, fecha_actual or ""):
        notificacion_exitosa = False
    if not await notificar_top_descuentos(juegos_con_descuento, fecha_actual or ""):
        notificacion_exitosa = False
    if not await notificar_juegos_nuevos(juegos_nuevos, fecha_actual or ""):
        notificacion_exitosa = False
    return notificacion_exitosa


def main():
    """Punto de entrada para ejecutar el script desde la línea de comandos."""
    json_path = OUTPUT_FILENAME  # Usar siempre el archivo por defecto
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
    exit_code = asyncio.run(enviar_notificaciones_desde_json(json_path, fecha_actual))
    sys.exit(0 if exit_code else 1)


if __name__ == "__main__":
    main()
