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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["frontier"],
        required=True,
    )
    args = parser.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    if args.stage == "frontier":
        stage_frontier()


if __name__ == "__main__":
    main()
