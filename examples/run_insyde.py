"""Run INSYDE with the default settings — the Python equivalent of
``r_reference/run_insyde_example.R``.

Computes the INSYDE depth-damage curve for the default (INSYDE reference)
building over a range of water depths, in both deterministic and probabilistic
(Monte-Carlo) modes, and prints a small summary table. No plotting dependency.
"""
import numpy as np

from pyinsyde import (
    ExposureVariables,
    HazardVariables,
    compute_damage,
    load_unit_prices,
    replacement_value_eur,
)


def main() -> None:
    exp = ExposureVariables()                 # INSYDE reference building
    up = load_unit_prices()                   # original EUR unit prices
    rv = replacement_value_eur(exp.BS, exp.BT)
    depths = np.arange(0.0, 3.0 + 1e-9, 0.5)

    # Deterministic: he may be passed as a vector.
    hz = HazardVariables(he=depths)
    det = compute_damage(exp, hz, up, rv, uncert=0)

    print(f"INSYDE reference building: BT={exp.BT} BS={exp.BS} "
          f"FA={exp.FA} NF={exp.NF}")
    print(f"Replacement value: EUR {rv:,.0f}/m2   "
          f"(total RVN = EUR {det.rvn:,.0f})\n")

    print(f"{'depth_m':>8} {'abs_EUR':>14} {'relative':>10} {'MC_mean_EUR':>14}")
    for i, h in enumerate(depths):
        # Probabilistic: hazard variables must be scalars; iterate over depth.
        hz_i = HazardVariables(he=float(h))
        rng = np.random.default_rng(0)
        mc = compute_damage(exp, hz_i, up, rv, uncert=1, nr_sim=2000, rng=rng)
        print(f"{h:8.2f} {det.abs_damage[i]:14,.0f} "
              f"{det.rel_damage[i]:10.3f} {mc.abs_damage.mean():14,.0f}")


if __name__ == "__main__":
    main()
