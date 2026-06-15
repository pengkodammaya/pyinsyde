# Bundled data provenance

`pyinsyde` ships only the **original INSYDE reference data** — the small,
machine-read text tables released with the INSYDE R model. There is no other
external data in this repository.

| File | What it is | Used by |
|---|---|---|
| `pyinsyde/data/unit_prices.txt` | INSYDE reference unit prices (EUR) per damage component | `prices.load_unit_prices` |
| `pyinsyde/data/replacement_values.txt` | INSYDE reference replacement values (EUR/m²), indexed by structure type (BS) and building type (BT) | `prices.replacement_value_eur` |
| `r_reference/*` | The original INSYDE R sources (`insyde_function.R`, `exposure_variables.R`, `hazard_variables.R`, `run_insyde_example.R`) plus the same two data tables, kept for line-by-line comparison | reference only |
| `Paper/` | Placeholder for the INSYDE paper (Dottori et al., 2016, *NHESS* 16, 2577–2591) — the model this package ports | reference only; PDF git-ignored |

## Using your own prices

The model is region-agnostic. To cost a building in another currency or market,
pass your own price table to `load_unit_prices(path=...)` (same
`name  value  #unit` line format) and your own replacement value to
`compute_damage`. The bundled EUR tables are only the reference defaults.
