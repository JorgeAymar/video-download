# Python Video Downloader

Herramienta sencilla en Python para descargar videos alojados en `iframe.mediadelivery.net`. El script extrae automáticamente la URL directa del video (MP4) desde los metadatos de la página (`og:video:url`) y lo descarga mostrando una barra de progreso.

## Características

- **Extracción Automática**: Detecta el enlace directo del video sin necesidad de intervención manual.
- **Nombres de Archivo**: Utiliza el título de la página para nombrar el archivo de video automáticamente.
- **Barra de Progreso**: Visualización clara del estado de la descarga gracias a `tqdm`.
- **Manejo de Archivos Grandes**: Descarga en "chunks" para no saturar la memoria RAM.

## Requisitos

- Python 3.x
- Dependencias (instalables vía `pip`):
  - `requests`
  - `beautifulsoup4`
  - `tqdm`

## Instalación

Si estás utilizando el entorno virtual (`venv`) ya configurado en este proyecto:

1. Asegúrate de tener las dependencias instaladas:
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```

## Uso

Ejecuta el script pasando la URL del video como argumento:

```bash
./venv/bin/python download_video.py [URL_DEL_VIDEO]
```

### Ejemplo

```bash
./venv/bin/python download_video.py https://iframe.mediadelivery.net/play/371698/a8da8e48-799e-48b0-b080-5c28b87d2f6d
```

Si no proporcionas ninguna URL, el script intentará descargar un video por defecto configurado en el código.

## Funcionamiento

1. El script hace una petición HTTP a la URL proporcionada simulando un navegador real (headers `User-Agent` y `Referer`).
2. Analiza el HTML buscando la etiqueta `<meta property="og:video:url">`.
3. Obtiene el título de la página para usarlo como nombre de archivo.
4. Inicia la descarga del archivo MP4 encontrado.
