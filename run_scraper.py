"""
Script de punto de entrada para el scraping de precios de juegos de Xbox.
Este archivo simplemente importa y ejecuta la función principal del paquete scrap.
"""
import asyncio
import sys
from scrap.main import main

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)
