"""Simple FastAPI backend for Argentina BestValueGPU."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scripts.mercadolibre_scraper import (
    load_gpu_data,
    save_gpu_data,
    update_prices,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "gpus.json"

app = FastAPI(title="Argentina BestValueGPU API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


class UpdatePricesRequest(BaseModel):
    dry_run: bool = Field(False, description="Si es true, no se escribe el JSON")
    max_results: int = Field(
        10,
        ge=1,
        le=50,
        description="Cantidad de resultados de MercadoLibre a inspeccionar",
    )
    sleep_seconds: float = Field(
        0.0,
        ge=0.0,
        le=2.0,
        description="Pausa opcional entre requests para evitar rate limits",
    )


class UpdatePricesResponse(BaseModel):
    dry_run: bool
    updated: bool
    gpu_count: int
    data_file: str
    changes: List[Dict[str, float]]


@api.get("/gpus")
def get_gpus() -> List[Dict[str, object]]:
    if not DATA_FILE.exists():
        raise HTTPException(status_code=500, detail="No existe data/gpus.json")
    return load_gpu_data(DATA_FILE)


@api.post("/update-prices", response_model=UpdatePricesResponse)
def update_prices_endpoint(payload: UpdatePricesRequest) -> UpdatePricesResponse:
    if not DATA_FILE.exists():
        raise HTTPException(status_code=500, detail="No existe data/gpus.json")

    gpus = load_gpu_data(DATA_FILE)
    previous_prices = {gpu.get("name"): gpu.get("priceArs") for gpu in gpus}

    updated = update_prices(
        gpus=gpus,
        max_results=payload.max_results,
        dry_run=payload.dry_run,
        sleep_seconds=payload.sleep_seconds,
        verbose=False,
    )

    changes = []
    for gpu in gpus:
        name = gpu.get("name")
        if not name:
            continue
        old_price = previous_prices.get(name)
        new_price = gpu.get("priceArs")
        if old_price != new_price:
            changes.append(
                {
                    "name": name,
                    "oldPriceArs": old_price,
                    "newPriceArs": new_price,
                }
            )

    if not payload.dry_run and updated:
        save_gpu_data(DATA_FILE, gpus)

    return UpdatePricesResponse(
        dry_run=payload.dry_run,
        updated=updated,
        gpu_count=len(gpus),
        data_file=str(DATA_FILE),
        changes=changes,
    )


@api.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


app.include_router(api)
