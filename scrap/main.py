"""
Módulo principal para ejecutar el scraping de precios de juegos de Xbox PC.
"""
import asyncio
from scrap.config import OUTPUT_FILENAME, DEBUG, logger
from scrap.data_manager import cargar_datos_previos, guardar_datos, filtrar_juegos_por_precio, generar_mensaje_telegram
from scrap.scraper import scrape_xbox_games
from scrap.telegram_client import enviar_mensaje_telegram

async def main():
    """Función principal del programa."""
    print("Iniciando scraper de Xbox PC Games...")
    
    # Cargar datos previos si existen
    datos_previos = cargar_datos_previos(OUTPUT_FILENAME)
    
    # Ejecutar scraping con datos previos
    juegos = scrape_xbox_games(datos_previos)

    if juegos:
        print(f"\n--- {len(juegos)} Juegos Encontrados ---")

        try:
            # Guardar los datos
            fecha_actual = guardar_datos(juegos, OUTPUT_FILENAME)
            if not fecha_actual:
                return
            
            # Preparar y enviar notificación de Telegram para juegos que bajaron de precio
            juegos_bajaron_precio = filtrar_juegos_por_precio(juegos, "decreased")
            
            if juegos_bajaron_precio or DEBUG:
                # Construir el mensaje para Telegram
                mensaje = generar_mensaje_telegram(juegos_bajaron_precio, fecha_actual, DEBUG)
                
                # Enviar el mensaje a través de Telegram
                print("\nEnviando notificación a Telegram...")
                await enviar_mensaje_telegram(mensaje)
            else:
                print("\nNo se encontraron juegos que hayan bajado de precio. No se envía notificación.")
                
        except Exception as e:
            logger.error(f"Error al guardar los datos en JSON o al enviar notificación: {e}")
    else:
        logger.warning("No se pudieron obtener datos de los juegos o la lista está vacía.")

if __name__ == "__main__":
    asyncio.run(main())
