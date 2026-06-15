# AGENTS.md

Repo-level instructions for **Codex** (and other coding agents). Codex reads this
file automatically when working in this repository — both locally via the Codex
CLI and in the GitHub Actions workflows under `.github/workflows/codex-*.yml`.

## What this project is

`pyinsyde` is a faithful, dependency-light **Python port of the INSYDE** synthetic
flood depth-damage model (Dottori et al. 2016, *NHESS* 16, 2577–2591; original
model GPL-3.0). It reproduces the R `ComputeDamage` function component by
component, in deterministic and Monte-Carlo modes, and ships INSYDE's original
reference (EUR) cost data. The original R sources live in `r_reference/` and are
the source of truth for the port.

Runtime dependencies are **only numpy and scipy** — this is a deliberate
constraint. Do not add new hard dependencies (pandas, openpyxl, matplotlib, …)
to `[project].dependencies` without strong cause.

## Architecture

| File | Responsibility |
|------|----------------|
| `pyinsyde/variables.py` | `ExposureVariables` / `HazardVariables` dataclasses (mirror `exposure_variables.R` / `hazard_variables.R`). |
| `pyinsyde/model.py` | `compute_damage` — the INSYDE engine, ported from `insyde_function.R`, with Monte-Carlo uncertainty. |
| `pyinsyde/prices.py` | Loaders for the original INSYDE EUR unit prices and replacement values. |
| `pyinsyde/data/` | `unit_prices.txt`, `replacement_values.txt` — INSYDE reference data. |

## Conventions

- **Fidelity first.** If you change the damage math, it must still match
  `r_reference/`; explain any deviation and update `PORTING.md`. In particular,
  the C4 (dehumidification) and F6 (baseboard) components are computed but
  **excluded from totals** on purpose — do not "fix" this.
- Relative depth-damage curves must be monotone non-decreasing in depth; guard
  for it.
- Keep the public API small and the dependency set minimal.

## How to verify a change

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run ruff check .
uv run pytest -q
```

All of the above must pass before a change is considered done. CI runs Python
3.10–3.13.

## Review guidance (for the PR-review workflow)

Focus reviews on: correctness of the damage math and units, fidelity to the
INSYDE R reference, monotonicity/bounds of the relative curve, accidental new
hard dependencies, public-API breaks, and missing test coverage. Be concise and
only flag the changed lines.
