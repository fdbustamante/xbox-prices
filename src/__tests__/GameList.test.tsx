import { render, screen } from '@testing-library/react';
import GameList from '../components/GameList';

// Basic type for the game object used in this test
interface TestGame {
  id: string;
  link: string;
  titulo: string;
  precio_num: number | null;
  imagen_url: string;
  precio_descuento_num: number | null;
  precio_old_num: number | null;
  precio_texto: string | null;
  precio_cambio: 'subió' | 'bajó' | 'sigue igual' | 'increased' | 'decreased' | 'unchanged' | null; // Made specific
  precio_anterior_num: number | null;
}

describe('GameList', () => {
  it('renders no games message when games array is empty', () => {
    render(<GameList games={[]} />);
    const message = screen.getByText(/No hay juegos que mostrar con los filtros actuales./i);
    expect(message).toBeInTheDocument();
  });

  it('renders a list of games', () => {
    const games: TestGame[] = [
      { id: '1', link: 'link1', titulo: 'Game 1', precio_num: 10, imagen_url: 'url1', precio_descuento_num: null, precio_old_num: null, precio_texto: 'ARS$ 10.00', precio_cambio: null, precio_anterior_num: null },
      { id: '2', link: 'link2', titulo: 'Game 2', precio_num: 20, imagen_url: 'url2', precio_descuento_num: 5, precio_old_num: 25, precio_texto: 'ARS$ 20.00', precio_cambio: null, precio_anterior_num: null },
    ];
    render(<GameList games={games} />);
    const game1 = screen.getByText(/Game 1/i);
    const game2 = screen.getByText(/Game 2/i);
    expect(game1).toBeInTheDocument();
    expect(game2).toBeInTheDocument();
  });
});
