import React, { useState, useEffect, useCallback } from 'react';
import GameList from './components/GameList';
import './style.css';

function App() {
    const [allGames, setAllGames] = useState([]);
    const [displayedGames, setDisplayedGames] = useState([]);
    
    // Estados de Filtro Existentes
    const [sortType, setSortType] = useState('default');
    const [filterMinPrice, setFilterMinPrice] = useState('');
    const [filterMaxPrice, setFilterMaxPrice] = useState('');
    const [hideNoPrice, setHideNoPrice] = useState(false); // Nuevo estado para ocultar juegos sin precio

    // Nuevos Estados de Filtro
    const [filterDiscountPercent, setFilterDiscountPercent] = useState('0'); // String para el input range, se parseará a número
    const [filterTitle, setFilterTitle] = useState('');

    // Estado para el botón Volver Arriba
    const [showBackToTop, setShowBackToTop] = useState(false);
    
    // Estado para la fecha de actualización
    const [fechaActualizacion, setFechaActualizacion] = useState(null);

    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        setIsLoading(true);
        setError(null);
        const jsonUrl = `${import.meta.env.BASE_URL}xbox_pc_games.json`;

        fetch(jsonUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error al cargar el archivo JSON: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Verificar la estructura de los datos (compatibilidad con nuevos y viejos formatos)
                const juegosData = data.juegos ? data.juegos : data;
                const fechaCreacion = data.fecha_creacion || null;
                
                if (fechaCreacion) {
                    console.log(`Datos actualizados el: ${fechaCreacion}`);
                    setFechaActualizacion(fechaCreacion);
                }
                
                const gamesWithId = juegosData.map((game, index) => ({
                    ...game,
                    id: game.link || `game-${index}`
                }));
                setAllGames(gamesWithId);
                setIsLoading(false);
            })
            .catch(err => {
                console.error("Error fetching game data:", err);
                setError(err.message);
                setIsLoading(false);
            });
    }, []);

    const applyFiltersAndSort = useCallback(() => {
        if (allGames.length === 0 && !isLoading) {
             setDisplayedGames([]); // Asegurarse de limpiar si no hay juegos base
             return;
        }

        let workingGames = [...allGames];

        // Parsear valores de filtro
        const minPrice = filterMinPrice === '' ? NaN : parseFloat(filterMinPrice);
        const maxPrice = filterMaxPrice === '' ? NaN : parseFloat(filterMaxPrice);
        const discountPercent = parseInt(filterDiscountPercent, 10); // Convertir a número
        const titleQuery = filterTitle.toLowerCase().trim();

        // Aplicar filtros
        workingGames = workingGames.filter(game => {
            // Filtro por Título
            if (titleQuery && !game.titulo.toLowerCase().includes(titleQuery)) {
                return false;
            }

            // Filtro por Porcentaje de Descuento
            // Mostrar si el descuento del juego es >= al filtro, o si el filtro es 0 (sin filtro de descuento)
            // o si el juego no tiene descuento (precio_descuento_num es null) y el filtro es 0.
            if (discountPercent > 0) {
                if (game.precio_descuento_num === null || game.precio_descuento_num < discountPercent) {
                    return false;
                }
            }

            // Filtro por Precio
            if (typeof game.precio_num === 'number' && !isNaN(game.precio_num) && game.precio_num > 0) {
                // Juegos con precio (mayor que cero)
                let passesMin = true;
                let passesMax = true;
                if (!isNaN(minPrice)) passesMin = game.precio_num >= minPrice;
                if (!isNaN(maxPrice)) passesMax = game.precio_num <= maxPrice;
                if (!(passesMin && passesMax)) return false;
            } else if (typeof game.precio_num === 'number' && !isNaN(game.precio_num) && game.precio_num === 0) {
                // Juegos gratuitos (precio igual a cero)
                if (hideNoPrice) return false; // Ocultar si el checkbox está marcado
                // No mostrar si hay filtros de precio numérico activos
                if (!isNaN(minPrice) || !isNaN(maxPrice)) return false;
            } else {
                // Juegos sin precio numérico (null, undefined, NaN, o cualquier otro valor no numérico)
                if (hideNoPrice) return false;
                // No mostrar si hay filtros de precio numérico activos
                if (!isNaN(minPrice) || !isNaN(maxPrice)) return false;
            }
            
            return true; // Pasa todos los filtros aplicables
        });

        // Aplicar ordenación
        if (sortType !== 'default') {
            workingGames.sort((a, b) => {
                const priceA = a.precio_num === null ? (sortType === 'asc' ? Infinity : -Infinity) : a.precio_num;
                const priceB = b.precio_num === null ? (sortType === 'asc' ? Infinity : -Infinity) : b.precio_num;
                return sortType === 'asc' ? priceA - priceB : priceB - priceA;
            });
        }
        setDisplayedGames(workingGames);
    }, [allGames, isLoading, sortType, filterMinPrice, filterMaxPrice, filterDiscountPercent, filterTitle, hideNoPrice]);

    useEffect(() => {
        applyFiltersAndSort();
    }, [applyFiltersAndSort]);

    // Efecto para controlar la visibilidad del botón "Volver Arriba"
    useEffect(() => {
        const handleScroll = () => {
            // Mostrar el botón cuando el usuario ha desplazado más de 300px
            if (window.scrollY > 300) {
                setShowBackToTop(true);
            } else {
                setShowBackToTop(false);
            }
        };

        // Añadir el event listener para el scroll
        window.addEventListener('scroll', handleScroll);
        
        // Limpiar el event listener cuando el componente se desmonte
        return () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }, []);

    // Función para volver arriba
    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth' // Para un desplazamiento suave
        });
    };

    const handleSortChange = (e) => setSortType(e.target.value);
    
    const handleClearFilters = () => {
        setFilterMinPrice('');
        setFilterMaxPrice('');
        setFilterDiscountPercent('0');
        setFilterTitle('');
        setSortType('default');
        setHideNoPrice(false); // Resetear el filtro de ocultar juegos sin precio
    };

    if (isLoading) return <div className="container"><p>Cargando juegos...</p></div>;
    if (error) return <div className="container"><p>Error al cargar datos: {error}</p></div>;

    return (
        <div className="container">
            <h1>Juegos de Xbox para PC</h1>
            {fechaActualizacion && (
                <p className="update-info">Última actualización: {fechaActualizacion}</p>
            )}
            <div className="controls">
                {/* Sección de Ordenación */}
                <div className="sort-controls">
                    <label htmlFor="sort-select">Ordenar por precio:</label>
                    <select id="sort-select" value={sortType} onChange={handleSortChange}>
                        <option value="default">Por defecto</option>
                        <option value="asc">Menor a Mayor</option>
                        <option value="desc">Mayor a Menor</option>
                    </select>
                </div>

                {/* Sección de Filtro por Título */}
                <div className="filter-title-control">
                     <label htmlFor="filter-title">Buscar por título:</label>
                     <input
                         type="text"
                         id="filter-title"
                         placeholder="Nombre del juego..."
                         value={filterTitle}
                         onChange={(e) => setFilterTitle(e.target.value)}
                     />
                </div>

                {/* Sección de Filtro por Precio */}
                <div className="filter-controls">
                    <div className="price-input-group">
                        <label htmlFor="min-price">Precio Mín (ARS):</label>
                        <input
                            type="number"
                            id="min-price"
                            placeholder="0"
                            value={filterMinPrice}
                            onChange={(e) => setFilterMinPrice(e.target.value)}
                        />
                    </div>
                    <div className="price-input-group">
                        <label htmlFor="max-price">Precio Máx (ARS):</label>
                        <input
                            type="number"
                            id="max-price"
                            placeholder="5000"
                            value={filterMaxPrice}
                            onChange={(e) => setFilterMaxPrice(e.target.value)}
                        />
                    </div>
                </div>
                
                {/* Sección de Filtro por Descuento */}
                <div className="filter-discount-control">
                    <label htmlFor="filter-discount">Descuento Mínimo: {filterDiscountPercent}%</label>
                    <input
                        type="range"
                        id="filter-discount"
                        min="0"
                        max="100"
                        step="5"
                        value={filterDiscountPercent}
                        onChange={(e) => setFilterDiscountPercent(e.target.value)}
                    />
                </div>

                {/* Checkbox para ocultar juegos sin precio */}
                <div className="filter-checkbox-control">
                    <label>
                        <input
                            type="checkbox"
                            checked={hideNoPrice}
                            onChange={(e) => setHideNoPrice(e.target.checked)}
                        />
                        Ocultar juegos sin precio y gratuitos
                    </label>
                </div>

                {/* Botón de Limpiar Filtros */}
                <div className="clear-filters-wrapper">
                     <button id="clear-filter-button" onClick={handleClearFilters}>Limpiar Filtros</button>
                </div>
            </div>
            
            {/* Contador de juegos */}
            <div className="games-counter">
                Mostrando {displayedGames.length} de {allGames.length} juegos
            </div>
            
            <GameList games={displayedGames} />
            
            {/* Botón Volver Arriba */}
            {showBackToTop && (
                <button 
                    className="back-to-top-button" 
                    onClick={scrollToTop}
                    aria-label="Volver arriba"
                >
                    ↑
                </button>
            )}
        </div>
    );
}

export default App;