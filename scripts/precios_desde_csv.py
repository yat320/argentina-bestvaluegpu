#!/usr/bin/env python3
"""Arma data/precios.json desde un CSV de precios cargados a mano o por un scraper.

El CSV tiene una fila por publicación: id,condicion,precio
  - id: el de data/gpus.json (por ejemplo rtx-4060)
  - condicion: nueva o usada
  - precio: en pesos, sin puntos

Por cada placa y condición guarda la mediana de lo que queda después de
descartar los precios a más de la mitad o el doble de la mediana, y cuántas
publicaciones quedaron.

    python scripts/precios_desde_csv.py data/precios.csv
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path
from statistics import median

DATA = Path(__file__).resolve().parent.parent / "data"


def limpiar(precios):
    m = median(precios)
    return [p for p in precios if m / 2 <= p <= m * 2]


def main(ruta_csv):
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
            crudos.setdefault(gid, {}).setdefault(cond, []).append(float(fila["precio"]))

    precios = {}
    for gid, conds in crudos.items():
        for cond, lista in conds.items():
            buenos = limpiar(lista)
            precios.setdefault(gid, {})[cond] = {
                "precio": round(median(buenos)),
                "publicaciones": len(buenos),
            }

    salida = {
        "ejemplo": False,
        "actualizado": date.today().isoformat(),
        "fuente": f"Mercado Libre, desde {Path(ruta_csv).name}",
        "precios": precios,
    }
    (DATA / "precios.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ok] {sum(len(c) for c in precios.values())} precios en data/precios.json")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python scripts/precios_desde_csv.py data/precios.csv")
    main(sys.argv[1])
