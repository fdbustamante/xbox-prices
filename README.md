# Xbox Prices Tracker

Un rastreador de precios para juegos de Xbox en PC, con actualizaciones automáticas cada 6 horas mediante scraping y despliegue continuo en GitHub Pages.

## 🎮 Descripción

Xbox Prices Tracker es una aplicación web que muestra y permite buscar los precios actuales de juegos disponibles en la tienda de Xbox para PC. Incluye información sobre descuentos, filtrado por diferentes criterios y actualización automática de datos.

### ✨ Características principales

- 🔍 Búsqueda y filtrado por título de juego
- 💰 Filtrado por rango de precios
- 🏷️ Filtrado por porcentaje mínimo de descuento
- 📊 Ordenación por precio (ascendente/descendente)
- 🔄 Actualización automática de datos cada 6 horas
- 📱 Diseño responsivo adaptado a diferentes dispositivos

## 🚀 Tecnologías utilizadas

- **Frontend**: React + Vite
- **Scraping**: Python con Selenium y BeautifulSoup
- **Automatización**: GitHub Actions
- **Despliegue**: GitHub Pages

## 💻 Desarrollo local

Para ejecutar este proyecto localmente:

```bash
# Clonar el repositorio
git clone https://github.com/fdbustamante/xbox-prices.git
cd xbox-prices

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

### Para ejecutar el scraper manualmente:

```bash
# Instalar dependencias de Python
pip install -r requirements.txt

# Ejecutar el scraper
python scrap.py
```

## 🤖 Automatización

El proyecto utiliza GitHub Actions para dos flujos de trabajo principales:

1. **Scraping programado**: Ejecuta el script de Python cada 6 horas para obtener datos actualizados de juegos, los guarda en un archivo JSON y despliega la aplicación si hay cambios.

2. **Despliegue continuo**: Al hacer push a la rama principal, automáticamente construye y despliega la aplicación en GitHub Pages.

## 📦 Estructura del proyecto

```
xbox-prices/
├── public/                  # Archivos públicos estáticos
│   └── xbox_pc_games.json   # Datos scrapeados de juegos
├── src/                     # Código fuente del frontend
│   ├── components/          # Componentes React
│   └── ...                  # Archivos principales y estilos
├── .github/workflows/       # Configuración de GitHub Actions
└── scrap.py                 # Script de scraping en Python
```

## 🔗 Enlaces útiles

- [Aplicación en vivo](https://fdbustamante.github.io/xbox-prices/)
- [Repositorio en GitHub](https://github.com/fdbustamante/xbox-prices)

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.
