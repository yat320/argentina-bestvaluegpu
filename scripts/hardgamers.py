#!/usr/bin/env python3
"""Saca precios de placas de video de páginas de HardGamers (hardgamers.com.ar).

HardGamers junta productos nuevos de tiendas argentinas. Cada producto viene
con microdatos de schema.org (nombre, precio en ARS, condición), así que no
depende del diseño de la página.

Lee páginas guardadas desde el navegador (Ctrl+S) o las baja de una URL, y
escribe un CSV con el formato de precios_desde_csv.py:

    id,condicion,precio,url,tienda,titulo

Solo quedan las publicaciones cuyo título coincide con una placa de
data/gpus.json: misma línea (RTX, GTX, RX, Arc), mismo número, misma variante
(Ti, Super, XT…) y, si el título dice la memoria, la misma VRAM.

    python scripts/hardgamers.py pagina1.html pagina2.html > data/precios.csv
    python scripts/hardgamers.py "https://www.hardgamers.com.ar/..." >> data/precios.csv
"""
import csv
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://www.hardgamers.com.ar"

# Línea, número y variante: "RTX 4060 TI", "RX7600 XT", "ARC B580".
CHIP = re.compile(r"\b(RTX|GTX|RX|ARC)\s*-?\s*([A-Z]?\d{3,4})(?:\s*(TI|SUPER|XTX|XT|GRE))?\b")
MEMORIA = re.compile(r"\b(\d{1,2})\s*GB\b")
# Títulos que nombran la placa pero no son una placa suelta.
NO_ES_PLACA = re.compile(
    r"\b(NOTEBOOK|LAPTOP|PC\s+(GAMER|ARMADA)|COMBO|KIT|COOLER|FAN|VENTILADOR|"
    r"SOPORTE|BACKPLATE|WATERBLOCK|RISER|CABLE|FUENTE|GABINETE|CAJA)\b"
)


def clave(texto):
    """('RTX', '4060', 'TI') a partir de un título o nombre, o None."""
    m = CHIP.search(texto.upper())
    return (m.group(1), m.group(2), m.group(3) or "") if m else None


def cargar_gpus():
    gpus = json.loads((DATA / "gpus.json").read_text(encoding="utf-8"))
    return [(clave(g["busqueda"]), g) for g in gpus if clave(g["busqueda"])]


def placa_de(titulo, gpus):
    """La placa de gpus.json que corresponde al título, o None."""
    t = titulo.upper()
    if NO_ES_PLACA.search(t):
        return None
    k = clave(t)
    if not k:
        return None
    memorias = {int(x) for x in MEMORIA.findall(t)}
    for kg, g in gpus:
        if kg != k:
            continue
        if memorias and g["vram"] not in memorias:
            continue
        return g
    return None


def texto(fragmento):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragmento))).strip()


def productos(pagina):
    """(titulo, precio, url, tienda) de cada producto de la página."""
    # Tarjetas de producto (búsqueda y "similares" de una página de producto).
    for art in re.findall(r"<article\b.*?</article>", pagina, re.S):
        nombre = re.search(r'itemprop="name"[^>]*>(.*?)<', art, re.S)
        precio = re.search(r'itemprop="price"\s+content="(\d+(?:\.\d+)?)"', art)
        url = re.search(r'href="(https://www\.hardgamers\.com\.ar/product/[^"]+)"', art)
        tienda = re.search(r'class="store"[^>]*>(.*?)<', art, re.S)
        cond = re.search(r'itemprop="itemCondition"\s+href="[^"]*/(\w+)"', art)
        if not (nombre and precio and url):
            continue
        if cond and cond.group(1) != "NewCondition":
            continue
        yield (texto(nombre.group(1)), float(precio.group(1)), url.group(1),
               texto(tienda.group(1)) if tienda else "")
    # El producto principal de una página de producto.
    canonico = re.search(r'<link rel="canonical" href="([^"]+/product/[^"]+)"', pagina)
    h1 = re.search(r'<h1[^>]*itemprop="name"[^>]*>(.*?)</h1>', pagina, re.S)
    oferta = re.search(r'class="Price-And-Store-Link".*?itemprop="price"\s+content="(\d+(?:\.\d+)?)"', pagina, re.S)
    tienda = re.search(r'title="Visitar sitio de ([^"]+)"', pagina)
    if canonico and h1 and oferta:
        yield (texto(h1.group(1)), float(oferta.group(1)), canonico.group(1),
               html.unescape(tienda.group(1)) if tienda else "")


def leer(fuente):
    if fuente.startswith("http"):
        req = Request(fuente, headers={"User-Agent": "Mozilla/5.0 (BestValueGPU Argentina)"})
        with urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", errors="replace")
    return Path(fuente).read_text(encoding="utf-8", errors="replace")


def main(fuentes):
    gpus = cargar_gpus()
    out = csv.writer(sys.stdout)
    out.writerow(["id", "condicion", "precio", "url", "tienda", "titulo"])
    vistos = set()
    for i, fuente in enumerate(fuentes):
        if i and fuente.startswith("http"):
            time.sleep(3)  # despacio con el sitio
        n = 0
        for titulo, precio, url, tienda in productos(leer(fuente)):
            g = placa_de(titulo, gpus)
            if not g or url in vistos:
                if not g:
                    print(f"[sin placa] {titulo}", file=sys.stderr)
                continue
            vistos.add(url)
            out.writerow([g["id"], "nueva", round(precio), url, tienda, titulo])
            n += 1
        print(f"[ok] {fuente}: {n} publicaciones", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
