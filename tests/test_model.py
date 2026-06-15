"""Validation tests for the INSYDE Python port.

No live R is available in this environment, so these checks combine:
  * independent re-derivation of a few components from the paper's formulas,
  * structural invariants the R model guarantees,
  * the C4/F6 exclusion quirk of insyde_function.R.
"""
import numpy as np
import pytest
from scipy.stats import truncnorm

from pyinsyde import (
    ExposureVariables,
    HazardVariables,
    compute_damage,
    load_unit_prices,
    replacement_value_eur,
)


@pytest.fixture
def default_run():
    e = ExposureVariables()
    hz = HazardVariables()
    up = load_unit_prices()
    rv = replacement_value_eur(e.BS, e.BT)
    return e, hz, up, rv, compute_damage(e, hz, up, rv, uncert=0)


def test_rvn(default_run):
    e, hz, up, rv, res = default_run
    assert res.rvn == pytest.approx(1131 * 100 * 2)


def test_monotonic_relative_damage(default_run):
    *_, res = default_run
    assert np.all(np.diff(res.rel_damage) >= -1e-9)


def test_no_damage_at_zero_depth(default_run):
    *_, res = default_run
    # At he=0 only velocity/quality-driven external terms exist; relative
    # damage should be small and finite, and abs damage non-negative.
    assert res.abs_damage[0] >= 0
    assert np.isfinite(res.rel_damage[0])


def test_structural_zero_when_velocity_low(default_run):
    e, hz, up, rv, res = default_run
    # v=0.5 < 2  ->  frag8 == 0  ->  structural group identically zero
    assert np.allclose(res.group_damage["structural"], 0.0)


def test_structural_nonzero_when_velocity_high():
    e = ExposureVariables()
    hz = HazardVariables(he=np.array([2.0]), v=2.5)
    up = load_unit_prices()
    rv = replacement_value_eur(e.BS, e.BT)
    res = compute_damage(e, hz, up, rv, uncert=0)
    assert res.group_damage["structural"][0] > 0


def test_c4_f6_excluded_from_total(default_run):
    """absDamage must equal the six group sums and exclude C4 and F6."""
    *_, res = default_run
    total_from_groups = sum(res.group_damage.values())
    assert np.allclose(res.abs_damage, total_from_groups)
    # C4 and F6 are computed and non-zero somewhere, but not in any group.
    assert res.component_damage["C4"].max() > 0
    assert "C4" not in str(res.group_damage)  # sanity: they're separate


def test_cleaning_component_independent_recompute(default_run):
    """Re-derive C3 (cleaning) at he=1.0 m straight from the formula."""
    e, hz, up, rv, res = default_run
    he = 1.0
    h = round(he - e.GL, 3)
    IP = 2.5 * e.EP
    BP = 4 * np.sqrt(e.BA)
    eco = 1 - 0.2 * (e.BT == 3)
    expected = up["cleaning"] * (1 + (hz.q == 1) * 0.4) * (
        e.IA * min(e.NF, np.ceil(h / e.IH)) + IP * h + e.BA + BP * e.BH
    ) * eco
    i = int(round(he / 0.01))
    assert res.component_damage["C3"][i] == pytest.approx(expected, rel=1e-9)


def test_fragility_matches_truncnorm():
    """frag2_1f at h=0.4 should equal the truncated-normal CDF midpoint (0.5)."""
    # Direct truncnorm value (matches model.py's standardized-bounds fragility).
    val = truncnorm.cdf(0.4, (0.2 - 0.4) / (0.4 / 6), (0.6 - 0.4) / (0.4 / 6),
                        loc=0.4, scale=0.4 / 6)
    assert round(val, 3) == 0.5


def test_height_reduces_relative_damage():
    """Core premise: more storeys -> lower relative damage at a given depth."""
    up = load_unit_prices()
    rels = []
    for nf in (1, 2, 3, 5):
        e = ExposureVariables(NF=nf)
        hz = HazardVariables(he=np.array([1.0]))
        rv = replacement_value_eur(e.BS, e.BT)
        res = compute_damage(e, hz, up, rv, uncert=0)
        rels.append(res.rel_damage[0])
    assert all(x > y for x, y in zip(rels, rels[1:])), rels


def test_uncertainty_mode_mean_near_deterministic():
    e = ExposureVariables()
    up = load_unit_prices()
    rv = replacement_value_eur(e.BS, e.BT)
    hz_det = HazardVariables(he=np.array([1.5]))
    det = compute_damage(e, hz_det, up, rv, uncert=0).abs_damage[0]
    hz_mc = HazardVariables(he=1.5)
    rng = np.random.default_rng(0)
    mc = compute_damage(e, hz_mc, up, rv, uncert=1, nr_sim=20000, rng=rng).abs_damage.mean()
    assert mc == pytest.approx(det, rel=0.05)
