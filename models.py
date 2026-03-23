"""
models.py — Data structures for the pallet building assistant.
Keeps everything simple: crate sizes, product definitions, and order format.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Crate types ──────────────────────────────────────────────────────────────

@dataclass
class CrateType:
    """Physical dimensions of a crate in centimetres."""
    id: str
    name: str
    width: float   # cm (along pallet width  = X axis)
    length: float  # cm (along pallet depth  = Y axis)
    height: float  # cm (stacking height)


# All crate types available in the warehouse
CRATE_TYPES: dict[str, CrateType] = {
    "large":  CrateType("large",  "Large Crate",  60, 40, 30),
    "medium": CrateType("medium", "Medium Crate", 40, 30, 25),
    "small":  CrateType("small",  "Small Crate",  30, 20, 20),
    "flat":   CrateType("flat",   "Flat Crate",   60, 40, 15),
}


# ── Products ─────────────────────────────────────────────────────────────────

@dataclass
class Product:
    """A warehouse product mapped to a crate type, with optional handling flags."""
    id: str
    name: str
    crate_type_id: str            # references a key in CRATE_TYPES
    fragile: bool = False         # fragile → goes on upper layers
    heavy: bool = False           # heavy   → goes on lower layers (packed first)
    color: str = "#888888"        # hex color for the UI visualisation


# Product catalogue
PRODUCTS: dict[str, Product] = {
    "bananas":     Product("bananas",     "Bananas",      "large",  fragile=False, heavy=True,  color="#F5C518"),
    "tomatoes":    Product("tomatoes",    "Tomatoes",     "medium", fragile=True,  heavy=False, color="#E53935"),
    "grapes":      Product("grapes",      "Grapes",       "small",  fragile=True,  heavy=False, color="#8E24AA"),
    "potatoes":    Product("potatoes",    "Potatoes",     "large",  fragile=False, heavy=True,  color="#795548"),
    "oranges":     Product("oranges",     "Oranges",      "medium", fragile=False, heavy=False, color="#FB8C00"),
    "strawberries":Product("strawberries","Strawberries", "small",  fragile=True,  heavy=False, color="#E91E63"),
    "watermelons": Product("watermelons", "Watermelons",  "large",  fragile=False, heavy=True,  color="#388E3C"),
    "lettuce":     Product("lettuce",     "Lettuce",      "flat",   fragile=True,  heavy=False, color="#66BB6A"),
}


# ── Order ─────────────────────────────────────────────────────────────────────

@dataclass
class OrderItem:
    """One line of an order: a product and how many crates of it are needed."""
    product_id: str
    quantity: int


@dataclass
class Order:
    """A full picking order sent to the API."""
    items: list[OrderItem]


# ── Step (output) ─────────────────────────────────────────────────────────────

@dataclass
class PlacementStep:
    """One instruction given to the worker."""
    step: int
    product_id: str
    product_name: str
    crate_type: str
    layer: int          # 1-indexed
    x: float            # cm from left edge of pallet
    y: float            # cm from front edge of pallet
    width: float        # crate footprint width
    length: float       # crate footprint length
    height: float       # crate height
    color: str
    instruction: str    # human-readable sentence shown on the scanner
