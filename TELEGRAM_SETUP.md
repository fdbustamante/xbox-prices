# Notificaciones de Telegram para Xbox Prices Tracker

Este módulo permite enviar notificaciones a Telegram cuando se detectan juegos de Xbox que bajan de precio.

## Configuración inicial

### 1. Crear un bot en Telegram
1. Abre Telegram y busca a [@BotFather](https://t.me/BotFather)
2. Envía el comando `/newbot` y sigue las instrucciones
3. Cuando termine, BotFather te dará un token (algo como `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Guárdalo.

### 2. Obtener tu ID de chat
Hay varias formas de obtenerlo:

#### Opción A: Con @userinfobot
1. Busca a [@userinfobot](https://t.me/userinfobot) en Telegram
2. Envíale cualquier mensaje
3. Te responderá con tu ID (un número como `123456789`)

#### Opción B: Para un grupo
1. Añade al bot que creaste al grupo donde quieres recibir las notificaciones
2. Envía un mensaje al grupo mencionando al bot (ej: `@tu_bot prueba`)
3. Visita la URL: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` (reemplaza `<BOT_TOKEN>` con tu token)
4. Busca "chat":{"id": y ese número (que empieza con -) es tu ID de grupo

## Configuración para desarrollo local

### Opción 1: Archivo telegram_config.py (recomendado para desarrollo)

Edita el archivo `telegram_config.py` con tu información:
```python
BOT_TOKEN = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"  # Tu token
CHAT_ID = "123456789"  # Tu ID personal o de grupo
DEBUG = False  # Cambiar a True para probar sin necesidad de juegos con bajadas
```

⚠️ **Importante:** Este archivo está listado en `.gitignore` y NO debe subirse al repositorio.

### Opción 2: Variables de entorno (alternativa)

También puedes establecer variables de entorno en tu sistema:

```bash
# Para Linux/Mac
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
export TELEGRAM_CHAT_ID="123456789"
export TELEGRAM_DEBUG="False"

# Para Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
$env:TELEGRAM_CHAT_ID = "123456789"
$env:TELEGRAM_DEBUG = "False"
```

## Configuración para entorno de producción (GitHub Actions)

Para GitHub Actions, debes configurar los secretos en el repositorio:

1. En GitHub, ve a tu repositorio → Settings → Secrets and variables → Actions
2. Crea los siguientes secretos:
   - `TELEGRAM_BOT_TOKEN`: Tu token del bot de Telegram
   - `TELEGRAM_CHAT_ID`: Tu ID de chat o grupo
   - `TELEGRAM_DEBUG`: "true" o "false" (opcional, por defecto es "false")

## Probar la configuración

Ejecuta el siguiente comando para probar que todo funciona correctamente:

```bash
python test_telegram.py
```

Si todo está bien configurado, recibirás un mensaje de prueba en tu chat o grupo.

## Uso normal

Las notificaciones se enviarán automáticamente cada vez que se ejecute `scrap.py` y se encuentren juegos que hayan bajado de precio.

```bash
python scrap.py
```

El script enviará una notificación sólo si encuentra juegos con bajadas de precio, salvo que tengas activado el modo DEBUG.
