# Contributing to pyinsyde

Thanks for your interest! `pyinsyde` is a **faithful port of the INSYDE R model**,
so the guiding rule is *fidelity to the reference*. The original R sources live in
[`r_reference/`](r_reference/) and are the source of truth.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/):

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run ruff check .
uv run pytest -q
```

CI runs the same lint + tests across Python 3.10–3.13; all must pass.

## Ground rules

- **Keep the dependency surface minimal.** Runtime deps are only `numpy` and
  `scipy`. Don't add new hard dependencies to `[project].dependencies` without
  strong justification.
- **Preserve fidelity to the R model.** If you change the damage math, it must
  still match `r_reference/`; explain any deviation and update
  [`PORTING.md`](PORTING.md). Note the deliberate quirk: components **C4**
  (dehumidification) and **F6** (baseboard) are computed but **excluded from the
  reported totals** on purpose — don't "fix" it.
- **Relative depth-damage curves must be monotone non-decreasing** in depth.
- **Add tests** for behaviour you change; mirror the style in
  [`tests/test_model.py`](tests/test_model.py) (independent re-derivation +
  structural invariants).

See [`AGENTS.md`](AGENTS.md) for the conventions agents and reviewers follow.

## Pull requests

Open a PR against `main`. CI must be green. An automated Codex review comments on
the diff (correctness, units, R-fidelity, monotonicity, new dependencies) — treat
it as a helpful first pass, not a gate.

## License

By contributing you agree your contributions are licensed under the project's
**GPL-3.0-or-later** license.
