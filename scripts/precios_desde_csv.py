#!/usr/bin/env python3
"""Actualiza data/precios.json desde un CSV de precios cargados a mano o por un scraper.

El CSV tiene una fila por publicación: id,condicion,precio[,url]
  - id: el de data/gpus.json (por ejemplo rtx-4060)
  - condicion: nueva o usada
  - precio: en pesos, sin puntos
  - url (opcional): link a la publicación

Por cada placa y condición guarda la mediana de lo que queda después de
descartar los precios a menos de la mitad o más del doble de la mediana,
cuántas publicaciones quedaron y la más barata de ellas que tenga url.

Solo reemplaza las condiciones que trae el CSV: las nuevas (HardGamers, en
GitHub Actions) y las usadas (Mercado Libre, desde una PC) se actualizan
por separado sin pisarse.

    python scripts/precios_desde_csv.py data/precios.csv --fuente hardgamers
    python scripts/precios_desde_csv.py data/usadas.csv --fuente mercadolibre
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path
from statistics import median

DATA = Path(__file__).resolve().parent.parent / "data"

# Lo que la página muestra como fuente y adónde lleva el link del precio
# ({q} es el nombre de la placa). Sin "busqueda", el link va al listado de ML.
FUENTES = {
    "hardgamers": {
        "nombre": "HardGamers",
        "url": "https://www.hardgamers.com.ar/search?category=placas-de-video",
        "busqueda": "https://www.hardgamers.com.ar/search?text={q}",
    },
    "mercadolibre": {
        "nombre": "Mercado Libre",
        "url": "https://www.mercadolibre.com.ar",
    },
}


def anterior():
    """El precios.json actual, con el formato viejo (una sola fuente) pasado al nuevo."""
    ruta = DATA / "precios.json"
    if not ruta.exists():
        return {"precios": {}, "fuentes": {}}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if datos.get("ejemplo"):
        return {"precios": {}, "fuentes": {}}
    if "fuentes" not in datos:
        conds = {c for p in datos.get("precios", {}).values() for c in p}
        datos["fuentes"] = {
            c: {k: v for k, v in {
                "nombre": datos.get("fuenteNombre"),
                "url": datos.get("fuenteUrl"),
                "busqueda": datos.get("busquedas", {}).get(c),
                "actualizado": datos.get("actualizado"),
            }.items() if v}
            for c in conds
        }
    return datos


def limpiar(pubs):
    m = median(p for p, _ in pubs)
    return [(p, u) for p, u in pubs if m / 2 <= p <= m * 2]


def main(ruta_csv, fuente):
    ids = {g["id"] for g in json.loads((DATA / "gpus.json").read_text(encoding="utf-8"))}
    crudos = {}
    with open(ruta_csv, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            gid, cond = fila["id"].strip(), fila["condicion"].strip().lower()
            if gid not in ids:
                print(f"[aviso] id desconocido, se saltea: {gid}", file=sys.stderr)
                continue
            if cond not in ("nueva", "usada"):
                print(f"[aviso] condición inválida en {gid}: {cond}", file=sys.stderr)
                continue
            url = (fila.get("url") or "").strip()
            crudos.setdefault(gid, {}).setdefault(cond, []).append((float(fila["precio"]), url))

    previo = anterior()
    nuevas = {cond for conds in crudos.values() for cond in conds}
    # Se borran las condiciones que trae el CSV y se dejan las otras.
    precios = {}
    for gid, conds in previo["precios"].items():
        quedan = {c: d for c, d in conds.items() if c not in nuevas}
        if quedan:
            precios[gid] = quedan
    for gid, conds in crudos.items():
        for cond, lista in conds.items():
            buenos = limpiar(lista)
            dato = {
                "precio": round(median(p for p, _ in buenos)),
                "publicaciones": len(buenos),
            }
            con_url = [(p, u) for p, u in buenos if u]
            if con_url:
                p, u = min(con_url)
                dato["barata"] = {"precio": round(p), "url": u}
            precios.setdefault(gid, {})[cond] = dato

    fuentes = {c: f for c, f in previo["fuentes"].items() if c not in nuevas}
    for cond in nuevas:
        fuentes[cond] = {**FUENTES[fuente], "actualizado": date.today().isoformat()}

    salida = {"ejemplo": False, "fuentes": dict(sorted(fuentes.items())), "precios": precios}
    (DATA / "precios.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for cond in sorted(nuevas):
        n = sum(1 for c in precios.values() if cond in c)
        print(f"[ok] {n} placas {cond}s en data/precios.json")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 3 or args[1] != "--fuente" or args[2] not in FUENTES:
        sys.exit("Uso: python scripts/precios_desde_csv.py archivo.csv --fuente " + "|".join(FUENTES))
    main(args[0], args[2])
