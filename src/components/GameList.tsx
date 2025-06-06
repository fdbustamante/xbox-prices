import React, { useState } from 'react';
import GameItem from './GameItem'; // Will resolve to GameItem.tsx
import ShareModal from './ShareModal'; // Will resolve to ShareModal.tsx
import { Game } from '../types'; // Import Game type

interface GameListProps {
  games: Game[];
  onHideGame: (title: string) => void; // New prop
}

const GameList: React.FC<GameListProps> = ({ games, onHideGame }) => {
    const [selectedGames, setSelectedGames] = useState<Game[]>([]);
    const [showShareModal, setShowShareModal] = useState<boolean>(false);
    
    const handleSelectToggle = (game: Game) => {
        setSelectedGames(prevSelectedGames => {
            const isAlreadySelected = prevSelectedGames.some(g => g.id === game.id || g.link === game.link);
            if (isAlreadySelected) {
                return prevSelectedGames.filter(g => g.id !== game.id && g.link !== game.link);
            } else {
                return [...prevSelectedGames, game];
            }
        });
    };

    if (!games || games.length === 0) {
        return <p id="no-games-message">No hay juegos que mostrar con los filtros actuales.</p>;
    }

    return (
        <div className="games-container">
            <ul id="game-grid">
                {games.map((game: Game) => (
                    <GameItem 
                        key={game.id || game.link || game.titulo} // game.id should be primary if always present
                        game={game} 
                        isSelected={selectedGames.some(g => g.id === game.id || g.link === game.link)}
                        onSelectToggle={handleSelectToggle}
                        onHideGame={onHideGame} // Pass the prop down
                    />
                ))}
            </ul>
            
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