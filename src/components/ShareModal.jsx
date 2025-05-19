import React, { useState } from 'react';

function ShareModal({ selectedGames, onClose }) {
    const [copied, setCopied] = useState(false);
    
    // Generar lista de juegos en formato de texto
    const gamesList = selectedGames.map(game => {
        // Determinar precio actual
        const precio = game.precio_num !== null && typeof game.precio_num === 'number' && game.precio_num > 0 
            ? `ARS$ ${game.precio_num.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : game.precio_num === 0 
            ? "Gratis" 
            : game.precio_texto;
        
        // Información de descuento si existe
        let infoAdicional = "";
        
        // Si hay descuento
        if (game.precio_descuento_num !== null && game.precio_descuento_num > 0) {
            infoAdicional += ` [-${game.precio_descuento_num}%`;
            
            // Si también hay precio viejo
            if (game.precio_old_num !== null && game.precio_old_num !== game.precio_num) {
                infoAdicional += `, antes: ARS$ ${game.precio_old_num.toLocaleString('es-AR')}`;
            }
            
            infoAdicional += `]`;
        } 
        // Si solo hay precio viejo sin descuento explícito
        else if (game.precio_old_num !== null && game.precio_old_num !== game.precio_num) {
            infoAdicional += ` [antes: ARS$ ${game.precio_old_num.toLocaleString('es-AR')}]`;
        }
            
        return `- ${game.titulo} - ${precio}${infoAdicional} (${game.link})`;
    }).join('\n');
    
    const copyToClipboard = () => {
        navigator.clipboard.writeText(gamesList)
            .then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            })
            .catch(err => console.error('Error al copiar al portapapeles:', err));
    };
    
    return (
        <div className="share-modal-overlay">
            <div className="share-modal">
                <div className="share-modal-header">
                    <h2>Compartir Juegos Seleccionados</h2>
                    <button onClick={onClose} className="close-button">&times;</button>
                </div>
                <div className="share-modal-content">
                    <p className="share-modal-description">
                        {selectedGames.length} juego{selectedGames.length !== 1 ? 's' : ''} seleccionado{selectedGames.length !== 1 ? 's' : ''}:
                    </p>
                    <div className="selected-games-list">
                        {selectedGames.map(game => {
                            const precio = game.precio_num !== null && typeof game.precio_num === 'number' && game.precio_num > 0 
                                ? `ARS$ ${game.precio_num.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                : game.precio_num === 0 
                                ? "Gratis" 
                                : game.precio_texto;
                            
                            // Mostrar descuento si existe    
                            const descuento = game.precio_descuento_num !== null && game.precio_descuento_num > 0 
                                ? `-${game.precio_descuento_num}%` 
                                : null;
                                
                            // Precio viejo si existe
                            const precioViejo = game.precio_old_num !== null && game.precio_old_num !== game.precio_num
                                ? `ARS$ ${game.precio_old_num.toLocaleString('es-AR')}`
                                : null;
                                
                            return (
                                <div key={game.id || game.link || game.titulo} className="selected-game-item">
                                    <span className="game-title">{game.titulo}</span>
                                    <div className="game-price-container">
                                        {descuento && <span className="game-discount">{descuento}</span>}
                                        <div className="price-details">
                                            {precioViejo && <span className="game-price-old">{precioViejo}</span>}
                                            <span className="game-price">{precio}</span>
                                        </div>
                                    </div>
                                    <a href={game.link} target="_blank" rel="noopener noreferrer" className="game-link">Tienda</a>
                                </div>
                            );
                        })}
                    </div>
                </div>
                <div className="share-modal-actions">
                    <button 
                        onClick={() => {
                            const fecha = new Date().toLocaleDateString('es-AR');
                            const whatsappText = encodeURIComponent(`🎮 JUEGOS DE XBOX EN OFERTA (${fecha}) 🎮\n\n${gamesList}\n\n📊 Lista generada con Xbox Prices Argentina`);
                            window.open(`https://wa.me/?text=${whatsappText}`, '_blank');
                        }}
                        className="whatsapp-button"
                    >
                        Compartir por WhatsApp
                    </button>
                    <button 
                        onClick={copyToClipboard} 
                        className={`copy-button ${copied ? 'copied' : ''}`}
                    >
                        {copied ? 'Copiado' : 'Copiar al portapapeles'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ShareModal;
