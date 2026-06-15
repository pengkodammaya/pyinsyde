"""INSYDE damage model, ported from insyde_function.R.

``compute_damage`` reproduces the R ``ComputeDamage`` function component for
component. Water depth ``he`` may be a vector in deterministic mode; in
probabilistic mode all hazard variables must be scalars and ``nr_sim`` draws
are returned.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from typing import Dict, Optional

import numpy as np
from scipy.stats import norm, truncnorm

from .variables import ExposureVariables, HazardVariables


def _ptruncnorm(x, a, b, mean, sd):
    """R truncnorm::ptruncnorm -> scipy truncnorm.cdf with standardized bounds."""
    return truncnorm.cdf(x, (a - mean) / sd, (b - mean) / sd, loc=mean, scale=sd)


def pmax(*args):
    """Element-wise (parallel) maximum, broadcasting like R's pmax."""
    return reduce(np.maximum, [np.asarray(a, dtype=float) for a in args])


def pmin(*args):
    return reduce(np.minimum, [np.asarray(a, dtype=float) for a in args])


@dataclass
class DamageResult:
    abs_damage: np.ndarray            # absolute damage (currency)
    rel_damage: np.ndarray            # damage / replacement value new
    group_damage: Dict[str, np.ndarray]      # 6 component groups
    component_damage: Dict[str, np.ndarray]  # 31 individual components
    rvn: float                        # replacement value new


def compute_damage(
    exposure: ExposureVariables,
    hazard: HazardVariables,
    unit_prices: Dict[str, float],
    repval: float,
    uncert: int = 0,
    nr_sim: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
) -> DamageResult:
    e, hz, up = exposure, hazard, unit_prices

    # IA, BA and he carry None as a documented sentinel and are filled by the
    # dataclass __post_init__, so they are concrete here. Assert it for the type
    # checker (and as a guard against a hand-constructed instance that skipped it).
    assert e.IA is not None and e.BA is not None and hz.he is not None

    # Unpack for readability (matches R variable names)
    FA, IA, BA, EP, IH, BH, GL, NF = e.FA, e.IA, e.BA, e.EP, e.IH, e.BH, e.GL, e.NF
    BT, BS, PD, PT, FL, YY, LM = e.BT, e.BS, e.PD, e.PT, e.FL, e.YY, e.LM
    v, s, d, q = hz.v, hz.s, hz.d, hz.q

    # Water depth at ground level (capped at the building height)
    he = np.minimum(np.asarray(hz.he, dtype=float), NF * IH * 1.05)
    h = np.round(he - GL, 3)
    h = (h > 0) * h

    # Derived geometry
    IP = 2.5 * EP        # internal perimeter (m)
    BP = 4 * np.sqrt(BA)  # basement perimeter (m)
    BL = GL - 0.3 - BH   # basement level (m)

    # Replacement values
    RVN = repval * FA * NF
    age = 2015 - YY
    decay = min(0.01 * age / LM, 0.3)
    RVU = RVN * (1 - decay)  # noqa: F841 (kept for parity; not used downstream)

    # Fragility functions (probabilities of damage)
    frag1 = np.round(_ptruncnorm(d, 12, 36, 24, 24 / 6), 3)
    frag2_1f = np.round(_ptruncnorm(h, 0.2, 0.6, 0.4, .4 / 6), 3)
    frag2_2f = np.round(_ptruncnorm(h, 0.2 + IH, 0.6 + IH, 0.4 + IH, .4 / 6), 3)
    frag3_1f = np.round(_ptruncnorm(h, 1.5, 2.0, 1.75, .5 / 6), 3)
    frag3_2f = np.round(_ptruncnorm(h, 1.5 + IH, 2.0 + IH, 1.75 + IH, .5 / 6), 3)
    frag4 = np.round(_ptruncnorm(v, 1, 1.5, 1.25, .5 / 6), 3)
    frag5_1f = np.round(_ptruncnorm(h, 0.4, 0.8, 0.6, .4 / 6), 3)
    frag5_2f = np.round(_ptruncnorm(h, 0.4 + IH, 0.8 + IH, 0.6 + IH, .4 / 6), 3)
    frag6_1f = np.round(_ptruncnorm(h, 1.2, 1.8, 1.5, .5 / 6), 3)
    frag6_2f = np.round(_ptruncnorm(h, 1.2 + IH, 1.8 + IH, 1.5 + IH, .5 / 6), 3)
    frag7 = np.round(_ptruncnorm(v, 0.8, 1, 0.9, .2 / 6), 3)
    frag8 = np.round(norm.cdf(he * v, loc=5, scale=4 / 6), 3) * (v >= 2)

    # Damage ratios (deterministic = expected value; uncertain = Bernoulli draws)
    if uncert == 0:
        dr1 = frag1
        dr2 = frag2_1f + frag2_2f
        dr3 = frag3_1f + frag3_2f
        dr4 = frag4
        dr5 = frag5_1f + frag5_2f
        dr6 = frag6_1f + frag6_2f
        dr7 = frag7
        dr8 = frag8
    else:
        if nr_sim is None:
            raise ValueError("nr_sim is required when uncert != 0")
        if np.size(he) > 1:
            # Same contract as the R original: in probabilistic mode all hazard
            # variables must be scalars (iterate over depths externally, as in
            # run_insyde_example.R). Without this check the bern() draws fail
            # with a cryptic numpy broadcast error.
            raise ValueError(
                f"In probabilistic mode (uncert=1) the water depth 'he' must be "
                f"a scalar; got a vector of length {np.size(he)}. Loop over "
                f"depths and call compute_damage once per value."
            )
        rng = rng or np.random.default_rng()

        def bern(p):
            return (rng.random(nr_sim) < p).astype(float)

        dr1 = bern(frag1)
        dr2 = bern(frag2_1f) + bern(frag2_2f)
        dr3 = bern(frag3_1f) + bern(frag3_2f)
        dr4 = bern(frag4)
        dr5 = bern(frag5_1f) + bern(frag5_2f)
        dr6 = bern(frag6_1f) + bern(frag6_2f)
        dr7 = bern(frag7)
        dr8 = bern(frag8)

    nf = NF  # np.minimum(NF, ...) broadcasts like R's rep(NF, ...)
    eco = 1 - 0.2 * (BT == 3)  # economies of scale for apartment blocks

    # 1. Cleanup ----------------------------------------------------------
    C1 = up["pumping"] * (he >= 0) * (
        IA * max(-GL, 0) + BA * (-BL - min(0.3, (GL > 0 and GL < 0.3) * (0.3 - GL)))
    ) * eco
    C2 = up["disposal"] * s * (1 + (q == 1) * 0.4) * (IA * h + BA * BH) * eco
    C3 = up["cleaning"] * (1 + (q == 1) * 0.4) * (
        IA * pmin(nf, np.ceil(h / IH)) + IP * h + BA + BP * BH
    ) * eco
    C4 = up["dehumidification"] * dr1 * (
        IA * IH * pmin(nf, np.ceil(h / IH)) * (he > 0) + BA * BH
    ) * eco

    # 2. Removal ----------------------------------------------------------
    R1 = up["screedremoval"] * IA * ((FL > 1) * dr1 * pmin(nf, dr2)) * eco
    R2 = up["parquetremoval"] * (FL > 1) * dr1 * pmin(nf, dr2) * IA * eco
    R3 = up["baseboardremoval"] * dr1 * pmin(nf, np.ceil((h - 0.05) / IH)) * IP * eco
    R4 = up["partitionsremoval"] * dr1 * (1 + (BS == 1) * 0.20) * 0.5 * IP * IH * pmin(nf, dr3) * eco
    R5 = up["plasterboardremoval"] * IA * 0.2 * pmin(nf, np.ceil((h - (IH - .5)) / IH)) * (FL > 1) * eco
    R6 = up["extplasterremoval"] * pmax(q == 1, LM <= 1, dr1, dr4) * EP * (he + 1.0) * eco
    R7 = up["intplasterremoval"] * pmax(q == 1, LM <= 1, dr1) * (IP * (h + 1.0) + BP * BH) * eco
    R8 = up["doorsremoval"] * pmax(dr4, dr1) * (pmin(nf, dr5) * 0.12 * IA + 0.03 * BA) * eco
    R9 = up["windowsremoval"] * pmax(dr7, dr1) * pmin(nf, dr6) * 0.12 * IA * eco
    R10 = up["boilerremoval"] * IA * (
        (PD == 1) * ((BA > 0) + (BA == 0) * (h > 1.6))
        + (PD == 2) * pmin(nf, np.ceil((h - 1.6) / IH))
    ) * eco

    # 3. Non-structural ---------------------------------------------------
    N1 = up["partitionsreplace"] * dr1 * (1 + (BS == 1) * 0.20) * 0.5 * IP * IH * pmin(nf, dr3) * eco
    N2 = up["screedreplace"] * IA * ((FL > 1) * dr1 * pmin(nf, dr2)) * eco
    N3 = up["plasterboardreplace"] * IA * 0.2 * pmin(nf, np.ceil((h - (IH - .5)) / IH)) * (FL > 1) * eco

    # 4. Structural -------------------------------------------------------
    S1 = up["soilconsolidation"] * dr8 * FA * NF * IH * (0.01 + (BS == 1) * 0.01) * eco
    S2 = up["localrepair"] * (BS == 2) * dr8 * EP * 0.5 * he * (1 + s) * eco
    S3 = up["pillarretrofitting"] * (BS == 1) * dr8 * 0.15 * EP * he * eco

    # 5. Finishing --------------------------------------------------------
    F1 = up["extplasterreplace"] * FL * pmax(q == 1, LM <= 1, dr1, dr4) * EP * (he + 1.0) * eco
    F2 = up["intplasterreplace"] * FL * pmax(q == 1, LM <= 1, dr1) * (IP * (h + 1.0) + BP * BH) * eco
    F3 = up["extpainting"] * pmin(nf, np.ceil(he / IH)) * IH * EP * FL * eco
    F4 = up["intpainting"] * (pmin(nf, np.ceil(h / IH)) * IH * IP + BP * BH * (FL > 1 and BT == 1)) * FL * eco
    F5 = up["parquetreplace"] * (FL > 1) * dr1 * pmin(nf, dr2) * IA * eco
    F6 = up["baseboardreplace"] * dr1 * pmin(nf, np.ceil((h - 0.05) / IH)) * IP * eco

    # 6. Windows and doors ------------------------------------------------
    W1 = up["doorsreplace"] * pmax(dr4, dr1) * (pmin(nf, dr5) * 0.12 * IA + 0.03 * BA) * (1 + (FL > 1)) * eco
    W2 = up["windowsreplace"] * pmax(dr7, dr1) * pmin(nf, dr6) * 0.12 * IA * (1 + (FL > 1)) * eco

    # 7. Building systems -------------------------------------------------
    P1 = up["boilerreplace"] * IA * (
        (PD == 1) * ((BA > 0) + (BA == 0) * (h > 1.6))
        + (PD == 2) * pmin(nf, np.ceil((h - 1.6) / IH))
    ) * (1 + 0.25 * np.logical_xor(BT == 1, BT == 2))
    P2 = up["radiatorpaint"] * (PT == 1) * pmin(nf, np.ceil((h - 0.2) / IH)) * IA / 20 * eco
    P3 = up["underfloorheatingreplace"] * IA * (PT == 2) * ((FL > 1) * dr1 * pmin(nf, dr2)) * eco
    P4 = up["electricalsystreplace"] * IA * (
        pmin(nf, np.ceil((h - 0.2) / IH)) * 0.4
        + pmin(nf, np.ceil((h - 1.1) / IH)) * 0.3
        + pmin(nf, np.ceil((h - 1.5) / IH)) * 0.3
    ) * (1 + (FL > 1)) * eco
    P5 = up["plumbingsystreplace"] * IA * ((s > 0.10) | (q == 1)) * (
        pmin(nf, np.ceil((h - 0.15) / IH)) * 0.1
        + pmin(nf, np.ceil((h - 0.4) / IH)) * 0.2
        + pmin(nf, np.ceil((h - 0.9) / IH)) * 0.2
    ) * (1 + (FL > 1)) * eco

    components = {
        "C1": C1, "C2": C2, "C3": C3, "C4": C4,
        "R1": R1, "R2": R2, "R3": R3, "R4": R4, "R5": R5,
        "R6": R6, "R7": R7, "R8": R8, "R9": R9, "R10": R10,
        "N1": N1, "N2": N2, "N3": N3,
        "S1": S1, "S2": S2, "S3": S3,
        "F1": F1, "F2": F2, "F3": F3, "F4": F4, "F5": F5, "F6": F6,
        "W1": W1, "W2": W2,
        "P1": P1, "P2": P2, "P3": P3, "P4": P4, "P5": P5,
    }
    # Broadcast every component to a common shape (depth vector in
    # deterministic mode, or nr_sim draws in probabilistic mode).
    shape = np.broadcast_shapes(
        *(np.shape(val) for val in components.values()), np.shape(he)
    )
    components = {k: np.broadcast_to(np.asarray(val, dtype=float), shape).copy()
                 for k, val in components.items()}

    # NOTE: matching insyde_function.R exactly -- the original computes C4
    # (dehumidification) and F6 (baseboard replacement) but does NOT include
    # them in the group totals or absDamage. They remain available in
    # ``component_damage`` for inspection but are excluded from the sums here
    # to reproduce the reference outputs bit-for-bit.
    groups = {
        "cleanup": components["C1"] + components["C2"] + components["C3"],
        "removal": sum(components[f"R{i}"] for i in range(1, 11)),
        "non_structural": components["N1"] + components["N2"] + components["N3"],
        "structural": components["S1"] + components["S2"] + components["S3"],
        "finishing": (components["F1"] + components["F2"] + components["F3"]
                      + components["F4"] + components["F5"]
                      + components["W1"] + components["W2"]),
        "systems": sum(components[f"P{i}"] for i in range(1, 6)),
    }
    abs_damage = sum(groups.values())
    rel_damage = abs_damage / RVN

    return DamageResult(abs_damage, rel_damage, groups, components, RVN)
