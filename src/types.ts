export interface Game {
  id: string;
  link: string;
  titulo: string;
  imagen_url?: string; // Optional as some games might not have it or it's "Imagen no encontrada"
  precio_num: number | null;
  precio_texto?: string | null; // e.g., "Gratis", "Incluido con Game Pass"
  precio_old_num?: number | null;
  precio_descuento_num?: number | null;
  precio_cambio?: 'subió' | 'bajó' | 'sigue igual' | 'increased' | 'decreased' | 'unchanged' | null;
  precio_anterior_num?: number | null;
  // For client-side processing, not from JSON directly
  isSelected?: boolean; 
}

// Type for the JSON data structure if it's nested under "juegos"
export interface GameData {
  juegos?: Game[]; // Optional if the root is directly an array of games
  fecha_creacion?: string;
  // Allow direct array of games as well for compatibility
  [index: number]: Game; 
}
