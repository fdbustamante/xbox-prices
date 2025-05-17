"""
Script de punto de entrada para el scraping de precios de juegos de Xbox.
Este archivo simplemente importa y ejecuta la función principal del paquete scrap.
"""
from scrap.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
