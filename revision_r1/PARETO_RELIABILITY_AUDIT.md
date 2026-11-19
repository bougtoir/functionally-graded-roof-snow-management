# PARETO_RELIABILITY_AUDIT (R1)

Sources: `results/r1/pareto/front_summary.csv`, `per_seed_budget_hypervolume.csv`, `front_recheck_fine.csv`, `front_summary_fine_recheck.csv`, `uniform_gap_coverage.csv`. Script `scripts/r1_analyze.py`.

## Front comparison (dt = 1 h)
| set | unique_objective_pairs | hv_max_x1.1 | hv_max_x1.05 | hv_max_x1.5 | eps_set_to_uniform | eps_uniform_to_set | eps_norm_set_to_uniform | eps_norm_uniform_to_set | nondominated_designs_incl_ties | matched_l_improvement_median | matched_l_improvement_maximum | matched_s_improvement_median | matched_s_improvement_maximum | graded_pairs_on_front |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uniform | 26 | 0.9822 | 0.9807 | 0.9895 | 0.0 | 0.0 | 0.0 | 0.0 | 69 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| geometry | 89 | 0.9869 | 0.9858 | 0.992 | 0.0 | 78.369 | 0.0 | 0.0126 | 1344 | 0.0064 | 0.0471 | 0.0049 | 0.1409 | 82 |
| surface | 49 | 0.9879 | 0.987 | 0.9926 | 0.0 | 80.3775 | 0.0 | 0.0129 | 2482 | 0.0 | 0.0 | 0.0 | 0.0 | 24 |
| joint | 86 | 0.988 | 0.987 | 0.9926 | 0.0 | 80.3775 | 0.0 | 0.0129 | 1070 | 0.0064 | 0.0471 | 0.0049 | 0.1409 | 80 |

## Per-seed / budget hypervolume (ref 1.1 x max)
| mode | seed | 15 | 30 | 45 |
|---|---|---|---|---|
| geometry | 1701 | 0.9843 | 0.9852 | 0.9853 |
| geometry | 2903 | 0.9828 | 0.985 | 0.9854 |
| geometry | 4517 | 0.9842 | 0.9863 | 0.9865 |
| geometry | 6007 | 0.9846 | 0.9862 | 0.9867 |
| geometry | 8191 | 0.9847 | 0.9857 | 0.9858 |
| joint | 1701 | 0.9862 | 0.9871 | 0.9875 |
| joint | 2903 | 0.9868 | 0.9876 | 0.9877 |
| joint | 4517 | 0.9877 | 0.9878 | 0.9879 |
| joint | 6007 | 0.9863 | 0.9872 | 0.9877 |
| joint | 8191 | 0.9862 | 0.9873 | 0.9876 |
| surface | 1701 | 0.9878 | 0.9878 | 0.9879 |
| surface | 2903 | 0.9854 | 0.9856 | 0.9861 |
| surface | 4517 | 0.9861 | 0.9875 | 0.9879 |
| surface | 6007 | 0.9856 | 0.9877 | 0.9878 |
| surface | 8191 | 0.9876 | 0.9879 | 0.9879 |

## Fine re-check of all 211 nondominated designs
- l_max_kg_per_m: median rel. change dt 1 -> 0.0625 h 0.03%, p95 0.12%, max 1.3%
- s_event_max_kg_per_m: median rel. change dt 1 -> 0.0625 h 0.03%, p95 5.93%, max 13.4%

| set | hv_max_x1.1_fine | eps_set_to_uniform_fine | eps_uniform_to_set_fine |
|---|---|---|---|
| uniform | 0.9822 | 0.0 | 0.0 |
| geometry | 0.9869 | 0.0431 | 78.355 |
| surface | 0.9879 | 0.0 | 80.3593 |
| joint | 0.988 | 0.0431 | 80.3593 |

## Interpretation
- No graded front is dominated by the uniform front; HV gains are small (<= 0.006) and robust to the reference point.
- Graded designs fill the uniform L_max gap in every seed (post hoc descriptive; see CONSTRAINED_OPTIMIZATION_AUDIT.md).
- Optimiser convergence is assessed only by seed spread and the 15/30/45-generation budget table above.
- Optimiser convergence, numerical convergence and physical validation are distinct; only the first two are assessed.