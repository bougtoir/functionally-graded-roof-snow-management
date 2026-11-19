# PHYSICAL_BENCHMARK_AUDIT (R1)

## What can be benchmarked
| Component | Model statement | Independent evidence available in project | Benchmark performed | Outcome |
|---|---|---|---|---|
| Sliding onset (Coulomb + adhesion) | Release when `m g sin θ ≥ μs m g cos θ + c A` | Qualitative friction/adhesion dependence on roughness, water content, ageing (Tomabechi 1996; Ito 1997; Fasani 2026) | Analytic verification only (`tests/test_simulation_v2.py::test_static_threshold_release_mass_is_analytic`) | Code reproduces the closed-form threshold to 1e-6; physical coefficient values unbenchmarked |
| Snow-guard / retention behaviour | High-friction class retains | Takakura 2003 snow-guard tests (test-specific) | none quantitative | Not comparable (guard spacing/strength not modelled) |
| Roof snow load time series | Retained mass | Tominaga et al. 2025 load-cell dataset (10.1016/j.coldregions.2025.104445) | **Not performed**: raw time series not in project storage | Identified as primary future validation target |
| Mass conservation | Input = shed + melt + residual | — | Verified in every run (< 1e-6 kg m⁻¹) | Pass |
| Timestep independence | Event endpoints | — | `NUMERICAL_CONVERGENCE_AUDIT.md` | Pass under pre-specified rule |

## Conclusion
Only verification (analytic, conservation, convergence) was possible. No component-level parameter was calibrated or validated against measurements; literature supports the direction of parameter effects, not their values. The manuscript therefore calls the model a "reduced-order comparative model" and avoids "validated".
