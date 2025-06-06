import React, { useState, useEffect, useCallback } from 'react';
import GameList from './components/GameList';
import './style.css';
import { Game, GameData } from './types'; // Import Game and GameData types

// Define a type for the keys of precioCambioMapped
type PrecioCambioKey = 'increased' | 'decreased' | 'unchanged' | 'null';

function App() { // Removed : JSX.Element return type
    const [allGames, setAllGames] = useState<Game[]>([]);
    const [displayedGames, setDisplayedGames] = useState<Game[]>([]);
    const [visibleCount, setVisibleCount] = useState<number>(50);
    const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
    
    const [sortType, setSortType] = useState<string>('default');
    const [filterMinPrice, setFilterMinPrice] = useState<string>('');
    const [filterMaxPrice, setFilterMaxPrice] = useState<string>('');
    const [hideNoPrice, setHideNoPrice] = useState<boolean>(false);

    const [hiddenGameTitles, setHiddenGameTitles] = useState<string[]>([]);
    const [showHidden, setShowHidden] = useState<boolean>(false);

    const [filterDiscountPercent, setFilterDiscountPercent] = useState<string>('0');
    const [filterTitle, setFilterTitle] = useState<string>('');
    const [filterPriceChange, setFilterPriceChange] = useState<string>('all');

    const [showBackToTop, setShowBackToTop] = useState<boolean>(false);
    
    const [fechaActualizacion, setFechaActualizacion] = useState<string | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const storedHiddenGames = localStorage.getItem('hiddenGameTitles');
        if (storedHiddenGames) {
            try {
                const parsedHiddenGames = JSON.parse(storedHiddenGames);
                if (Array.isArray(parsedHiddenGames)) {
                    setHiddenGameTitles(parsedHiddenGames);
                } else {
                    console.warn("Stored hiddenGameTitles is not an array:", parsedHiddenGames);
                    setHiddenGameTitles([]); // Fallback to empty array
                }
            } catch (e) {
                console.error("Failed to parse hiddenGameTitles from localStorage:", e);
                setHiddenGameTitles([]); // Fallback to empty array on error
            }
        }
    }, []); // Runs once on mount

    const handleHideSelectedGames = (gamesToHide: Game[]) => {
        const titlesToHide = gamesToHide.map(game => game.titulo);
        setHiddenGameTitles(prevHiddenTitles => {
            const newHiddenTitlesSet = new Set([...prevHiddenTitles, ...titlesToHide]);
            const newHiddenTitlesArray = Array.from(newHiddenTitlesSet);
            localStorage.setItem('hiddenGameTitles', JSON.stringify(newHiddenTitlesArray));
            return newHiddenTitlesArray;
        });
    };

    useEffect(() => {
        setIsLoading(true);
        setError(null);
        const jsonUrl = `${import.meta.env.BASE_URL}xbox_pc_games.json`;

        fetch(jsonUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error al cargar el archivo JSON: ${response.statusText}`);
                }
                return response.json() as Promise<GameData>; 
            })
            .then(data => {
                const juegosData: Game[] = Array.isArray(data) ? data : data.juegos || [];
                const fechaCreacion: string | null = Array.isArray(data) ? null : data.fecha_creacion || null;
                
                if (fechaCreacion) {
                    console.log(`Datos actualizados el: ${fechaCreacion}`);
                    setFechaActualizacion(fechaCreacion);
                }
                
                const gamesWithId: Game[] = juegosData.map((game: Game, index: number) => ({
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

        let workingGames: Game[] = [...allGames];

        if (!showHidden) {
            workingGames = workingGames.filter(game => !hiddenGameTitles.includes(game.titulo));
        }

        const minPrice = filterMinPrice === '' ? NaN : parseFloat(filterMinPrice);
        const maxPrice = filterMaxPrice === '' ? NaN : parseFloat(filterMaxPrice);
        const discountPercent = parseInt(filterDiscountPercent, 10);
        const titleQuery = filterTitle.toLowerCase().trim();

        workingGames = workingGames.filter(game => {
            if (titleQuery && !game.titulo.toLowerCase().includes(titleQuery)) {
                return false;
            }

            if (discountPercent > 0) {
                if (game.precio_descuento_num === null || game.precio_descuento_num === undefined || game.precio_descuento_num < discountPercent) {
                    return false;
                }
            }
            
            if (filterPriceChange !== 'all') {
                const precioCambioMapped: Record<PrecioCambioKey, Game['precio_cambio']> = {
                    'increased': 'subió',
                    'decreased': 'bajó',
                    'unchanged': 'sigue igual',
                    'null': null 
                };
                
                if (filterPriceChange === 'null') {
                    if (game.precio_cambio !== null) return false;
                } else {
                    if (!game.precio_cambio || 
                        (game.precio_cambio !== filterPriceChange && 
                         game.precio_cambio !== precioCambioMapped[filterPriceChange as PrecioCambioKey])) {
                        return false;
                    }
                }
            }

            if (typeof game.precio_num === 'number' && !isNaN(game.precio_num) && game.precio_num > 0) {
                let passesMin = true;
                let passesMax = true;
                if (!isNaN(minPrice)) passesMin = game.precio_num >= minPrice;
                if (!isNaN(maxPrice)) passesMax = game.precio_num <= maxPrice;
                if (!(passesMin && passesMax)) return false;
            } else if (typeof game.precio_num === 'number' && !isNaN(game.precio_num) && game.precio_num === 0) {
                if (hideNoPrice) return false;
                if (!isNaN(minPrice) || !isNaN(maxPrice)) return false;
            } else {
                if (hideNoPrice) return false;
                if (!isNaN(minPrice) || !isNaN(maxPrice)) return false;
            }
            
            return true;
        });

        if (sortType !== 'default') {
            workingGames.sort((a, b) => {
                const priceA = a.precio_num === null ? (sortType === 'asc' ? Infinity : -Infinity) : a.precio_num;
                const priceB = b.precio_num === null ? (sortType === 'asc' ? Infinity : -Infinity) : b.precio_num;
                return sortType === 'asc' ? priceA - priceB : priceB - priceA;
            });
        }
        setDisplayedGames(workingGames);
        setVisibleCount(50);
    }, [allGames, isLoading, sortType, filterMinPrice, filterMaxPrice, filterDiscountPercent, filterTitle, hideNoPrice, filterPriceChange, hiddenGameTitles, showHidden]);

    useEffect(() => {
        applyFiltersAndSort();
    }, [applyFiltersAndSort]);

    useEffect(() => {
        const handleScroll = () => {
            if (isLoadingMore || visibleCount >= displayedGames.length) return;
            const scrollPosition = window.innerHeight + window.scrollY;
            const threshold = document.body.offsetHeight - 200;
            if (scrollPosition >= threshold) {
                setIsLoadingMore(true);
                setTimeout(() => {
                    setVisibleCount(prevCount => Math.min(prevCount + 50, displayedGames.length));
                    setIsLoadingMore(false);
                }, 300);
            }
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [displayedGames.length, isLoadingMore, visibleCount]);

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > 300) {
                setShowBackToTop(true);
            } else {
                setShowBackToTop(false);
            }
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToTop = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => setSortType(e.target.value);
    
    const handleClearFilters = () => {
        setFilterMinPrice('');
        setFilterMaxPrice('');
        setFilterDiscountPercent('0');
        setFilterTitle('');
        setSortType('default');
        setHideNoPrice(false); // Resetear el filtro de ocultar juegos sin precio
        setFilterPriceChange('all'); // Resetear el filtro de cambios de precio
        setVisibleCount(50); // Resetear la paginación
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

                {/* Filtro por Cambio de Precio */}
                <div className="filter-price-change-control">
                    <label htmlFor="filter-price-change">Cambio de precio:</label>
                    <select 
                        id="filter-price-change"
                        value={filterPriceChange}
                        onChange={(e) => setFilterPriceChange(e.target.value)}
                    >
                        <option value="all">Todos</option>
                        <option value="increased">Precio subió</option>
                        <option value="decreased">Precio bajó</option>
                        <option value="unchanged">Sin cambios</option>
                        <option value="null">Sin histórico</option>
                    </select>
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

                {/* Checkbox para mostrar juegos ocultos */}
                <div className="filter-checkbox-control">
                    <label>
                        <input
                            type="checkbox"
                            checked={showHidden}
                            onChange={(e) => setShowHidden(e.target.checked)}
                        />
                        Mostrar juegos ocultos ({hiddenGameTitles.length})
                    </label>
                </div>
            </div>
            
            {/* Contador de juegos */}
            <div className="games-counter">
                Mostrando {Math.min(visibleCount, displayedGames.length)} de {displayedGames.length} juegos
            </div>
            
            <GameList
                games={displayedGames.slice(0, visibleCount)}
                onHideSelectedGames={handleHideSelectedGames}
            />
            
            {/* Carga de más juegos */}
            {isLoadingMore && (
                <div className="loading-more">
                    Cargando más juegos...
                </div>
            )}
            
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