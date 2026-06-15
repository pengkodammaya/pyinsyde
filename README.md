# pyinsyde — a Python port of the INSYDE flood-damage model

[![CI](https://github.com/pengkodammaya/pyinsyde/actions/workflows/ci.yml/badge.svg)](https://github.com/pengkodammaya/pyinsyde/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue.svg)](pyproject.toml)

`pyinsyde` is a faithful, dependency-light Python port of **INSYDE**, the
synthetic (component-based) flood depth-damage model for residential buildings of
Dottori et al. (2016, *NHESS* 16, 2577–2591). It reproduces the original R model
(`ComputeDamage`) component by component — in both deterministic and Monte-Carlo
modes — and ships the model's original reference (EUR) cost data.

The only runtime dependencies are **numpy** and **scipy**.

> Port of the reference R implementation by Dottori, Figueiredo, Martina,
> Molinari and Scorzini (GPL-3.0). See [`PORTING.md`](PORTING.md) for fidelity
> notes and the known R quirks that are reproduced on purpose.

---

## What INSYDE does

INSYDE estimates flood damage to a residential building by summing **physical
damage to individual components** (structure, finishes, windows/doors, systems,
clean-up/dehumidification, …) as a function of the flood **hazard** (water depth,
velocity, duration, sediment load, water quality) and the building's **exposure**
(geometry, materials, finishing level). Damage is returned in absolute terms and
as a relative damage ratio (0→1) against the building's replacement value, and
can be produced as an expected value or as a Monte-Carlo distribution.

---

## Install

```bash
pip install -e .            # or: uv pip install -e .
```

For development (tests + linter):

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run pytest -q
```

## Quick start

```python
import numpy as np
from pyinsyde import (ExposureVariables, HazardVariables,
                      compute_damage, load_unit_prices, replacement_value_eur)

exp = ExposureVariables()                 # INSYDE reference building
up = load_unit_prices()                   # original EUR unit prices
rv = replacement_value_eur(exp.BS, exp.BT)

hz = HazardVariables(he=np.arange(0.0, 3.0 + 1e-9, 0.5))   # depth vector
res = compute_damage(exp, hz, up, rv, uncert=0)            # deterministic
print(res.rel_damage)     # relative damage ratio at each depth
```

A complete runnable script — the Python equivalent of the R example — is in
[`examples/run_insyde.py`](examples/run_insyde.py):

```bash
uv run python examples/run_insyde.py
```

---

## Regional localization (bring your own prices)

INSYDE's damage logic is region-agnostic; only the **cost inputs** are local. The
model ships with its original Italian (EUR) reference data, but you can run it for
any country without modifying the package:

```python
from pyinsyde import compute_damage, load_unit_prices, ExposureVariables, HazardVariables

up = load_unit_prices(path="prices/my_region.txt")   # your unit-price table
rv = 2000.0                                           # your replacement value (per m²)
res = compute_damage(ExposureVariables(), HazardVariables(), up, rv, uncert=0)
```

Your price table uses the same `name  value  #unit` format as
[`pyinsyde/data/unit_prices.txt`](pyinsyde/data/unit_prices.txt). Supply your
region's replacement value directly to `compute_damage`.

> **Only commit openly-licensed data.** Keep commercial cost tables out of the
> repository and load them at runtime via `path=`. Contributions of
> **open** regional datasets are very welcome — see the roadmap
> ([multi-region support](https://github.com/pengkodammaya/pyinsyde/issues/3)).

---

## Repository layout

```
pyinsyde/
  variables.py   ExposureVariables / HazardVariables  (mirror INSYDE inputs)
  model.py       compute_damage — faithful port of insyde_function.R
  prices.py      unit-price + replacement-value loaders (original EUR data)
  data/          unit_prices.txt, replacement_values.txt  (INSYDE EUR reference)
examples/
  run_insyde.py  the R INSYDE example, in Python (deterministic + Monte-Carlo)
tests/           model validation tests
r_reference/     the original INSYDE R sources, for line-by-line comparison
PORTING.md       fidelity notes and reproduced R quirks
DATA.md          provenance of the bundled reference data
```

---

## License / attribution

Ported from INSYDE (Dottori, Figueiredo, Martina, Molinari, Scorzini), released
under the **GNU GPL-3.0**. This port is likewise GPL-3.0 — see [`LICENSE`](LICENSE).
The bundled `unit_prices.txt` / `replacement_values.txt` are the model's original
reference data; see [`DATA.md`](DATA.md).
