# Phase 10 manuscript revision

## Implemented changes

- Presents the exhaustive uniform objective set before heterogeneous comparisons.
- Replaces the cross-front knee percentage headline with unique objective regions,
  common-reference hypervolume, additive epsilon, and matched objective caps.
- States that heterogeneous fronts are heuristic multi-seed results.
- Makes objective-equivalent robustness variation and the six-way robust-score tie
  prominent.
- Makes constructability screening, mapping loss, and transition-penalty results
  prominent.
- Reports the failed selected-design timestep criterion as a limitation.
- Adds paired JMA ranges while retaining the scenario-forcing-only interpretation.
- Discusses retention, shedding, active, manual, and hybrid strategies as conditional
  choices.
- Answers the research question directly in the Discussion and avoids universal,
  structural-safety, pedestrian-safety, and code-compliance claims.
- Generates all quantitative manuscript values from canonical result files.

## Verification

- Abstract length: 182 words.
- `ruff check src/graded_roof/manuscript.py`: pass.
- `pytest -q tests/test_manuscript.py tests/test_study.py`: 6 passed.
- Manuscript DOCX regenerated successfully.

## Remaining work

Figures and editable tables still require the Phase 11 rebuild. The DOCX will be
regenerated again after that rebuild and before packaging.
