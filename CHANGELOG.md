# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
semantic versioning.

## [0.1.0] - 2026-06-15

Initial release: a faithful, dependency-light Python port of the INSYDE flood
depth-damage model (Dottori et al. 2016).

### Added
- `compute_damage` — INSYDE engine ported from `insyde_function.R`, component by
  component, in deterministic and Monte-Carlo modes.
- `ExposureVariables` / `HazardVariables` input containers.
- Loaders for the original INSYDE EUR unit prices and replacement values.
- The original R sources under `r_reference/` for line-by-line comparison, and
  `PORTING.md` documenting fidelity (including the deliberate C4/F6
  exclude-from-totals quirk).
- `examples/run_insyde.py` — the R example reproduced in Python.
- PEP 561 `py.typed` marker so downstream users get type information.
- CI across Python 3.10–3.13; Codex automation for PR review, issue triage, and
  release notes (the release workflow falls back to GitHub auto-notes when no
  API key is configured).

[0.1.0]: https://github.com/pengkodammaya/pyinsyde/releases/tag/v0.1.0
