"""
main.py — FastAPI backend for the Pallet Building Assistant.

Endpoints:
  GET  /crate-types   → return all available crate definitions
  GET  /products      → return all available products
  POST /build-pallet  → accept an order, return placement steps
  GET  /              → serve the frontend HTML
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from models import CRATE_TYPES, PRODUCTS, Order, OrderItem
from algorithm import build_pallet

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Pallet Building Assistant",
    description="Greedy pallet layout engine for warehouse picking",
    version="1.0.0",
)

# Allow the HTML frontend (served from file://) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic request/response schemas ─────────────────────────────────────────

class OrderItemRequest(BaseModel):
    product_id: str
    quantity:   int

class OrderRequest(BaseModel):
    items: list[OrderItemRequest]

class StepResponse(BaseModel):
    step:         int
    product_id:   str
    product_name: str
    crate_type:   str
    layer:        int
    x:            float
    y:            float
    width:        float
    length:       float
    height:       float
    color:        str
    instruction:  str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    """Serve the single-page frontend."""
    return FileResponse("index.html")


@app.get("/crate-types")
def get_crate_types():
    """Return all crate type definitions."""
    return [
        {
            "id":     c.id,
            "name":   c.name,
            "width":  c.width,
            "length": c.length,
            "height": c.height,
        }
        for c in CRATE_TYPES.values()
    ]


@app.get("/products")
def get_products():
    """Return all product definitions."""
    return [
        {
            "id":           p.id,
            "name":         p.name,
            "crate_type_id":p.crate_type_id,
            "fragile":      p.fragile,
            "heavy":        p.heavy,
            "color":        p.color,
        }
        for p in PRODUCTS.values()
    ]


@app.post("/build-pallet", response_model=list[StepResponse])
def api_build_pallet(order_req: OrderRequest):
    """
    Accept an order and return step-by-step pallet placement instructions.

    Example request body:
    {
      "items": [
        {"product_id": "bananas",  "quantity": 2},
        {"product_id": "tomatoes", "quantity": 3},
        {"product_id": "grapes",   "quantity": 1}
      ]
    }
    """
    # Convert request model → internal Order dataclass
    order = Order(
        items=[OrderItem(product_id=i.product_id, quantity=i.quantity)
               for i in order_req.items]
    )

    try:
        steps = build_pallet(order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Convert PlacementStep dataclasses → dicts for Pydantic
    return [vars(s) for s in steps]


# ── Dev entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
