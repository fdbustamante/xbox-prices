import { render, screen, waitFor } from '@testing-library/react';
import App from '../App';
import { vi } from 'vitest';

// Mockear fetch usando vi.stubGlobal
vi.stubGlobal('fetch', vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ juegos: [], fecha_creacion: '2023-01-01' }),
  })
));

describe('App', () => {
  beforeEach(() => {
    // Limpiar mocks antes de cada prueba si es necesario
    (fetch as ReturnType<typeof vi.fn>).mockClear();
  });

  it('renders headline after loading', async () => {
    render(<App />);
    // Esperar a que el estado de carga termine y el contenido se renderice
    await waitFor(() => {
      const headline = screen.getByText(/Juegos de Xbox para PC/i);
      expect(headline).toBeInTheDocument();
    });
  });
});
