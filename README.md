# Argentina BestValueGPU

Página estilo *bestvaluegpu* / *Kryptex - best GPUs for mining*,
adaptada a precios y contexto de Argentina.

## TODO

- Scraper / carga manual de datos de GPUs
- Cálculo de:
  - Hashrate
  - Consumo
  - Rentabilidad diaria
  - Costo por MH/s
  - ROI estimado en ARS / USD
- Filtros por:
  - Algoritmo / moneda
  - Rango de precio
  - Consumo eléctrico

## Datos mock en JSON

El frontend ahora consume `data/gpus.json` en vez de tener los datos embebidos en `src/app.js`. Esto permite:

- Editar el archivo manualmente con precios reales en ARS.
- Simular la respuesta del futuro backend/API (`/gpus`).
- Mantener el mismo esquema de campos usado por la tabla.

Para actualizar los datos podés reemplazar `data/gpus.json` mediante un script o scraper (por ejemplo, MercadoLibre).

## Scraper de precios (MercadoLibre)

Hay un script listo para consultar la API pública de MercadoLibre y refrescar los campos `priceArs` en `data/gpus.json`:

```bash
python scripts/mercadolibre_scraper.py          # actualiza precios in-place
python scripts/mercadolibre_scraper.py --dry-run  # solo muestra resultados
```

- Usa el campo `name` de cada GPU como query (opcionalmente se puede añadir `mlQuery` en el JSON para personalizar la búsqueda).
- Por defecto inspecciona los primeros 10 resultados y toma el precio mínimo en ARS.
- Incluye un `--sleep` configurable para no saturar la API pública.

## Backend API (FastAPI)

Hay un backend mínimo en `backend/app.py` (FastAPI) que expone endpoints
para servir los datos al frontend y disparar el scraper:

- `GET /api/gpus`: lee `data/gpus.json` y devuelve el listado actual.
- `POST /api/update-prices`: ejecuta el scraper internamente. Permite
  `dry_run`, ajustar `max_results` y `sleep_seconds`.

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}' \
  http://localhost:8000/api/update-prices
```

### Cómo levantarlo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload --port 8000
```

El backend ya incluye CORS abierto para poder usarlo desde el servidor
estático (`python -m http.server`). Si preferís servir todo detrás del
mismo dominio, montá el backend detrás de `/api` en tu reverse proxy.

### Frontend apuntando al backend

El frontend intenta cargar los datos siguiendo este orden:

1. Endpoint definido por el query param `?api=` (por ejemplo,
   `http://localhost:8000/api`).
2. `/api/gpus` en el mismo origen.
3. `data/gpus.json` (fallback local).

Con esto podés seguir editando el JSON a mano, usar el backend local o
implementar un proxy sin tocar el código del frontend.
