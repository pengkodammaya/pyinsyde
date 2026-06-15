"""pyinsyde: a Python port of the INSYDE synthetic flood damage model.

Original R model: Dottori et al. (2016), *NHESS* 16, 2577-2591. This package is a
faithful, dependency-light port of the INSYDE component-based residential
flood-damage model and ships its original reference (EUR) cost data.
"""
from .variables import ExposureVariables, HazardVariables
from .model import compute_damage, DamageResult
from .prices import (
    load_unit_prices,
    replacement_value_eur,
    REPLACEMENT_VALUES_EUR,
)

__all__ = [
    "ExposureVariables",
    "HazardVariables",
    "compute_damage",
    "DamageResult",
    "load_unit_prices",
    "replacement_value_eur",
    "REPLACEMENT_VALUES_EUR",
]
