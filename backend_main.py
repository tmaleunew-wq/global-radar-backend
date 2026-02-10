"""
============================================================
Global Radar – FastAPI Backend
Spusti: uvicorn main:app --reload --port 8000
============================================================
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
from datetime import datetime

app = FastAPI(title="Global Radar API", version="1.0.0")

# ── CORS (Chrome extension potrebuje toto) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # V produkcii zmeň na extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("GLOBAL_RADAR_API_KEY", "gr_dev_key")

# ──────────────────────────────────────────────
# MODELY
# ──────────────────────────────────────────────

class ProductData(BaseModel):
    shop: str
    productId: Optional[str] = ""
    productUrl: str
    title: Optional[str] = ""
    price: Optional[str] = ""
    originalPrice: Optional[str] = ""
    shipping: Optional[str] = ""
    warehouse: Optional[str] = "CN"
    imageUrl: Optional[str] = ""
    specs: Optional[Dict[str, str]] = {}
    targetCountry: Optional[str] = None
    scannedAt: Optional[str] = None

class ImageMatchRequest(BaseModel):
    imageUrl: str
    sourceShop: str

# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────

def verify_key(x_api_key: str = Header(default="")):
    if x_api_key != API_KEY and API_KEY != "gr_dev_key":
        raise HTTPException(status_code=401, detail="Neplatný API kľúč")
    return x_api_key

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Global Radar API is running 🚀"}


@app.post("/api/products/scan")
async def scan_product(data: ProductData, _key=Depends(verify_key)):
    """
    Prijme naskenované dáta z Chrome extension.
    Tu môžeš pridať:
    - Uloženie do DB (PostgreSQL / Supabase)
    - AI generovanie popisku
    - Prekladanie do DE/PL/CZ
    """
    # Simulácia ceny dopravy pre krajinu
    shipping_prices = {
        "SK": estimate_shipping(data.price, "SK"),
        "CZ": estimate_shipping(data.price, "CZ"),
        "PL": estimate_shipping(data.price, "PL"),
        "DE": estimate_shipping(data.price, "DE"),
    }

    return {
        "success": True,
        "productId": data.productId,
        "receivedAt": datetime.utcnow().isoformat(),
        "shipping": shipping_prices.get(data.targetCountry, "N/A") if data.targetCountry else "N/A",
        "allShipping": shipping_prices,
        "specs": data.specs,
        "message": "Produkt zaznamenaný",
    }


@app.post("/api/products/publish")
async def publish_product(data: ProductData, _key=Depends(verify_key)):
    """
    Publikuje produkt na Global Radar.
    Tu integruj: Supabase / WordPress REST API / vlastnú DB.
    """
    # TODO: Uložiť do databázy
    # TODO: AI popis v 4 jazykoch
    # TODO: Trigger na web deploy

    product_id = f"gr_{data.shop}_{data.productId}_{int(datetime.utcnow().timestamp())}"

    return {
        "success": True,
        "id": product_id,
        "url": f"https://globalradar.eu/product/{product_id}",
        "publishedAt": datetime.utcnow().isoformat(),
        "message": f"Publikované v 4 jazykoch ✅",
    }


@app.post("/api/products/match-image")
async def match_image(request: ImageMatchRequest, _key=Depends(verify_key)):
    """
    Image matching cez Google Lens / vizuálny search.
    Integrácia: Google Cloud Vision API alebo SerpAPI Google Lens.
    """
    # TODO: Skutočné Google Lens API volanie
    # Príklad s SerpAPI:
    # async with httpx.AsyncClient() as client:
    #     r = await client.get("https://serpapi.com/search", params={
    #         "engine": "google_lens",
    #         "url": request.imageUrl,
    #         "api_key": os.getenv("SERPAPI_KEY"),
    #     })
    #     results = r.json()

    # Mock odpoveď pre vývoj:
    mock_matches = [
        {
            "shop": "temu" if request.sourceShop == "aliexpress" else "aliexpress",
            "title": "Podobný produkt (mock)",
            "price": "9.99",
            "imageUrl": request.imageUrl,  # V reáli by bola iná URL
            "url": "https://www.temu.com/example",
            "similarity": 0.92,
        }
    ]

    return {"success": True, "matches": mock_matches}


@app.get("/api/products/drafts")
async def get_drafts(_key=Depends(verify_key)):
    """Vráti drafty z backend DB (voliteľné)."""
    return {"drafts": []}


# ──────────────────────────────────────────────
# POMOCNÉ FUNKCIE
# ──────────────────────────────────────────────

def estimate_shipping(price_str: str, country: str) -> str:
    """Odhadne cenu dopravy podľa krajiny (zjednodušená verzia)."""
    base_rates = {"SK": 2.99, "CZ": 3.49, "PL": 3.29, "DE": 4.99}
    try:
        price = float(price_str or 0)
        if price > 30:
            return "FREE"
        return str(base_rates.get(country, 3.99))
    except:
        return "N/A"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
