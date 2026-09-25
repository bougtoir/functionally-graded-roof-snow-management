from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "generated"
AUDIT = ROOT / "audit" / "final_revision"
OBJECTIVES = ["l_max_kg_per_m", "s_max_kg_per_m"]
CLASSES = ["uniform", "geometry", "surface", "joint"]
ROUND_DECIMALS = 6


def unique_objectives(frame: pd.DataFrame) -> pd.DataFrame:
    values = frame[OBJECTIVES].round(ROUND_DECIMALS)
    return values.drop_duplicates().sort_values(OBJECTIVES).reset_index(drop=True)


def nondominated(points: np.ndarray) -> np.ndarray:
    mask = np.ones(len(points), dtype=bool)
    for index, point in enumerate(points):
        dominated = np.all(points <= point, axis=1) & np.any(
            points < point, axis=1
        )
        if dominated.any():
            mask[index] = False
    return mask


def hypervolume_fraction(points: np.ndarray, reference: np.ndarray) -> float:
    values = np.unique(points, axis=0)
    values = values[nondominated(values)]
    values = values[np.argsort(values[:, 0])]
    area = 0.0
    previous_y = float(reference[1])
    for x_value, y_value in values:
        if y_value < previous_y:
            area += (reference[0] - x_value) * (previous_y - y_value)
            previous_y = float(y_value)
    return float(area / np.prod(reference))


def additive_epsilon(
    approximation: np.ndarray,
    reference: np.ndarray,
) -> float:
    distances = approximation[:, None, :] - reference[None, :, :]
    return float(np.max(np.min(np.max(distances, axis=2), axis=0)))


def strict_dominated_fraction(
    candidate: np.ndarray,
    combined: np.ndarray,
) -> float:
    dominated = [
        bool(
            (
                np.all(combined <= point, axis=1)
                & np.any(combined < point, axis=1)
            ).any()
        )
        for point in candidate
    ]
    return float(np.mean(dominated))


def normalization(
    points: np.ndarray,
    global_minimum: np.ndarray,
    global_maximum: np.ndarray,
    origin: str,
) -> np.ndarray:
    if origin == "zero":
        return points / np.where(global_maximum > 0, global_maximum, 1.0)
    span = np.where(
        global_maximum > global_minimum,
        global_maximum - global_minimum,
        1.0,
    )
    return (points - global_minimum) / span


def stage_frontier() -> None:
    fronts = {
        name: pd.read_csv(RESULTS / f"{name}_pareto.csv") for name in CLASSES
    }
    unique = {name: unique_objectives(frame) for name, frame in fronts.items()}
    labeled_unique = pd.concat(
        [frame.assign(design_class=name) for name, frame in unique.items()],
        ignore_index=True,
    )
    labeled_unique.to_csv(
        RESULTS / "final_revision_frontier_unique_objectives.csv",
        index=False,
    )
    combined = labeled_unique[OBJECTIVES].to_numpy(float)
    global_minimum = combined.min(axis=0)
    global_maximum = combined.max(axis=0)
    normalized_uniform = normalization(
        unique["uniform"].to_numpy(float),
        global_minimum,
        global_maximum,
        "minimum",
    )
    summary_rows = []
    for name in CLASSES:
        raw = fronts[name][OBJECTIVES].to_numpy(float)
        points = unique[name].to_numpy(float)
        normalized = normalization(
            points,
            global_minimum,
            global_maximum,
            "minimum",
        )
        summary_rows.append(
            {
                "design_class": name,
                "nondominated_design_rows": len(raw),
                "unique_objective_pairs": len(points),
                "duplicate_design_rows": len(raw) - len(points),
                "unique_pair_fraction": len(points) / len(raw),
                "strict_dominated_fraction_unique_pairs": (
                    strict_dominated_fraction(points, combined)
                ),
                "additive_epsilon_vs_uniform_common_minmax": (
                    additive_epsilon(normalized, normalized_uniform)
                ),
                "uniform_epsilon_vs_class_common_minmax": additive_epsilon(
                    normalized_uniform,
                    normalized,
                ),
            }
        )
    pd.DataFrame(summary_rows).to_csv(
        RESULTS / "final_revision_frontier_summary.csv",
        index=False,
    )

    sensitivity_rows = []
    for origin in ("zero", "minimum"):
        for margin in (1.05, 1.10):
            reference = np.array([margin, margin])
            for name in CLASSES:
                points = normalization(
                    unique[name].to_numpy(float),
                    global_minimum,
                    global_maximum,
                    origin,
                )
                sensitivity_rows.append(
                    {
                        "normalization_origin": origin,
                        "reference_margin": margin,
                        "design_class": name,
                        "normalized_hypervolume_fraction": (
                            hypervolume_fraction(points, reference)
                        ),
                    }
                )
    pd.DataFrame(sensitivity_rows).to_csv(
        RESULTS / "final_revision_frontier_metric_sensitivity.csv",
        index=False,
    )

    seed_rows = []
    for name in ("geometry", "surface", "joint"):
        for path in sorted(RESULTS.glob(f"{name}_seed_*_pareto.csv")):
            seed = int(path.stem.split("_")[2])
            frame = pd.read_csv(path)
            points = unique_objectives(frame).to_numpy(float)
            normalized = normalization(
                points,
                global_minimum,
                global_maximum,
                "minimum",
            )
            seed_rows.append(
                {
                    "design_class": name,
                    "seed": seed,
                    "nondominated_design_rows": len(frame),
                    "unique_objective_pairs": len(points),
                    "common_normalized_hypervolume": hypervolume_fraction(
                        normalized,
                        np.array([1.05, 1.05]),
                    ),
                }
            )
    pd.DataFrame(seed_rows).to_csv(
        RESULTS / "final_revision_per_seed_frontier_audit.csv",
        index=False,
    )


def knee_row(
    points: pd.DataFrame,
    minimum: np.ndarray,
    maximum: np.ndarray,
) -> tuple[pd.Series, float]:
    span = np.where(maximum > minimum, maximum - minimum, 1.0)
    normalized = (points[OBJECTIVES].to_numpy(float) - minimum) / span
    distances = np.linalg.norm(normalized, axis=1)
    index = int(np.argmin(distances))
    return points.iloc[index], float(distances[index])


def stage_knee() -> None:
    fronts = {
        name: unique_objectives(
            pd.read_csv(RESULTS / f"{name}_pareto.csv")
        )
        for name in CLASSES
    }
    combined = pd.concat(fronts.values(), ignore_index=True)[OBJECTIVES]
    common_minimum = combined.min().to_numpy(float)
    common_maximum = combined.max().to_numpy(float)
    knee_rows = []
    for name, points in fronts.items():
        class_minimum = points[OBJECTIVES].min().to_numpy(float)
        class_maximum = points[OBJECTIVES].max().to_numpy(float)
        front_knee, front_distance = knee_row(
            points,
            class_minimum,
            class_maximum,
        )
        common_knee, common_distance = knee_row(
            points,
            common_minimum,
            common_maximum,
        )
        for method, row, distance in [
            ("front_specific_minmax", front_knee, front_distance),
            ("common_combined_minmax", common_knee, common_distance),
        ]:
            knee_rows.append(
                {
                    "design_class": name,
                    "normalization": method,
                    "l_max_kg_per_m": row["l_max_kg_per_m"],
                    "s_max_kg_per_m": row["s_max_kg_per_m"],
                    "normalized_distance_to_ideal": distance,
                }
            )
    pd.DataFrame(knee_rows).to_csv(
        RESULTS / "final_revision_knee_audit.csv",
        index=False,
    )

    l_thresholds = sorted(
        set(
            pd.concat(fronts.values(), ignore_index=True)[
                "l_max_kg_per_m"
            ].tolist()
        )
    )
    s_thresholds = sorted(
        set(
            pd.concat(fronts.values(), ignore_index=True)[
                "s_max_kg_per_m"
            ].tolist()
        )
    )
    matched_rows = []
    for threshold in l_thresholds:
        for name, points in fronts.items():
            feasible = points[points["l_max_kg_per_m"] <= threshold + 1e-6]
            matched_rows.append(
                {
                    "constraint": "l_max_at_most",
                    "threshold_kg_per_m": threshold,
                    "design_class": name,
                    "feasible": not feasible.empty,
                    "best_other_objective_kg_per_m": (
                        feasible["s_max_kg_per_m"].min()
                        if not feasible.empty
                        else np.nan
                    ),
                }
            )
    for threshold in s_thresholds:
        for name, points in fronts.items():
            feasible = points[points["s_max_kg_per_m"] <= threshold + 1e-6]
            matched_rows.append(
                {
                    "constraint": "s_max_at_most",
                    "threshold_kg_per_m": threshold,
                    "design_class": name,
                    "feasible": not feasible.empty,
                    "best_other_objective_kg_per_m": (
                        feasible["l_max_kg_per_m"].min()
                        if not feasible.empty
                        else np.nan
                    ),
                }
            )
    pd.DataFrame(matched_rows).to_csv(
        RESULTS / "final_revision_matched_tradeoffs.csv",
        index=False,
    )

    config_thresholds = [20.0, 80.0, 200.0]
    constrained_rows = []
    for threshold in config_thresholds:
        for name, points in fronts.items():
            feasible = points[points["s_max_kg_per_m"] <= threshold + 1e-6]
            constrained_rows.append(
                {
                    "s_max_limit_kg_per_m": threshold,
                    "design_class": name,
                    "feasible": not feasible.empty,
                    "minimum_l_max_kg_per_m": (
                        feasible["l_max_kg_per_m"].min()
                        if not feasible.empty
                        else np.nan
                    ),
                }
            )
    pd.DataFrame(constrained_rows).to_csv(
        RESULTS / "final_revision_prespecified_constraints.csv",
        index=False,
    )

    uniform = fronts["uniform"]
    joint = fronts["joint"]
    region_rows = []
    for _, point in joint.iterrows():
        uniform_same_or_better = uniform[
            (uniform["l_max_kg_per_m"] <= point["l_max_kg_per_m"] + 1e-6)
            & (uniform["s_max_kg_per_m"] <= point["s_max_kg_per_m"] + 1e-6)
        ]
        region_rows.append(
            {
                **point.to_dict(),
                "attainable_by_uniform_under_same_caps": (
                    not uniform_same_or_better.empty
                ),
            }
        )
    pd.DataFrame(region_rows).to_csv(
        RESULTS / "final_revision_joint_unique_regions.csv",
        index=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["frontier", "knee"],
        required=True,
    )
    args = parser.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    if args.stage == "frontier":
        stage_frontier()
    elif args.stage == "knee":
        stage_knee()


if __name__ == "__main__":
    main()
