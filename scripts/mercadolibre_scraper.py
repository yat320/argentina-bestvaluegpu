#!/usr/bin/env python3
"""Simple MercadoLibre scraper to refresh GPU prices.

This script reads `data/gpus.json`, queries the official MercadoLibre
search API for each GPU (by default using the GPU `name` as the query),
and updates `priceArs` with the minimum ARS price found in the search
results.

Usage examples:
    python scripts/mercadolibre_scraper.py
    python scripts/mercadolibre_scraper.py --dry-run --max-results 5

The script is intentionally lightweight and avoids third-party
dependencies so it can run anywhere Python 3 is available.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://api.mercadolibre.com/sites/MLA/search"
DEFAULT_SLEEP_SECONDS = 0.35  # avoid hammering the public endpoint


def load_gpu_data(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_gpu_data(path: Path, data: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(list(data), fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def fetch_min_price(query: str, max_results: int) -> Optional[float]:
    """
    Devuelve el precio mínimo en ARS para la búsqueda dada.
    Usa la API pública de MercadoLibre (sites/MLA/search) e intenta
    hacerse pasar por un navegador normal vía User-Agent.
    """
    params = {
        "q": query,
        "limit": max_results,
    }
    query_string = urlencode(params)
    url = f"{API_URL}?{query_string}"

    # Headers para que no parezca un bot “crudo”
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        print(f"[ERROR] Failed to fetch '{query}': {exc}", file=sys.stderr)
        return None

    results = payload.get("results", [])
    prices = [
        item.get("price")
        for item in results
        if item.get("currency_id") == "ARS"
    ]
    prices = [price for price in prices if isinstance(price, (int, float))]
    if not prices:
        print(f"[WARN] No ARS prices found for '{query}'", file=sys.stderr)
        return None
    return min(prices)


def update_prices(
    gpus: List[Dict[str, Any]],
    max_results: int,
    dry_run: bool,
    sleep_seconds: float,
    verbose: bool = True,
) -> bool:
    def log(message: str, *, error: bool = False) -> None:
        if not verbose:
            return
        stream = sys.stderr if error else sys.stdout
        print(message, file=stream)

    updated = False
    for gpu in gpus:
        query = gpu.get("mlQuery") or gpu.get("name")
        if not query:
            log("[WARN] GPU entry missing 'name' field; skipping", error=True)
            continue

        price = fetch_min_price(query, max_results)
        if price is None:
            continue

        old_price = gpu.get("priceArs")
        new_price = round(price)
        gpu["priceArs"] = new_price
        log(f"[INFO] {query}: ARS {new_price:,.0f}")
        if old_price != new_price:
            updated = True

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    if dry_run:
        log("[INFO] Dry run enabled; data file not modified.")
        return False

    return updated


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update GPU prices using MercadoLibre search API.")
    parser.add_argument(
        "--data-file",
        type=Path,
        default=Path("data/gpus.json"),
        help="Path to the GPU dataset JSON file (default: data/gpus.json)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Number of MercadoLibre search results to inspect for each GPU (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch prices but do not overwrite the JSON file.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help="Seconds to wait between requests (default: 0.35)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    gpus = load_gpu_data(args.data_file)

    data_changed = update_prices(
        gpus=gpus,
        max_results=args.max_results,
        dry_run=args.dry_run,
        sleep_seconds=max(args.sleep, 0),
    )

    if not args.dry_run and data_changed:
        save_gpu_data(args.data_file, gpus)
        print(f"[INFO] Updated {args.data_file}")
    elif not args.dry_run:
        print("[INFO] Prices already up to date; no changes written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
