"""
Módulo principal para ejecutar el scraping de precios de juegos de Xbox PC.
"""
import asyncio
import time
import sys
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from scrap.config import OUTPUT_FILENAME, DEBUG, logger
from scrap.data_manager import cargar_datos_previos, guardar_datos, filtrar_juegos_por_precio, generar_mensaje_telegram
from scrap.scraper import scrape_xbox_games
from scrap.telegram_client import enviar_mensaje_telegram

async def ejecutar_scraping() -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Ejecuta el proceso de scraping y retorna los resultados.
    
    Returns:
        Tupla con la lista de juegos encontrados y el diccionario de datos previos
    """
    logger.info("Cargando datos previos...")
    datos_previos = cargar_datos_previos(OUTPUT_FILENAME)
    
    logger.info("Iniciando el proceso de scraping...")
    juegos = scrape_xbox_games(datos_previos)
    
    return juegos, datos_previos

async def guardar_resultados(juegos: List[Dict[str, Any]]) -> Optional[str]:
    """
    Guarda los resultados del scraping en un archivo JSON.
    
    Args:
        juegos: Lista de diccionarios con los datos de los juegos
        
    Returns:
        String con la fecha actual o None si ocurre un error
    """
    try:
        return guardar_datos(juegos, OUTPUT_FILENAME)
    except Exception as e:
        logger.error(f"Error al guardar los resultados: {e}")
        return None

async def enviar_notificaciones(juegos: List[Dict[str, Any]], fecha_actual: str) -> bool:
    """
    Filtra los juegos que bajaron de precio y envía la notificación.
    
    Args:
        juegos: Lista de juegos encontrados
        fecha_actual: Fecha actual formateada
        
    Returns:
        True si se envió la notificación correctamente, False en caso contrario
    """
    # Filtrar juegos que bajaron de precio
    juegos_bajaron_precio = filtrar_juegos_por_precio(juegos, "decreased")
    
    if juegos_bajaron_precio or DEBUG:
        try:
            # Construir el mensaje
            mensaje = generar_mensaje_telegram(juegos_bajaron_precio, fecha_actual, DEBUG)
            
            # Enviar notificación
            logger.info("Enviando notificación a Telegram...")
            await enviar_mensaje_telegram(mensaje)
            return True
        except Exception as e:
            logger.error(f"Error al enviar notificación: {e}")
            return False
    else:
        logger.info("No se encontraron juegos con bajada de precio. No se envía notificación.")
        return True

async def main() -> int:
    """
    Función principal del programa.
    
    Returns:
        Código de salida (0 para éxito, otro valor para error)
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Iniciando scraper de Xbox PC Games...")
    
    try:
        # Ejecutar el scraping
        juegos, _ = await ejecutar_scraping()
        
        if not juegos:
            logger.error("No se encontraron juegos o ocurrió un error durante el scraping.")
            return 1
            
        logger.info(f"Se encontraron {len(juegos)} juegos.")
        
        # Guardar los resultados
        fecha_actual = await guardar_resultados(juegos)
        if not fecha_actual:
            logger.error("No se pudieron guardar los resultados.")
            return 1
            
        # Enviar notificaciones
        envio_exitoso = await enviar_notificaciones(juegos, fecha_actual)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Proceso completado en {elapsed_time:.2f} segundos.")
        logger.info("=" * 60)
        
        return 0 if envio_exitoso else 1
        
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario.")
        return 130
    except Exception as e:
        logger.error(f"Error no controlado en el proceso: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
