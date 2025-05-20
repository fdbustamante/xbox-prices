import { render, screen } from '@testing-library/react';
import GameItem from '../components/GameItem';
import { vi } from 'vitest';

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

describe('GameItem', () => {
  const game: TestGame = {
    id: '1',
    link: 'link1',
    titulo: 'Test Game',
    precio_num: 10,
    imagen_url: 'http://example.com/image.png',
    precio_descuento_num: 5,
    precio_old_num: 20,
    precio_texto: 'ARS$ 10.00',
    precio_cambio: null, // Ensure this matches one of the allowed literal types or null
    precio_anterior_num: null,
  };

  it('renders game title and price', () => {
    // Mock the onSelectToggle function
    const mockOnSelectToggle = vi.fn();
    render(<GameItem game={game} isSelected={false} onSelectToggle={mockOnSelectToggle} />);
    const title = screen.getByText(/Test Game/i);
    // Check for the current price, as precio_texto is used when precio_num is not a positive number
    const price = screen.getByText(/ARS\$ 10.00/i); 
    expect(title).toBeInTheDocument();
    expect(price).toBeInTheDocument();
  });
});
