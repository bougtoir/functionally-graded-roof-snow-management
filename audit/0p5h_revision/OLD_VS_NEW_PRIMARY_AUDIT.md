# Old-versus-new primary audit

The 0.5-h rerun retained nominal intermediate joint trade-offs, but fewer unique pairs remained and no joint row passed every post hoc constructability check. Mapping loss and the targeted 0.25-h sensitivity make constructability and interval dependence the dominant interpretation.

| Section | Class | Item | Metric | 1 h | 0.5 h | Relative change |
|---|---|---|---|---:|---:|---:|
| baseline | uniform_baseline | conventional_shedding | l_max_kg_per_m | 79.999 | 39.9995 | -50.00% |
| baseline | uniform_baseline | conventional_shedding | s_max_kg_per_m | 79.999 | 39.9995 | -50.00% |
| frontier | uniform | complete_front | unique_objective_pairs | 2 | 2 | +0.00% |
| frontier | joint | complete_front | unique_objective_pairs | 8 | 6 | -25.00% |
| descriptive_knee | joint | front_specific_normalization | l_max_kg_per_m | 3210.64 | 4547.37 | +41.63% |
| descriptive_knee | joint | front_specific_normalization | s_max_kg_per_m | 39.9995 | 12.2798 | -69.30% |
| frontier_metric | uniform | zero_origin_1p05_reference | normalized_hypervolume_fraction | 0.402463 | 0.701118 | +74.21% |
| frontier_metric | joint | zero_origin_1p05_reference | normalized_hypervolume_fraction | 0.611446 | 0.761655 | +24.57% |
| constructability | joint | all_objective_groups | feasible_design_rows | 9 | 0 | -100.00% |
| constructability | joint | selected_knee_mapping | l_max_percent_change | 0.363725 | -98.2786 | -27120.06% |
| constructability | joint | selected_knee_mapping | s_max_percent_change | 11.03 | 537.469 | +4772.79% |
| robustness | joint_and_uniform | largest_objective_equivalent_group | candidate_count | 14 | 12 | -14.29% |
| robustness | joint_and_uniform | largest_objective_equivalent_group | q95_l_min_kg_per_m | 103.786 | 51.8931 | -50.00% |
| robustness | joint_and_uniform | largest_objective_equivalent_group | q95_l_max_kg_per_m | 7465.52 | 5816.68 | -22.09% |
| robustness | joint_and_uniform | largest_objective_equivalent_group | q95_s_min_kg_per_m | 103.786 | 51.8931 | -50.00% |
| robustness | joint_and_uniform | largest_objective_equivalent_group | q95_s_max_kg_per_m | 5482.6 | 2726.63 | -50.27% |
| robustness | joint_and_uniform | minimum_score_tie | candidate_count | 6 | 6 | +0.00% |
| jma_scenario | joint_vs_uniform | station_winter_median | joint_to_uniform_l_max_ratio | 5.10408 | 8.34906 | +63.58% |
| jma_scenario | joint_vs_uniform | station_winter_median | joint_to_uniform_s_max_ratio | 0.5 | 0.291667 | -41.67% |
| jma_scenario | joint_vs_uniform | station_winter_median | l_max_increase_percent | 410.408 | 734.906 | +79.07% |
| jma_scenario | joint_vs_uniform | station_winter_median | s_max_reduction_percent | 50 | 70.8333 | +41.67% |

The complete machine-readable comparison is `results/generated/1h_vs_0p5h.csv`.
