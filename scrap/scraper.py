"""
Módulo de scraping para extraer los precios de juegos de Xbox.
"""
import time
import re
from pathlib import Path
from dataclasses import dataclass, field
from functools import wraps, lru_cache
from contextlib import contextmanager
from typing import Dict, List, Optional, Union, Any, Callable, Iterator, TypeVar, cast
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementClickInterceptedException, StaleElementReferenceException
)
from bs4 import BeautifulSoup, Tag

from scrap.utils import clean_price_to_float, extract_discount_percentage, comparar_precio
from scrap.config import logger

# Constantes para configuración
URL_XBOX_TIENDA = "https://www.xbox.com/es-AR/games/all-games/pc?PlayWith=PC&xr=shellnav&orderby=Title+Asc"
SELECTOR_CARD_WRAPPER = "div.ProductCard-module__cardWrapper___6Ls86"
SELECTOR_TITULO = "span.ProductCard-module__title___nHGIp"
SELECTOR_ENLACE = "a.commonStyles-module__basicButton___go-bX"
SELECTOR_IMAGEN = "img.ProductCard-module__boxArt___-2vQY"
SELECTOR_PRECIO_CONTAINER = "div.ProductCard-module__priceGroup___bACzG"
SELECTOR_PRECIO_ORIGINAL = "span.Price-module__originalPrice___XNCxs"
SELECTOR_PRECIO_ACTUAL = r"span.ProductCard-module__price___cs1xr, span.Price-module__listedDiscountPrice___A-\+d5"
SELECTOR_DESCUENTO_TAG = "div.ProductCard-module__discountTag___OjGFy"
SELECTOR_GRID_CONTAINER = "ol.SearchProductGrid-module__container___jew-i"
XPATH_BOTON_CARGAR_MAS = "//button[.//div[contains(text(),'Cargar más')]]"
XPATH_BOTON_COOKIES = "//button[@id='onetrust-accept-btn-handler']"
MAX_JUEGOS_A_CARGAR = 100
MAX_FALLOS_CONSECUTIVOS = 3

# Tipo para funciones de retry
F = TypeVar('F', bound=Callable[..., Any])

@dataclass
class GameData:
    """Representación de un juego de Xbox con sus datos."""
    titulo: str = "Título no encontrado"
    link: str = "Enlace no encontrado"
    imagen_url: str = "Imagen no encontrada"
    precio_num: Optional[float] = None
    precio_old_num: Optional[float] = None
    precio_descuento_num: Optional[float] = None
    precio_texto: str = "Precio no disponible"
    precio_cambio: Optional[str] = None
    precio_anterior_num: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a un diccionario."""
        return {k: v for k, v in self.__dict__.items()}


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)) -> Callable[[F], F]:
    """
    Decorador para reintentar una función en caso de excepción.
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Tiempo de espera inicial entre intentos
        backoff: Factor multiplicativo para aumentar el tiempo de espera
        exceptions: Excepciones que activarán el reintento
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            current_delay = delay
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Función {func.__name__} falló después de {max_attempts} intentos: {e}")
                        raise
                    logger.warning(f"Intento {attempts} fallido en {func.__name__}: {e}. Reintentando en {current_delay:.2f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
        return cast(F, wrapper)
    return decorator


@contextmanager
def create_driver() -> Iterator[webdriver.Chrome]:
    """
    Administra la creación y cierre del driver de Selenium usando un contexto.
    
    Yields:
        Instancia del driver de Chrome configurado
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    logger.info("Iniciando el navegador...")
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        yield driver
    except Exception as e:
        logger.error(f"Error al iniciar ChromeDriver: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador cerrado correctamente.")


class XboxScraper:
    """Clase para manejar el scraping de juegos de Xbox."""
    
    def __init__(self, url: str = URL_XBOX_TIENDA, max_juegos: int = MAX_JUEGOS_A_CARGAR):
        """
        Inicializa el scraper de Xbox.
        
        Args:
            url: URL de la tienda de Xbox para hacer scraping
            max_juegos: Número máximo de juegos a cargar
        """
        self.url = url
        self.max_juegos = max_juegos
        
    @retry(max_attempts=2, delay=5.0)
    def cargar_pagina_inicial(self, driver: webdriver.Chrome) -> bool:
        """
        Carga la página inicial y configura la navegación.
        
        Args:
            driver: Instancia del driver de Chrome
            
        Returns:
            True si la página se carga correctamente, False en caso contrario
        """
        logger.info(f"Cargando página: {self.url}")
        driver.get(self.url)
        
        # Esperar a que la página cargue
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )

        # Aceptar cookies si aparece el banner
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_BOTON_COOKIES))
            ).click()
            logger.info("Banner de cookies aceptado.")
        except TimeoutException:
            logger.info("No se encontró el banner de cookies o ya fue aceptado.")
        except Exception as e:
            logger.warning(f"Error al aceptar cookies: {e}")

        # Esperar a que cargue la grilla de juegos
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTOR_GRID_CONTAINER))
            )
            
            # Esperar a que aparezca el primer juego
            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER))
            )
            logger.info("Grilla de juegos cargada correctamente.")
            return True
            
        except TimeoutException:
            logger.error("Timeout: Contenedor de grilla o primer item no encontrado.")
            Path("xbox_page_source_error_grid.html").write_text(
                driver.page_source, encoding="utf-8"
            )
            return False
            
    def scrape_xbox_games(self, datos_previos: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Realiza el scraping de los juegos de PC en la tienda de Xbox.
        
        Args:
            datos_previos: Diccionario con los datos previos para comparar precios
            
        Returns:
            Lista de diccionarios con la información de los juegos
        """
        try:
            with create_driver() as driver:
                if not self.cargar_pagina_inicial(driver):
                    logger.error("No se pudo cargar la página inicial.")
                    return []

                # Cargar más juegos haciendo click en "Cargar más"
                games_data = self._cargar_mas_juegos(driver)
                
                # Comparar con datos previos
                if datos_previos:
                    self._comparar_con_datos_previos_bulk(games_data, datos_previos)
                    
                return [game.to_dict() for game in games_data]
                
        except Exception as e:
            logger.error(f"Error durante el scraping: {e}", exc_info=True)
            return []
    
    def _cargar_mas_juegos(self, driver: webdriver.Chrome) -> List[GameData]:
        """
        Método para hacer clic en 'Cargar más' y obtener más juegos.
        
        Args:
            driver: Instancia de WebDriver de Selenium
            
        Returns:
            Lista de GameData con la información de los juegos
        """
        consecutive_failures = 0
        last_item_count = 0
        adaptive_wait_time = 1.5  # Tiempo de espera adaptativo
        
        while consecutive_failures < MAX_FALLOS_CONSECUTIVOS:
            try:
                current_items_count = len(driver.find_elements(By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER))
                logger.info(f"Items actualmente cargados: {current_items_count}")
            except StaleElementReferenceException:
                # Si los elementos están siendo actualizados, esperar y reintentar
                time.sleep(adaptive_wait_time)
                continue

            if current_items_count >= self.max_juegos:
                logger.info(f"Límite de {self.max_juegos} juegos alcanzado. Deteniendo carga.")
                break

            if current_items_count > 0 and current_items_count == last_item_count:
                consecutive_failures += 1
                adaptive_wait_time *= 1.5  # Aumentar tiempo de espera
            else:
                consecutive_failures = 0
                adaptive_wait_time = max(1.5, adaptive_wait_time * 0.8)  # Reducir tiempo de espera

            last_item_count = current_items_count

            try:
                # Localizar y hacer clic en el botón "Cargar más"
                load_more_button = self._encontrar_boton_cargar_mas(driver)
                if load_more_button:
                    self._hacer_click_seguro(driver, load_more_button)
                    logger.info("Botón 'Cargar más' presionado.")
                    
                    # Esperar a que se carguen nuevos elementos (espera dinámica)
                    self._esperar_nuevos_elementos(driver, last_item_count)
                else:
                    logger.info("Botón 'Cargar más' no encontrado. Posiblemente se cargaron todos los juegos.")
                    consecutive_failures += 1
            except TimeoutException:
                logger.info("Timeout al buscar/presionar 'Cargar más'.")
                consecutive_failures += 1
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(adaptive_wait_time)
            except Exception as e:
                logger.error(f"Error en bucle 'Cargar más': {e}")
                consecutive_failures += 1
                time.sleep(adaptive_wait_time)
                
            # Si tenemos suficientes fallos, asumimos que no hay más juegos
            if consecutive_failures >= MAX_FALLOS_CONSECUTIVOS:
                break
        
        # Guardar el HTML para procesarlo
        page_source = driver.page_source
        Path("xbox_page_source.html").write_text(page_source if page_source else "", encoding="utf-8")
        
        # Procesar los datos obtenidos
        return self._procesar_datos_juegos(page_source)
    
    def _encontrar_boton_cargar_mas(self, driver: webdriver.Chrome) -> Optional[webdriver.remote.webelement.WebElement]:
        """Encuentra el botón 'Cargar más' y hace scroll hacia él."""
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATH_BOTON_CARGAR_MAS))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'nearest'});", 
                load_more_button
            )
            return WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_BOTON_CARGAR_MAS))
            )
        except (TimeoutException, NoSuchElementException):
            return None
            
    def _hacer_click_seguro(self, driver: webdriver.Chrome, elemento: webdriver.remote.webelement.WebElement) -> None:
        """Intenta hacer click en un elemento de forma segura."""
        try:
            elemento.click()
        except ElementClickInterceptedException:
            # Si está interceptado, usar JavaScript
            driver.execute_script("arguments[0].click();", elemento)
    
    def _esperar_nuevos_elementos(self, driver: webdriver.Chrome, ultimo_conteo: int) -> None:
        """Espera a que se carguen nuevos elementos."""
        try:
            WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER)) > ultimo_conteo
            )
            logger.info(f"Nuevos items cargados. Total ahora: {len(driver.find_elements(By.CSS_SELECTOR, SELECTOR_CARD_WRAPPER))}")
            # Breve pausa para permitir renderizado completo
            time.sleep(1)
        except TimeoutException:
            logger.warning("No se detectaron nuevos elementos después de hacer clic en 'Cargar más'")

    def _procesar_datos_juegos(self, page_source: str) -> List[GameData]:
        """
        Procesa el HTML de la página para extraer información de los juegos.
        
        Args:
            page_source: Código HTML de la página
            
        Returns:
            Lista de objetos GameData con los datos de los juegos procesados
        """
        soup = BeautifulSoup(page_source, 'html.parser')
        juegos_procesados = []
        juegos_omitidos = 0
        game_items = soup.select(SELECTOR_CARD_WRAPPER)
        logger.info(f"Procesando {len(game_items)} items de juego con BeautifulSoup.")

        # Usar comprensión de lista con filtrado
        juegos_validos = []
        for item in game_items:
            game_data = self._extraer_datos_juego(item)
            
            # Omitir juegos sin información suficiente
            if game_data.titulo == "Título no encontrado" and game_data.precio_texto == "Precio no disponible":
                juegos_omitidos += 1
                continue
                
            juegos_validos.append(game_data)
        
        # Mostrar estadísticas finales
        logger.info(f"\n--- Estadísticas finales de scraping ---")
        logger.info(f"Juegos encontrados y procesados correctamente: {len(juegos_validos)}")
        logger.info(f"Juegos omitidos por falta de información: {juegos_omitidos}")
        logger.info(f"Total de elementos analizados: {len(game_items)}")
        
        return juegos_validos

    def _extraer_datos_juego(self, item: Tag) -> GameData:
        """
        Extrae los datos de un elemento de juego individual.
        
        Args:
            item: Elemento BeautifulSoup que representa un juego
            
        Returns:
            Objeto GameData con los datos del juego
        """
        game = GameData()
        
        # Extraer datos básicos
        # Título
        title_tag = item.select_one(SELECTOR_TITULO)
        if title_tag:
            game.titulo = title_tag.text.strip()

        # Enlace
        link_tag = item.select_one(SELECTOR_ENLACE)
        if link_tag and link_tag.get('href'):
            game.link = link_tag.get('href')

        # URL de la Imagen
        img_tag = item.select_one(SELECTOR_IMAGEN)
        if img_tag and img_tag.get('src'):
            game.imagen_url = img_tag.get('src')

        # Extraer información de precios
        self._extraer_info_precios(item, game, link_tag)
        
        return game
        
    def _extraer_info_precios(self, item: Tag, game: GameData, link_tag: Optional[Tag] = None) -> None:
        """
        Extrae la información de precios de un item de juego.
        
        Args:
            item: Elemento BeautifulSoup
            game: Objeto GameData para almacenar los datos
            link_tag: Etiqueta de enlace para obtener atributos adicionales
        """
        price_container = item.select_one(SELECTOR_PRECIO_CONTAINER)
        if not price_container:
            return
            
        original_price_span = price_container.select_one(SELECTOR_PRECIO_ORIGINAL)
        current_price_span = price_container.select_one(SELECTOR_PRECIO_ACTUAL)
        discount_tag_span = price_container.select_one(SELECTOR_DESCUENTO_TAG)

        if original_price_span and current_price_span:  # Hay descuento
            self._procesar_precio_con_descuento(
                game, original_price_span, current_price_span, discount_tag_span, link_tag
            )
        elif current_price_span:  # Solo precio normal
            current_price_text = current_price_span.text.strip()
            game.precio_num = clean_price_to_float(current_price_text)
            game.precio_texto = current_price_text
        
        # Manejar casos especiales (Gratis, Game Pass)
        self._detectar_precios_especiales(game, price_container)
        
        # Fallback para casos donde no se detectó precio en el contenedor principal
        if (game.precio_texto == "Precio no disponible" or 
            (game.precio_num is None and "ARS$" not in game.precio_texto and 
             game.precio_texto != "Incluido con Game Pass")):
            
            self._detectar_precios_en_texto_completo(game, item)
                
    def _procesar_precio_con_descuento(self, 
                                      game: GameData, 
                                      original_price_span: Tag, 
                                      current_price_span: Tag, 
                                      discount_tag_span: Optional[Tag], 
                                      link_tag: Optional[Tag]) -> None:
        """Procesa los precios cuando hay un descuento aplicado."""
        original_price_text = original_price_span.text.strip()
        current_price_text = current_price_span.text.strip()
        
        game.precio_old_num = clean_price_to_float(original_price_text)
        game.precio_num = clean_price_to_float(current_price_text)
        
        if discount_tag_span:
            game.precio_descuento_num = extract_discount_percentage(discount_tag_span.text.strip())

        # Formatear texto de display usando expresiones regulares para extraer info del aria-label
        if link_tag and link_tag.get('aria-label'):
            aria_label = link_tag.get('aria-label')
            precio_pattern = re.compile(r"Precio original:\s*(ARS\$\s*[\d\.,]+);\s*en oferta por\s*(ARS\$\s*[\d\.,]+)", re.IGNORECASE)
            match_aria = precio_pattern.search(aria_label)
            
            if match_aria:
                game.precio_texto = f"Antes: {match_aria.group(1).strip()}, Ahora: {match_aria.group(2).strip()}"
                if game.precio_descuento_num:
                    game.precio_texto += f" (-{game.precio_descuento_num}%)"
            elif "ARS$" in aria_label:
                game.precio_texto = aria_label.split(',', 1)[-1].strip()
            else:
                game.precio_texto = f"Antes: {original_price_text}, Ahora: {current_price_text}"
        else:
            game.precio_texto = f"Antes: {original_price_text}, Ahora: {current_price_text}"
        
    def _detectar_precios_especiales(self, game: GameData, price_container: Tag) -> None:
        """Detecta precios especiales como 'Gratis' o 'Game Pass'."""
        if game.precio_num is None and (game.precio_texto == "Precio no disponible" or "ARS$" not in game.precio_texto):
            container_text_lower = price_container.text.lower()
            if "gratis" in container_text_lower:
                game.precio_texto = "Gratis"
                game.precio_num = 0.0
            elif "incluido con" in container_text_lower or "game pass" in container_text_lower:
                game.precio_texto = "Incluido con Game Pass"
                
    def _detectar_precios_en_texto_completo(self, game: GameData, item: Tag) -> None:
        """Busca precios en todo el texto del elemento cuando no se detectó en el contenedor principal."""
        item_text_lower = item.text.lower()
        if "gratis" in item_text_lower:
            game.precio_texto = "Gratis"
            game.precio_num = 0.0
        elif "incluido con game pass" in item_text_lower or "game pass" in item_text_lower:
            game.precio_texto = "Incluido con Game Pass"
    
    def _comparar_con_datos_previos_bulk(self, 
                                        juegos_actuales: List[GameData], 
                                        datos_previos: Dict[str, Dict[str, Any]]) -> None:
        """Compara en bloque todos los juegos con los datos previos."""
        for game in juegos_actuales:
            if game.titulo in datos_previos:
                juego_previo = datos_previos[game.titulo]
                self._comparar_con_datos_previos(game, juego_previo)
            
    def _comparar_con_datos_previos(self, game: GameData, juego_previo: Dict[str, Any]) -> None:
        """Compara el precio actual con los datos previos."""
        if 'precio_num' in juego_previo and juego_previo['precio_num'] is not None:
            precio_prev = juego_previo['precio_num']
            game.precio_cambio = comparar_precio(game.precio_num, precio_prev)
            
            # Guardar precio anterior si hubo cambio
            if game.precio_cambio in ["increased", "decreased"]:
                game.precio_anterior_num = precio_prev


@lru_cache(maxsize=1)
def get_scraper(url: str = URL_XBOX_TIENDA, max_juegos: int = MAX_JUEGOS_A_CARGAR) -> XboxScraper:
    """
    Obtiene una instancia única del scraper (patrón Singleton con cache).
    
    Args:
        url: URL de la tienda
        max_juegos: Número máximo de juegos a cargar
        
    Returns:
        Instancia de XboxScraper
    """
    return XboxScraper(url, max_juegos)


def scrape_xbox_games(datos_previos: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Función principal de scraping para mantener compatibilidad con código existente.
    
    Args:
        datos_previos: Diccionario con datos previos para comparar precios
        
    Returns:
        Lista de juegos con su información
    """
    scraper = get_scraper()
    return scraper.scrape_xbox_games(datos_previos)
