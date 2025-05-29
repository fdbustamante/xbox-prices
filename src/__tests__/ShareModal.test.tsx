import { render, screen } from '@testing-library/react';
import ShareModal from '../components/ShareModal';
import { vi } from 'vitest';

// Basic type for the game object used in this test (subset for ShareModal)
interface SelectedGame {
  id: string;
  link: string;
  titulo: string;
  precio_num: number | null;
  // imagen_url is not directly used by ShareModal for rendering the list, but good to have for consistency
  imagen_url?: string; 
  precio_descuento_num: number | null;
  precio_old_num: number | null;
  precio_texto: string | null;
}

describe('ShareModal', () => {
  const selectedGames: SelectedGame[] = [
    { id: '1', link: 'link1', titulo: 'Game 1', precio_num: 10, imagen_url: 'url1', precio_descuento_num: null, precio_old_num: null, precio_texto: 'ARS$ 10.00' },
    { id: '2', link: 'link2', titulo: 'Game 2', precio_num: 20, imagen_url: 'url2', precio_descuento_num: 5, precio_old_num: 25, precio_texto: 'ARS$ 20.00' },
  ];

  it('renders modal with selected games', () => {
    const mockOnClose = vi.fn();
    render(<ShareModal selectedGames={selectedGames} onClose={mockOnClose} />);
    const headline = screen.getByText(/Compartir Juegos Seleccionados/i);
    const game1 = screen.getByText(/Game 1/i);
    const game2 = screen.getByText(/Game 2/i);
    expect(headline).toBeInTheDocument();
    expect(game1).toBeInTheDocument();
    expect(game2).toBeInTheDocument();
  });
});
