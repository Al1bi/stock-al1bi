# Book Tracker

Un monitor automático construido con Flask que rastrea el stock y los precios de una lista de libros, enviando notificaciones push en tiempo real cuando hay cambios.

## Caracteristicas Principales

* Monitoreo de stock y precios directamente del catálogo.
* Notificaciones push al instante mediante [ntfy](https://ntfy.sh/).
* Almacenamiento en la nube usando Upstash Redis y JSONBin.

## Instalacion

1. **Clona el repositorio e instala dependencias:**
```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
pip install -r requirements.txt

```

2. **Configura tu entorno:**
Crea un archivo `.env` en la raíz con tus credenciales:
```env
JSONBIN_API_KEY=tu_api_key
JSONBIN_BIN_ID=tu_bin_id
UPSTASH_REDIS_URL=tu_url_redis
UPSTASH_REDIS_TOKEN=tu_token_redis
NTFY_TOPIC=tu_tema_ntfy
SCAN_AUTH_TOKEN=tu_token_secreto

```

## Uso

1. **Levanta el servidor localmente:**
```bash
python app.py

```

2. **Ejecuta un escaneo:**
Llama a la ruta protegida (ideal para configurar en un cronjob cada 20 minutos):
```text
GET http://localhost:5000/scan?token=tu_token_secreto

```