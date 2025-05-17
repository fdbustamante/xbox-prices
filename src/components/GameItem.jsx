import React from 'react';

function GameItem({ game }) {
    const isValidImageUrl = game.imagen_url && game.imagen_url !== "Imagen no encontrada" && game.imagen_url.startsWith('http');

    let discountColorClass = '';
    if (game.precio_descuento_num !== null && game.precio_descuento_num > 0) {
        if (game.precio_descuento_num > 50) {
            discountColorClass = 'discount-high';
        } else if (game.precio_descuento_num >= 21) {
            discountColorClass = 'discount-medium';
        } else {
            discountColorClass = 'discount-low';
        }
    }
    
    // Función para limpiar el título eliminando contenido entre paréntesis
    const cleanGameTitle = (title) => {
        return title.replace(/\s*\([^)]*\)/g, '').trim();
    };

    return (
        <li className="game-card">
            {isValidImageUrl ? (
                <img 
                    src={game.imagen_url} 
                    alt={game.titulo} 
                    onError={(e) => { 
                        e.target.style.display = 'none';
                        const placeholder = e.target.parentElement.querySelector('.game-image-placeholder-active');
                        if (placeholder) placeholder.style.display = 'flex';
                    }}
                />
            ) : null}
             
            {!isValidImageUrl && (
                 <div className="game-image-placeholder game-image-placeholder-active" style={{display: isValidImageUrl ? 'none': 'flex'}}>Sin Imagen</div>
            )}

            <div className="game-card-content">
                <div className="game-title" title={game.titulo}>{game.titulo}</div>
                
                <div className="game-prices">
                    {/* Mostrar descuento primero si existe */}
                    {game.precio_descuento_num !== null && game.precio_descuento_num > 0 && (
                        <div className="game-price-line">
                            <span className={`game-discount-percentage ${discountColorClass}`}>
                                -{game.precio_descuento_num}%
                            </span>
                        </div>
                    )}

                    {/* Mostrar precio viejo si existe y es diferente del actual */}
                    {game.precio_old_num !== null && game.precio_old_num !== game.precio_num && (
                        <div className="game-price-line">
                            <span className="game-price-old">
                                ARS$ {game.precio_old_num.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} {/* Sin decimales para precio viejo */}
                            </span>
                        </div>
                    )}
                    
                    {/* Precio Actual (o texto como "Gratis", "Game Pass") */}
                    <div className="game-price-line">
                        {game.precio_num !== null && typeof game.precio_num === 'number' && game.precio_num > 0 ? (
                            <span className="game-price-current">
                                ARS$ {game.precio_num.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                        ) : game.precio_num === 0 ? ( // Específicamente para "Gratis"
                            <span className="game-price-text">Gratis</span>
                        ): ( // Para "Incluido con Game Pass" u otros textos
                            <span className="game-price-text">{game.precio_texto}</span>
                        )}
                    </div>
                    
                    {/* Indicador de cambio de precio */}
                    {game.precio_cambio && (
                        <div className="game-price-line">
                            <span className={`game-price-change ${game.precio_cambio === 'subió' || game.precio_cambio === 'increased' ? 'increased' : 
                                           game.precio_cambio === 'bajó' || game.precio_cambio === 'decreased' ? 'decreased' : 'unchanged'}`}>
                                {(game.precio_cambio === 'increased' || game.precio_cambio === 'subió') && '↑ Subió'}
                                {(game.precio_cambio === 'decreased' || game.precio_cambio === 'bajó') && '↓ Bajó'}
                                {(game.precio_cambio === 'unchanged' || game.precio_cambio === 'sigue igual') && '→ Sin cambios'}
                                
                                {/* Mostrar precio anterior si existe */}
                                {game.precio_anterior_num !== null && game.precio_anterior_num !== undefined && 
                                 (game.precio_cambio === 'increased' || game.precio_cambio === 'decreased' || 
                                  game.precio_cambio === 'subió' || game.precio_cambio === 'bajó') && (
                                    <span className="precio-anterior">
                                        {' '}(Antes: ARS$ {game.precio_anterior_num.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})
                                    </span>
                                )}
                            </span>
                        </div>
                    )}
                </div>
            </div>
            
            <div className="game-link">
                <a href={game.link} target="_blank" rel="noopener noreferrer">
                    Ver en la Tienda
                </a>
                <a 
                    href={`https://www.youtube.com/results?search_query=${encodeURIComponent(cleanGameTitle(game.titulo) + "+review")}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                >
                    YouTube
                </a>
                <a 
                    href={`https://store.steampowered.com/search/?term=${encodeURIComponent(cleanGameTitle(game.titulo))}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                >
                    Steam
                </a>
            </div>
        </li>
    );
}

export default GameItem;