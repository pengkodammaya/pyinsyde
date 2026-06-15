"""Loaders for the original INSYDE unit prices and replacement values.

These provide the Italian (EUR) reference data shipped with the INSYDE R model
(``unit_prices.txt`` and ``replacement_values.txt`` in ``r_reference/``). Pass a
``path`` to ``load_unit_prices`` to supply your own region's unit prices.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

DATA_DIR = Path(__file__).resolve().parent / "data"

# Replacement value lookup, EUR/m2, indexed [BS][BT] exactly as in
# replacement_values.txt:  rows = structure (RC, M, W), cols = type
# (Detached, Semi-detached, Apartment).
REPLACEMENT_VALUES_EUR = {
    1: {1: 1580.0, 2: 1432.0, 3: 1288.0},  # RC
    2: {1: 1131.0, 2: 1027.0, 3: 1288.0},  # Masonry
    3: {1: 1131.0, 2: 1027.0, 3: 1288.0},  # Wood
}


def load_unit_prices(path: Optional[Path] = None) -> Dict[str, float]:
    """Parse unit_prices.txt into a {component: price} dict.

    The file has ``name  value  #unit`` lines plus comment/section lines.
    """
    path = Path(path) if path else DATA_DIR / "unit_prices.txt"
    prices: Dict[str, float] = {}
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()  # drop inline comments
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue  # header tokens like "UnitPrice"
        name, value = parts[0], parts[1]
        try:
            prices[name] = float(value)
        except ValueError:
            continue
    return prices


def replacement_value_eur(BS: int, BT: int) -> float:
    """INSYDE reference replacement value (EUR/m2) for a structure/type pair."""
    return REPLACEMENT_VALUES_EUR[BS][BT]
