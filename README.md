# BestValueGPU Argentina

Placas de video ordenadas por cuánto rinden por cada peso: puntos de 3DMark contra el precio en Mercado Libre. La idea es la de [bestvaluegpu.com](https://bestvaluegpu.com), con precios argentinos.

Es una página estática (`index.html`) que lee dos archivos:

- `data/gpus.json`: las placas. `id`, `nombre`, `marca`, `watt`, `vram`, `tdmark` (puntaje de 3DMark, la misma prueba para todas) y `busqueda` (lo que se busca en ML).
- `data/precios.json`: los precios, por `id` y condición:

```json
{ "ejemplo": false, "actualizado": "2026-10-04",
  "precios": { "rtx-4060": { "nueva": {"precio": 520000, "publicaciones": 20,
                                       "barata": {"precio": 489999, "url": "https://articulo.mercadolibre.com.ar/MLA-..."}},
                             "usada": {"precio": 400000, "publicaciones": 9} } } }
```

Con `"ejemplo": true` la página muestra un cartel de que los precios no son reales. **Hoy los precios son de ejemplo y los puntajes de 3DMark son aproximados.**

## Cómo verla

```bash
python -m http.server 8000   # y abrir http://localhost:8000
```

Abriendo `index.html` directo con doble clic no carga los datos: el navegador no deja leer archivos locales.

## Cómo actualizar los precios

Los precios se juntan en una PC con IP de casa: Mercado Libre bloquea las IPs de servidores y de la nube (incluido GitHub Actions).

1. Juntar las publicaciones en un CSV, una fila por publicación: `id,condicion,precio,url` (condición `nueva` o `usada`, precio en pesos sin puntos, url opcional). Puede salir de un scraper o cargarse a mano.
2. `python scripts/precios_desde_csv.py data/precios.csv` arma `data/precios.json`: por placa y condición, la mediana de las publicaciones después de sacar las que están a menos de la mitad o más del doble de la mediana, y la más barata que quedó con su link (`barata`), que la página muestra debajo del precio.
3. Commit y push.

### Desde HardGamers (placas nuevas)

[HardGamers](https://www.hardgamers.com.ar) junta productos nuevos de tiendas argentinas, con precio en pesos y link a la tienda. `scripts/hardgamers.py` lee sus páginas (guardadas con Ctrl+S o por URL), se queda con los productos que coinciden con una placa de `gpus.json` (misma línea, número, variante Ti/Super/XT y VRAM; descarta notebooks, PCs y accesorios) y escribe el CSV:

```bash
python scripts/hardgamers.py busqueda-4060.html producto-3060.html > data/precios.csv
python scripts/precios_desde_csv.py data/precios.csv
```

Cada fila lleva el link a la página del producto en HardGamers, que muestra la tienda. Las usadas siguen saliendo de Mercado Libre.

## Historia

Hasta octubre de 2026 este repo era un comparador para minar (hashrate, ROI) con un backend FastAPI y un scraper que usaba la API de búsqueda de ML sin token. Ethereum dejó de minarse en 2022 y esa API pide token desde abril de 2025, así que se reemplazó; el código viejo queda en el historial de git.
