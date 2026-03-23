"""
algorithm.py — Greedy pallet-building logic.

HOW IT WORKS (plain English for the presentation):
──────────────────────────────────────────────────
1. Sort crates: heavy items first, then fragile items last, then by footprint
   (largest first).  This ensures stability — heavy/big stuff sits at the
   bottom, fragile stuff ends up near the top.

2. Work layer by layer.  Each layer is a 120 × 80 cm rectangle (standard EU
   pallet).  We scan the layer left-to-right, row-by-row, exactly like reading
   a page.

3. For each crate we try to fit it into the current position.  If it doesn't
   fit horizontally we jump to the next row.  If it doesn't fit in the current
   layer at all we open a new layer on top.

4. Output one human-readable instruction per crate so the worker never has to
   think — they just read the screen and place the box.

Limitations (intentional, this is a prototype):
- No rotation of crates.
- No bin-packing optimisation — we just fill row by row.
- Fragile flag is honoured by sorting, not by strict layer constraints.
"""

from models import (
    CrateType, Product, PlacementStep,
    CRATE_TYPES, PRODUCTS, Order, OrderItem,
)

# ── Pallet dimensions (cm) ────────────────────────────────────────────────────
PALLET_WIDTH  = 120   # X axis
PALLET_DEPTH  = 80    # Y axis
MAX_LAYERS    = 5     # safety ceiling

# ── Direction labels for the instruction text ─────────────────────────────────
def _x_label(x: float, width: float, pallet_w: float = PALLET_WIDTH) -> str:
    """Turn an X coordinate into a friendly left/center/right label."""
    center = x + width / 2
    third  = pallet_w / 3
    if center < third:
        return "left"
    elif center < 2 * third:
        return "center"
    return "right"

def _y_label(y: float, length: float, pallet_d: float = PALLET_DEPTH) -> str:
    """Turn a Y coordinate into a front/middle/back label."""
    center = y + length / 2
    third  = pallet_d / 3
    if center < third:
        return "front"
    elif center < 2 * third:
        return "middle"
    return "back"


def _sort_key(item: tuple[Product, CrateType]) -> tuple:
    """
    Sorting priority:
      1. Heavy items first  (heavy=True → lower sort value)
      2. Fragile items last (fragile=True → higher sort value)
      3. Larger footprint first (bigger area → lower sort value, so negate)
    """
    product, crate = item
    heavy_priority   = 0 if product.heavy   else 1
    fragile_priority = 1 if product.fragile else 0
    area             = -(crate.width * crate.length)   # negate → bigger first
    return (heavy_priority, fragile_priority, area)


def build_pallet(order: Order) -> list[PlacementStep]:
    """
    Main entry point.  Takes an Order, returns a list of PlacementStep objects.
    """
    # ── 1. Expand order into a flat list of (product, crate) pairs ────────────
    expanded: list[tuple[Product, CrateType]] = []
    for item in order.items:
        product   = PRODUCTS.get(item.product_id)
        if product is None:
            raise ValueError(f"Unknown product id: {item.product_id!r}")
        crate = CRATE_TYPES.get(product.crate_type_id)
        if crate is None:
            raise ValueError(f"Unknown crate type: {product.crate_type_id!r}")
        for _ in range(item.quantity):
            expanded.append((product, crate))

    # ── 2. Sort according to priority rules ───────────────────────────────────
    expanded.sort(key=_sort_key)

    # ── 3. Place crates greedily, layer by layer ──────────────────────────────
    steps:  list[PlacementStep] = []
    step_n: int = 1

    # Track the current state of the layer being filled
    layer:        int   = 1
    cursor_x:     float = 0.0   # current X position in this row
    cursor_y:     float = 0.0   # current Y position (front of current row)
    row_height:   float = 0.0   # deepest crate length seen in this row
    layer_height: float = 0.0   # tallest crate seen in this layer (for stacking)
    layer_heights: dict[int, float] = {}  # accumulated height per layer

    for product, crate in expanded:
        w, l, h = crate.width, crate.length, crate.height

        # Sanity-check: crate must fit on the pallet at all
        if w > PALLET_WIDTH or l > PALLET_DEPTH:
            raise ValueError(
                f"Crate {crate.id!r} ({w}×{l} cm) does not fit on a "
                f"{PALLET_WIDTH}×{PALLET_DEPTH} cm pallet."
            )

        placed = False
        while not placed:
            # ── Try to fit in current column position ──────────────────────
            if cursor_x + w <= PALLET_WIDTH:
                # Fits horizontally — place it here
                x = cursor_x
                y = cursor_y
                cursor_x  += w                        # advance X cursor
                row_height = max(row_height, l)       # track deepest crate in row
                layer_height = max(layer_height, h)   # track tallest crate in layer
                placed = True

            else:
                # ── Row is full — try the next row ─────────────────────────
                cursor_y += row_height   # move Y to next row
                cursor_x  = 0.0
                row_height = 0.0

                if cursor_y + l > PALLET_DEPTH:
                    # ── Layer is full — open a new layer ───────────────────
                    layer_heights[layer] = layer_height
                    layer       += 1
                    if layer > MAX_LAYERS:
                        raise ValueError("Order too large: exceeded maximum layer count.")
                    cursor_x     = 0.0
                    cursor_y     = 0.0
                    row_height   = 0.0
                    layer_height = 0.0

        # ── Build the human-readable instruction ──────────────────────────────
        x_lbl = _x_label(x, w)
        y_lbl = _y_label(y, l)
        z_offset = sum(layer_heights.get(lyr, 0) for lyr in range(1, layer))
        instruction = (
            f"Place {product.name} ({crate.name}) at the {x_lbl}-{y_lbl} "
            f"of Layer {layer}  ·  position ({x:.0f}, {y:.0f}) cm"
        )

        steps.append(PlacementStep(
            step         = step_n,
            product_id   = product.id,
            product_name = product.name,
            crate_type   = crate.name,
            layer        = layer,
            x            = x,
            y            = y,
            width        = w,
            length       = l,
            height       = h,
            color        = product.color,
            instruction  = instruction,
        ))
        step_n += 1

    return steps
