# 🏭 PalletOS — Warehouse Pallet Building Assistant

A demo prototype that computes step-by-step pallet stacking instructions for warehouse workers, eliminating mental load on the picking floor.

---

## How to Run

### 1. Install dependencies
```bash
cd pallet-builder
pip install -r requirements.txt
```

### 2. Start the backend
```bash
python main.py
```
The API is now live at **http://localhost:8000**

### 3. Open the frontend
Open `index.html` in your browser, **or** navigate to:
```
http://localhost:8000
```
(FastAPI serves the HTML directly.)

### 4. Use it
- Adjust quantities in the Order panel on the left
- Click **▶ Build Pallet**
- Switch between layers using the L1 / L2 / ... tabs
- Click any step or canvas box to cross-highlight

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves the frontend |
| GET | `/crate-types` | All available crate definitions |
| GET | `/products` | All product definitions |
| POST | `/build-pallet` | Build a pallet from an order |

### Example request (`POST /build-pallet`)
```json
{
  "items": [
    { "product_id": "bananas",  "quantity": 2 },
    { "product_id": "tomatoes", "quantity": 3 },
    { "product_id": "grapes",   "quantity": 1 }
  ]
}
```

### Example response (one step shown)
```json
[
  {
    "step": 1,
    "product_id": "bananas",
    "product_name": "Bananas",
    "crate_type": "Large Crate",
    "layer": 1,
    "x": 0.0,
    "y": 0.0,
    "width": 60.0,
    "length": 40.0,
    "height": 30.0,
    "color": "#F5C518",
    "instruction": "Place Bananas (Large Crate) at the left-front of Layer 1  ·  position (0, 0) cm"
  }
]
```

---

## Project Structure

```
pallet-builder/
├── main.py          # FastAPI app — routes and server setup
├── algorithm.py     # Greedy pallet-building logic
├── models.py        # Data structures, product/crate catalogue
├── index.html       # Single-file frontend (no build step needed)
└── requirements.txt
```

---

## Algorithm Explained (for your presentation)

The algorithm works in three stages:

**Stage 1 — Sort by priority**
Before placing anything, we sort the crates:
- Heavy items first → go to the bottom for stability
- Fragile items last → end up higher where there's less weight
- Within the same priority, larger footprints go first → fills space efficiently

**Stage 2 — Fill row by row**
Think of each layer as a 120 × 80 cm grid.
We scan left-to-right, just like reading a sentence.
When a row is full (no more horizontal space), we start a new row behind it.
When the entire layer is full, we add a new layer on top and start over.

**Stage 3 — Generate instructions**
For each placed crate we convert the (x, y) coordinates into human-readable language:
- x position → "left / center / right"
- y position → "front / middle / back"
- Layer number → "Layer 1", "Layer 2", etc.

This gives workers clear, unambiguous instructions with zero mental arithmetic.

**What it deliberately does NOT do:**
- No rotation of crates (keeps it simple)
- No bin-packing optimisation (no OR-tools, no SAT solver)
- No backtracking (greedy = one pass only)

For a warehouse demo prototype, this is exactly the right level of complexity.

---

## Crate Types

| ID | Name | W × D × H (cm) |
|----|------|----------------|
| large | Large Crate | 60 × 40 × 30 |
| medium | Medium Crate | 40 × 30 × 25 |
| small | Small Crate | 30 × 20 × 20 |
| flat | Flat Crate | 60 × 40 × 15 |

## Products

| Product | Crate | Heavy | Fragile |
|---------|-------|-------|---------|
| Bananas | Large | ✓ | |
| Tomatoes | Medium | | ✓ |
| Grapes | Small | | ✓ |
| Potatoes | Large | ✓ | |
| Oranges | Medium | | |
| Strawberries | Small | | ✓ |
| Watermelons | Large | ✓ | |
| Lettuce | Flat | | ✓ |
