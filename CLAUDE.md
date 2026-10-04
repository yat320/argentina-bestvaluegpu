# BestValueGPU Argentina — guía para Claude Code

Página estática que ordena placas de video por puntos de 3DMark por peso, con precios de Mercado Libre Argentina. Ver el README para el formato de `data/gpus.json` y `data/precios.json`.

- Rendimiento: puntaje de 3DMark, siempre la misma prueba para todas las placas (en la escala de bestvaluegpu, una GTX 1070 da ~6080 y una GTX 1080 ~7570). Los valores actuales son aproximados y hay que verificarlos.
- Value: puntos por cada $100.000 en escala de 0 a 100, donde 100 es la mejor placa de esa condición (nuevas y usadas por separado). La búsqueda y el filtro de marca no lo cambian. Se muestran las dos columnas a propósito: pts/$100k sirve para comparar en el tiempo y Value de un vistazo.
- Precio: la mediana de las publicaciones del modelo exacto, nunca el mínimo de una búsqueda.

## Lo que ya sabemos de Mercado Libre (no volver a equivocarse acá)

1. **La API de búsqueda no es pública.** Desde abril de 2025, `GET https://api.mercadolibre.com/sites/MLA/search` pide un token OAuth. Sin token devuelve 403.
2. **El 403 no venía del User-Agent.** Cambiar headers no lo arregla. Ante un 403, revisar el token: si falta, si venció (dura ~6 h) o si no tiene permisos.
3. **ML bloquea IPs de datacenter**, en la API y en el HTML del listado. El scraping se prueba y se corre desde una PC con IP de casa; desde la nube o desde GitHub Actions no anda.
4. **El matching de modelos es frágil.** Confunden:
   - variantes con el mismo número: 4060 y 4060 Ti, 4070 y 4070 Super, RX 7600 y 7600 XT;
   - la misma placa con distinta memoria: 3060 12GB y 8GB, 4060 Ti 8GB y 16GB;
   - cosas que no son la placa: notebooks, PCs armadas, coolers, backplates, cajas vacías.

   Cualquier cambio al matching se prueba con títulos reales guardados, mirando los falsos positivos.
5. **Hay precios basura:** $1 o $999999 para figurar, precios en dólares, por cuota o por unidad de un lote, reacondicionadas y placas de minería. `scripts/precios_desde_csv.py` descarta lo que está a menos de la mitad o más del doble de la mediana, pero el matching tiene que venir limpio.
6. **No copiar del código viejo** (en el historial de git, antes de octubre de 2026): le pegaba a la API sin token, intentaba resolver el 403 con headers de navegador y se quedaba con el precio mínimo sin filtrar.

## Cómo trabajar

- Ante un error, mirar la respuesta real (código HTTP y cuerpo) antes de suponer la causa.
- Para depurar el scraping del HTML, guardar la página bajada en `debug/` (está en `.gitignore`) y trabajar sobre esa copia.
- Pausa de un par de segundos entre pedidos a ML.
- Credenciales en `.env`, nunca en el código ni en git.
- Probar la página en un ancho de celular (400 px): la tabla se desliza de costado, la página no.
