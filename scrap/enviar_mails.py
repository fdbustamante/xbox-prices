"""
Script para enviar notificaciones de juegos de Xbox a Telegram, leyendo desde el archivo JSON generado por el scraper.
"""
import sys
import asyncio
import os
import json
from scrap.config import OUTPUT_FILENAME, DEBUG, logger
from scrap.data_manager import (
    filtrar_juegos_por_precio, filtrar_juegos_nuevos,
    generar_mensaje_telegram, generar_mensaje_telegram_nuevos,
    filtrar_juegos_por_mayor_descuento
)
from scrap.telegram_client import enviar_mensaje_telegram

async def enviar_notificaciones_desde_json(json_path: str, fecha_actual: str = None) -> bool:
    with open(json_path, 'r', encoding='utf-8') as f:
        juegos = json.load(f)
    
    # Si el archivo es un dict con clave 'juegos', usar esa lista
    if isinstance(juegos, dict) and 'juegos' in juegos:
        juegos = juegos['juegos']

    # Filtrar juegos que bajaron de precio
    juegos_bajaron_precio = filtrar_juegos_por_precio(juegos, "decreased")
    # Filtrar juegos nuevos
    juegos_nuevos = filtrar_juegos_nuevos(juegos)

    notificacion_exitosa = True

    # Calcular descuentos si faltan
    for juego in juegos_bajaron_precio:
        if juego.get('precio_descuento_num') is None:
            precio_anterior = juego.get('precio_anterior_num')
            precio_actual = juego.get('precio_num')
            if precio_anterior and precio_actual and precio_anterior > 0:
                descuento = (1 - (precio_actual / precio_anterior)) * 100
                juego['precio_descuento_num'] = round(descuento, 1)
            else:
                juego['precio_descuento_num'] = None
    # Ordenar por mayor descuento
    juegos_bajaron_precio.sort(key=lambda j: j.get('precio_descuento_num') or 0, reverse=True)

    # Notificación general
    if juegos_bajaron_precio or DEBUG:
        try:
            mensaje = generar_mensaje_telegram(juegos_bajaron_precio, fecha_actual or "", DEBUG)
            logger.info("Enviando notificación de bajadas de precio a Telegram...")
            resultado = await enviar_mensaje_telegram(mensaje)
            if not resultado:
                notificacion_exitosa = False
        except Exception as e:
            logger.error(f"Error al enviar notificación de bajadas de precio: {e}")
            notificacion_exitosa = False
    # Notificación top descuentos
    try:
        from scrap.data_manager import generar_mensaje_telegram_top_descuentos
        # Usar la función utilitaria para obtener los juegos con mayor descuento
        juegos_con_descuento = filtrar_juegos_por_mayor_descuento(juegos)
        if juegos_con_descuento or DEBUG:
            mensaje = generar_mensaje_telegram_top_descuentos(juegos_con_descuento, fecha_actual or "", DEBUG)
            logger.info("Enviando notificación de top descuentos a Telegram...")
            resultado = await enviar_mensaje_telegram(mensaje)
            if not resultado:
                notificacion_exitosa = False
    except Exception as e:
        logger.error(f"Error al enviar notificación de top descuentos: {e}")
        notificacion_exitosa = False
    # Notificación juegos nuevos
    if juegos_nuevos or DEBUG:
        try:
            mensaje = generar_mensaje_telegram_nuevos(juegos_nuevos, fecha_actual or "", DEBUG)
            logger.info("Enviando notificación de juegos nuevos a Telegram...")
            resultado = await enviar_mensaje_telegram(mensaje)
            if not resultado:
                notificacion_exitosa = False
        except Exception as e:
            logger.error(f"Error al enviar notificación de juegos nuevos: {e}")
            notificacion_exitosa = False
    return notificacion_exitosa

if __name__ == "__main__":
    import datetime
    json_path = OUTPUT_FILENAME  # Usar siempre el archivo por defecto
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
    exit_code = asyncio.run(enviar_notificaciones_desde_json(json_path, fecha_actual))
    sys.exit(0 if exit_code else 1)
