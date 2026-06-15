"""Exposure and hazard variable containers for INSYDE.

These mirror ``exposure_variables.R`` and ``hazard_variables.R`` from the
original R implementation. Defaults reproduce the R example exactly so the
Python port can be checked against it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ExposureVariables:
    """Building exposure parameters (see exposure_variables.R)."""

    # Geometry
    FA: float = 100.0          # Footprint area (m2)
    IA: Optional[float] = None  # Internal area (m2); default 0.9 * FA
    BA: Optional[float] = None  # Basement area (m2); default 0.5 * FA
    EP: float = 40.0           # External perimeter (m)
    IH: float = 3.5            # Inter-storey height (m)
    BH: float = 3.2            # Basement height (m)
    GL: float = 0.1            # Ground-floor level / elevation above grade (m)
    NF: int = 2                # Number of floors (storeys)

    # Typology / quality
    BT: int = 1    # Building type: 1 Detached, 2 Semi-detached, 3 Apartment
    BS: int = 2    # Structure: 1 Reinforced concrete, 2 Masonry, 3 Wood
    PD: int = 1    # Plant distribution: 1 Centralized, 2 Distributed
    PT: int = 1    # Heating type: 1 Radiator, 2 Underfloor heating
    FL: float = 1.2  # Finishing level: High 1.2, Medium 1.0, Low 0.8
    YY: int = 1994   # Year of construction
    LM: float = 1.1  # Maintenance level: High 1.1, Medium 1.0, Low 0.9

    def __post_init__(self) -> None:
        if self.IA is None:
            self.IA = 0.9 * self.FA
        if self.BA is None:
            self.BA = 0.5 * self.FA


@dataclass
class HazardVariables:
    """Flood hazard parameters (see hazard_variables.R).

    ``he`` may be a scalar or a 1-D array of water depths; in the original
    model exactly one hazard variable may be passed as a vector.
    """

    he: np.ndarray = None  # Water depth at ground level (m)
    v: float = 0.5         # Flow velocity (m/s)
    s: float = 0.05        # Sediment concentration (-)
    d: float = 24.0        # Flood duration (h)
    q: int = 1             # Pollutant presence: 1 yes, 0 no

    def __post_init__(self) -> None:
        if self.he is None:
            self.he = np.arange(0.0, 5.0 + 1e-9, 0.01)
        self.he = np.asarray(self.he, dtype=float)
