// src/components/GameList.jsx (solo para confirmar el id)
import React, { useState } from 'react';
import GameItem from './GameItem';
import ShareModal from './ShareModal';

function GameList({ games }) {
    const [selectedGames, setSelectedGames] = useState([]);
    const [showShareModal, setShowShareModal] = useState(false);
    
    const handleSelectToggle = (game) => {
        setSelectedGames(prev => {
            const isAlreadySelected = prev.some(g => g.id === game.id || g.link === game.link);
            if (isAlreadySelected) {
                return prev.filter(g => g.id !== game.id && g.link !== game.link);
            } else {
                return [...prev, game];
            }
        });
    };

    if (!games || games.length === 0) {
        return <p id="no-games-message">No hay juegos que mostrar con los filtros actuales.</p>;
    }

    return (
        <div className="games-container">
            <ul id="game-grid"> {/* Asegúrate de que el id esté aquí */}
                {games.map((game) => (
                    <GameItem 
                        key={game.id || game.link || game.titulo} 
                        game={game} 
                        isSelected={selectedGames.some(g => g.id === game.id || g.link === game.link)}
                        onSelectToggle={handleSelectToggle}
                    />
                ))}
            </ul>
            
            {/* Botón flotante de compartir */}
            {selectedGames.length > 0 && (
                <div className="floating-buttons">
                    <button 
                        className="share-btn"
                        onClick={() => setShowShareModal(true)}
                        title="Compartir juegos seleccionados"
                    >
                        Compartir ({selectedGames.length})
                    </button>
                </div>
            )}
            
            {/* Modal de Compartir */}
            {showShareModal && (
                <ShareModal 
                    selectedGames={selectedGames} 
                    onClose={() => setShowShareModal(false)} 
                />
            )}
        </div>
    );
}

export default GameList;