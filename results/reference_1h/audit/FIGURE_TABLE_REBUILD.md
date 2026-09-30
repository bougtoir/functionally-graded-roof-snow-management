# Phase 11 figure and table rebuild

## Canonical table inputs

- Table 1 now uses the final frontier summary, common-reference hypervolume,
  additive epsilon, unique objective-pair counts, and front-specific descriptive
  knees.
- Table 2 contains the continuous joint-knee profile and its post hoc mapped
  profile.
- Table 3 reports mapping changes both as absolute values with units and as
  percentages.
- Table 8 uses the candidate-level robustness audit, including the robust
  nondominance and minimum-score-tie fields.
- Table 9 uses the 12 paired JMA station-winter comparisons.

## Figure changes

- Figure 3 displays unique objective pairs in a full-range panel and a clearly
  labeled intermediate-region panel.
- Figure 4 directly compares continuous and mapped slope and friction profiles
  and shows the mapped generic surface classes.
- Figure 5 removes duplicate objective-pair overplotting.
- Figure 6 displays all four frozen convergence metrics and marks the 24-cell,
  1-h production setting.
- Figure 7 labels every prespecified low/high factor or encoded alternative and
  defines the plotted quantity as relative change from baseline.
- Figure 8 replaces 6,250 perturbed-point overlays with candidate-level Q95
  outcomes under the paired perturbation draws.
- Figure 9 aggregates phase-diagram selections into frequency-scaled objective
  points and shows the frozen labor-scarcity comparison explicitly.

## Output and document checks

- Nine figures were regenerated in PNG, TIFF, SVG, PDF, and EPS formats.
- Nine machine-readable CSV tables were regenerated.
- The separate manuscript contains editable tables and separate figure captions.
- The inline manuscript contains nine figures and nine editable tables.
- Figure and table captions were updated to match the rebuilt content.

## Verification

- `ruff check src/graded_roof/reporting.py src/graded_roof/manuscript.py`: pass.
- `python -m py_compile src/graded_roof/reporting.py src/graded_roof/manuscript.py`:
  pass.
- `pytest -q tests/test_manuscript.py tests/test_study.py`: 6 passed.
- `git diff --check`: pass.
