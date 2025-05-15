// src/components/GameList.jsx (solo para confirmar el id)
import React from 'react';
import GameItem from './GameItem';

function GameList({ games }) {
    if (!games || games.length === 0) {
        return <p id="no-games-message">No hay juegos que mostrar con los filtros actuales.</p>;
    }

    return (
        <ul id="game-grid"> {/* Asegúrate de que el id esté aquí */}
            {games.map((game) => (
                <GameItem key={game.id || game.link || game.titulo} game={game} />
            ))}
        </ul>
    );
}

export default GameList;