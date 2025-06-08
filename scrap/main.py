"""
Módulo principal para ejecutar el scraping de precios de juegos de Xbox PC.
"""
import asyncio
import time
import sys
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from scrap.config import OUTPUT_FILENAME, logger
from scrap.data_manager import (
    cargar_datos_previos, guardar_datos, filtrar_juegos_por_precio, 
    filtrar_juegos_nuevos, generar_mensaje_telegram, generar_mensaje_telegram_nuevos
)
from scrap.scraper import scrape_xbox_games

async def ejecutar_scraping() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Ejecuta el proceso de scraping y retorna los resultados.
    Utiliza run_in_executor para ejecutar el scraping de forma asíncrona.
    
    Returns:
        Tupla con la lista de juegos encontrados y el diccionario de datos previos
    """
    logger.info("Cargando datos previos...")
    datos_previos = cargar_datos_previos(OUTPUT_FILENAME)
    
    logger.info("Iniciando el proceso de scraping de forma asíncrona...")
    # Ejecutar el proceso intensivo en un threadpool
    loop = asyncio.get_event_loop()
    juegos = await loop.run_in_executor(None, lambda: scrape_xbox_games(datos_previos))
    
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

if __name__ == "__main__":
    async def main_scraper():
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Iniciando scraper de Xbox PC Games...")
        try:
            juegos, _ = await ejecutar_scraping()
            if not juegos:
                logger.error("No se encontraron juegos o ocurrió un error durante el scraping.")
                sys.exit(1)
            logger.info(f"Se encontraron {len(juegos)} juegos.")
            fecha_actual = await guardar_resultados(juegos)
            if not fecha_actual:
                logger.error("No se pudieron guardar los resultados.")
                sys.exit(1)
            elapsed_time = time.time() - start_time
            logger.info(f"Scraping completado en {elapsed_time:.2f} segundos.")
            logger.info("=" * 60)
            sys.exit(0)
        except KeyboardInterrupt:
            logger.info("Proceso interrumpido por el usuario.")
            sys.exit(130)
        except Exception as e:
            logger.error(f"Error no controlado en el proceso: {e}", exc_info=True)
            sys.exit(1)
    asyncio.run(main_scraper())
