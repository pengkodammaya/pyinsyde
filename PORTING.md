# Porting notes

`pyinsyde` is a line-by-line port of the INSYDE R model. The R sources it was
ported from are kept in [`r_reference/`](r_reference/) so the port can be audited
against the original.

| R source | Python |
|---|---|
| `insyde_function.R` (`ComputeDamage`) | `pyinsyde/model.py` (`compute_damage`) |
| `exposure_variables.R` | `pyinsyde/variables.py` (`ExposureVariables`) |
| `hazard_variables.R` | `pyinsyde/variables.py` (`HazardVariables`) |
| `unit_prices.txt`, `replacement_values.txt` | `pyinsyde/data/*` + `pyinsyde/prices.py` |
| `run_insyde_example.R` | `examples/run_insyde.py` |

## Fidelity

- `compute_damage` reproduces R `ComputeDamage` **component by component**.
- **Reproduced quirk:** the original R computes components **C4**
  (dehumidification) and **F6** (baseboard replacement) but **excludes them from
  the reported totals**. The port reproduces this exactly so the numbers match;
  both components are still available in `DamageResult.component_damage`.
- Both the deterministic mode (`uncert=0`) and the probabilistic Monte-Carlo mode
  (`uncert=1`, `nr_sim`) are supported. As in the R model, deterministic mode
  accepts one hazard variable as a vector; probabilistic mode requires scalar
  hazard inputs. The Monte-Carlo mean matches the deterministic value (tested to
  within 5%).
- Truncated-normal fragility terms use `scipy.stats.truncnorm` with standardized
  bounds, matching R's `truncnorm::ptruncnorm`.

## Validation

`tests/test_model.py` combines independent re-derivation of selected components
from the paper's formulas, the structural invariants the R model guarantees, the
C4/F6 exclusion quirk, and a deterministic-vs-Monte-Carlo consistency check.
Run with `uv run pytest -q`.
