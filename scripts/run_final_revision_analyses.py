from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from graded_roof.complexity import manufacturable_mapping
from graded_roof.study import (
    evaluate_design,
    heterogeneous_design,
    simulation_config,
    synthetic_weather_set,
    uniform_design,
)
from graded_roof.weather import resample_weather

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


def stage_robustness() -> None:
    raw = pd.read_csv(RESULTS / "robustness.csv")
    summary = pd.read_csv(RESULTS / "robustness_summary.csv")
    sample_counts = raw.groupby("candidate_id")["sample"].nunique()
    if not sample_counts.eq(250).all():
        raise ValueError("every robustness candidate must have 250 draws")
    perturbations = [
        "friction_factor",
        "adhesion_factor",
        "density_factor",
        "snowfall_factor",
        "temperature_shift_c",
    ]
    for _, sample in raw.groupby("sample"):
        if any(sample[column].nunique() != 1 for column in perturbations):
            raise ValueError("candidates do not share common random draws")

    robust_objectives = [
        "quantile_l_max_kg_per_m",
        "quantile_s_max_kg_per_m",
        "probability_manual_intervention",
    ]
    robust_values = summary[robust_objectives].to_numpy(float)
    robust_nondominated = nondominated(robust_values)
    minimum_score = float(summary["robust_selection_score"].min())
    score_tolerance = 1e-12
    candidate_audit = summary.copy()
    candidate_audit["robust_nondominated"] = robust_nondominated
    candidate_audit["minimum_score_tie"] = np.isclose(
        candidate_audit["robust_selection_score"],
        minimum_score,
        rtol=0.0,
        atol=score_tolerance,
    )
    candidate_audit.to_csv(
        RESULTS / "final_revision_robustness_candidate_audit.csv",
        index=False,
    )

    grouped = summary.assign(
        nominal_l_rounded=summary["nominal_l_max_kg_per_m"].round(
            ROUND_DECIMALS
        ),
        nominal_s_rounded=summary["nominal_s_max_kg_per_m"].round(
            ROUND_DECIMALS
        ),
    ).groupby(["nominal_l_rounded", "nominal_s_rounded"], as_index=False)
    group_rows = []
    for (nominal_l, nominal_s), group in grouped:
        group_rows.append(
            {
                "nominal_l_max_kg_per_m": nominal_l,
                "nominal_s_max_kg_per_m": nominal_s,
                "candidate_count": len(group),
                "design_classes": ";".join(
                    sorted(group["design_class"].unique())
                ),
                "q95_l_min_kg_per_m": group[
                    "quantile_l_max_kg_per_m"
                ].min(),
                "q95_l_max_kg_per_m": group[
                    "quantile_l_max_kg_per_m"
                ].max(),
                "q95_s_min_kg_per_m": group[
                    "quantile_s_max_kg_per_m"
                ].min(),
                "q95_s_max_kg_per_m": group[
                    "quantile_s_max_kg_per_m"
                ].max(),
                "intervention_probability_min": group[
                    "probability_manual_intervention"
                ].min(),
                "intervention_probability_max": group[
                    "probability_manual_intervention"
                ].max(),
                "minimum_score_tie_count": int(
                    candidate_audit.loc[
                        candidate_audit["candidate_id"].isin(
                            group["candidate_id"]
                        ),
                        "minimum_score_tie",
                    ].sum()
                ),
            }
        )
    pd.DataFrame(group_rows).to_csv(
        RESULTS / "final_revision_objective_equivalent_robustness.csv",
        index=False,
    )

    candidate_audit.loc[candidate_audit["minimum_score_tie"]].to_csv(
        RESULTS / "final_revision_robust_selection_ties.csv",
        index=False,
    )


def stage_constructability() -> None:
    complexity = pd.read_csv(
        ROOT / "tables" / "generated" / "table_6_complexity_analysis.csv"
    )
    feasibility_columns = [
        "meets_adjacent_slope_limit",
        "meets_minimum_segment_length",
        "meets_maximum_transitions",
    ]
    complexity["meets_all_constraints"] = complexity[
        feasibility_columns
    ].all(axis=1)
    complexity["l_rounded"] = complexity["l_max_kg_per_m"].round(
        ROUND_DECIMALS
    )
    complexity["s_rounded"] = complexity["s_max_kg_per_m"].round(
        ROUND_DECIMALS
    )
    rows = []
    for keys, group in complexity.groupby(
        ["design_class", "l_rounded", "s_rounded"]
    ):
        design_class, l_value, s_value = keys
        rows.append(
            {
                "design_class": design_class,
                "l_max_kg_per_m": l_value,
                "s_max_kg_per_m": s_value,
                "design_rows": len(group),
                "feasible_design_rows": int(
                    group["meets_all_constraints"].sum()
                ),
                "feasible_fraction": group[
                    "meets_all_constraints"
                ].mean(),
                "minimum_transition_count": group[
                    "transition_count"
                ].min(),
                "maximum_minimum_segment_cells": group[
                    "minimum_segment_cells"
                ].max(),
                "maximum_adjacent_slope_change_deg": group[
                    "maximum_adjacent_slope_change_deg"
                ].max(),
            }
        )
    pd.DataFrame(rows).to_csv(
        RESULTS / "final_revision_constructability_by_objective.csv",
        index=False,
    )

    discretization = pd.read_csv(
        ROOT / "tables" / "generated" / "table_3_discretization.csv"
    )
    continuous = discretization.iloc[0]
    mapped = discretization.iloc[1]
    losses = pd.DataFrame(
        [
            {
                "mapping": mapped["mapping"],
                "l_max_absolute_change_kg_per_m": (
                    mapped["l_max_kg_per_m"]
                    - continuous["l_max_kg_per_m"]
                ),
                "l_max_percent_change": 100
                * (
                    mapped["l_max_kg_per_m"]
                    - continuous["l_max_kg_per_m"]
                )
                / continuous["l_max_kg_per_m"],
                "s_max_absolute_change_kg_per_m": (
                    mapped["s_max_kg_per_m"]
                    - continuous["s_max_kg_per_m"]
                ),
                "s_max_percent_change": 100
                * (
                    mapped["s_max_kg_per_m"]
                    - continuous["s_max_kg_per_m"]
                )
                / continuous["s_max_kg_per_m"],
                "continuous_slope_transitions": continuous[
                    "slope_transition_count"
                ],
                "mapped_slope_transitions": mapped[
                    "slope_transition_count"
                ],
                "continuous_surface_transitions": continuous[
                    "surface_transition_count"
                ],
                "mapped_surface_transitions": mapped[
                    "surface_transition_count"
                ],
            }
        ]
    )
    losses.to_csv(
        RESULTS / "final_revision_discretization_loss.csv",
        index=False,
    )

    enforcement = pd.DataFrame(
        [
            {
                "constraint": "maximum adjacent slope change",
                "continuous_optimization": True,
                "post_hoc_mapping": True,
            },
            {
                "constraint": "minimum segment length",
                "continuous_optimization": False,
                "post_hoc_mapping": True,
            },
            {
                "constraint": "maximum transition count",
                "continuous_optimization": False,
                "post_hoc_mapping": True,
            },
            {
                "constraint": "discrete generic surface classes",
                "continuous_optimization": False,
                "post_hoc_mapping": True,
            },
        ]
    )
    enforcement.to_csv(
        RESULTS / "final_revision_constraint_enforcement.csv",
        index=False,
    )


def stage_jma() -> None:
    evaluation = pd.read_csv(RESULTS / "jma_daily_evaluation.csv")
    config = yaml.safe_load(
        (ROOT / "config" / "production.yaml").read_text(encoding="utf-8")
    )
    station_names = {
        station["id"]: station["name"] for station in config["jma"]["stations"]
    }
    required_classes = {"uniform_knee", "joint_knee"}
    paired_rows = []
    for (station_id, winter), group in evaluation.groupby(
        ["station_id", "winter"]
    ):
        classes = set(group["design_class"])
        if classes != required_classes:
            raise ValueError(
                f"{station_id}/{winter} does not have the required pair"
            )
        uniform = group.loc[group["design_class"] == "uniform_knee"].iloc[0]
        joint = group.loc[group["design_class"] == "joint_knee"].iloc[0]
        paired_rows.append(
            {
                "station_id": station_id,
                "station_name": station_names[station_id],
                "winter": winter,
                "days": int(uniform["days"]),
                "missing_temperature_days": int(
                    uniform["missing_temperature_days"]
                ),
                "missing_snowfall_days": int(
                    uniform["missing_snowfall_days"]
                ),
                "uniform_l_max_kg_per_m": uniform["l_max_kg_per_m"],
                "joint_l_max_kg_per_m": joint["l_max_kg_per_m"],
                "joint_minus_uniform_l_max_kg_per_m": (
                    joint["l_max_kg_per_m"] - uniform["l_max_kg_per_m"]
                ),
                "joint_to_uniform_l_max_ratio": (
                    joint["l_max_kg_per_m"] / uniform["l_max_kg_per_m"]
                ),
                "uniform_s_max_kg_per_m": uniform["s_max_kg_per_m"],
                "joint_s_max_kg_per_m": joint["s_max_kg_per_m"],
                "joint_minus_uniform_s_max_kg_per_m": (
                    joint["s_max_kg_per_m"] - uniform["s_max_kg_per_m"]
                ),
                "joint_to_uniform_s_max_ratio": (
                    joint["s_max_kg_per_m"] / uniform["s_max_kg_per_m"]
                ),
                "s_max_reduction_percent": 100
                * (
                    uniform["s_max_kg_per_m"] - joint["s_max_kg_per_m"]
                )
                / uniform["s_max_kg_per_m"],
                "l_max_increase_percent": 100
                * (
                    joint["l_max_kg_per_m"] - uniform["l_max_kg_per_m"]
                )
                / uniform["l_max_kg_per_m"],
            }
        )
    paired = pd.DataFrame(paired_rows).sort_values(
        ["station_id", "winter"]
    )
    expected_pairs = len(config["jma"]["stations"]) * len(
        config["jma"]["winters"]
    )
    if len(paired) != expected_pairs:
        raise ValueError("JMA station-winter pair count is incomplete")
    paired.to_csv(
        RESULTS / "final_revision_jma_paired_tradeoffs.csv",
        index=False,
    )

    metrics = [
        "joint_to_uniform_l_max_ratio",
        "joint_to_uniform_s_max_ratio",
        "l_max_increase_percent",
        "s_max_reduction_percent",
    ]
    summary_rows = []
    for metric in metrics:
        summary_rows.append(
            {
                "metric": metric,
                "minimum": paired[metric].min(),
                "median": paired[metric].median(),
                "maximum": paired[metric].max(),
            }
        )
    pd.DataFrame(summary_rows).to_csv(
        RESULTS / "final_revision_jma_paired_summary.csv",
        index=False,
    )


def stage_literature() -> None:
    literature = pd.read_csv(ROOT / "references" / "literature_database.csv")
    ledger = pd.read_csv(ROOT / "data" / "metadata" / "acquisition_ledger.csv")
    rows = []
    for record in literature.itertuples(index=False):
        source_rows = ledger.loc[
            ledger["identifier"].fillna("").astype(str).str.lower()
            == str(record.doi_or_identifier).lower()
        ]
        if source_rows.empty:
            source_rows = ledger.loc[
                ledger["url"].fillna("").astype(str) == str(record.url)
            ]
        source_rows = source_rows.loc[
            source_rows["local_status"].eq("verified")
            & source_rows["storage_path"].fillna("").str.startswith("data/raw/")
        ]
        if len(source_rows) != 1:
            raise ValueError(
                f"{record.record_id} does not resolve to one ledger source"
            )
        source = source_rows.iloc[0]
        source_path = ROOT / source["storage_path"]
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        checksum = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if checksum != source["sha256"]:
            raise ValueError(f"checksum mismatch for {record.record_id}")

        volume = ""
        issue = ""
        pages = ""
        metadata_title = record.title
        metadata_year = int(record.year)
        if source_path.suffix == ".json" and str(
            record.doi_or_identifier
        ).startswith("10."):
            metadata = json.loads(source_path.read_text(encoding="utf-8"))[
                "message"
            ]
            volume = metadata.get("volume", "")
            issue = metadata.get("issue", "")
            pages = metadata.get("page", "")
            metadata_title = metadata["title"][0].rstrip(".")
            date = (
                metadata.get("published-print")
                or metadata.get("published")
                or metadata["issued"]
            )
            metadata_year = date["date-parts"][0][0]
        title_matches = (
            record.title.rstrip(".").casefold() == metadata_title.casefold()
        )
        accepted_metadata_variants = {"JP04", "JP07"}
        title_status = (
            "exact"
            if title_matches
            else (
                "verified_metadata_variant"
                if record.record_id in accepted_metadata_variants
                else "unverified"
            )
        )
        rows.append(
            {
                "record_id": record.record_id,
                "authors": record.authors,
                "year": int(record.year),
                "title": record.title,
                "journal_or_publisher": record.journal_or_publisher,
                "volume": volume,
                "issue": issue,
                "pages_or_article_number": pages,
                "doi_or_identifier": record.doi_or_identifier,
                "official_url": record.url,
                "evidence_role": record.evidence_role,
                "claim_supported": record.claim_supported,
                "transfer_limit": record.transfer_limit,
                "snapshot_title": metadata_title,
                "title_verification_status": title_status,
                "year_matches_snapshot": int(record.year) == metadata_year,
                "source_local_status": source["local_status"],
                "source_path": source["storage_path"],
                "source_sha256": checksum,
            }
        )
    audit = pd.DataFrame(rows)
    checks = [
        audit["title_verification_status"].ne("unverified").all(),
        audit["year_matches_snapshot"].all(),
        audit["source_local_status"].eq("verified").all(),
    ]
    if not all(checks):
        raise ValueError("literature verification failed")
    audit.to_csv(
        ROOT / "references" / "final_revision_reference_audit.csv",
        index=False,
    )


def stage_targeted() -> None:
    config = yaml.safe_load(
        (ROOT / "config" / "production.yaml").read_text(encoding="utf-8")
    )
    joint_front = pd.read_csv(RESULTS / "joint_pareto.csv")
    joint_points = joint_front[OBJECTIVES]
    joint_minimum = joint_points.min().to_numpy()
    joint_maximum = joint_points.max().to_numpy()
    joint_row, _ = knee_row(joint_front, joint_minimum, joint_maximum)
    variables = joint_row[
        sorted(
            (column for column in joint_row.index if column.startswith("x_")),
            key=lambda column: int(column.split("_", maxsplit=1)[1]),
        )
    ].to_numpy(dtype=float)
    joint = heterogeneous_design(
        variables,
        config,
        "joint",
        label="joint_continuous_knee",
    )
    mapped, _ = manufacturable_mapping(
        joint,
        config["surface"]["discrete_classes"],
        slope_rounding_deg=config["complexity"]["slope_rounding_deg"],
        minimum_segment_cells=config["roof"]["minimum_segment_cells"],
        maximum_transitions=config["roof"]["maximum_transitions"],
        maximum_adjacent_slope_change_deg=config["roof"][
            "adjacent_slope_limit_deg"
        ],
    )
    mapped = replace(mapped, label="joint_mapped_knee")

    uniform_front = pd.read_csv(RESULTS / "uniform_pareto.csv")
    uniform_points = uniform_front[OBJECTIVES]
    uniform_row, _ = knee_row(
        uniform_front,
        uniform_points.min().to_numpy(),
        uniform_points.max().to_numpy(),
    )
    uniform = uniform_design(
        config,
        float(uniform_row["slope_deg"]),
        float(uniform_row["mu_static"]),
        float(uniform_row["adhesion_pa"]),
        label="uniform_knee",
    )

    master_config = json.loads(json.dumps(config))
    master_config["simulation"]["dt_hours"] = min(
        config["convergence"]["dt_hours"]
    )
    master_weathers = synthetic_weather_set(master_config)
    settings = simulation_config(config)
    rows = []
    for design in [uniform, joint, mapped]:
        for dt_hours in config["convergence"]["dt_hours"]:
            weathers = [
                resample_weather(weather, dt_hours)
                for weather in master_weathers
            ]
            aggregate, _ = evaluate_design(design, weathers, settings)
            rows.append(
                {
                    "design": design.label,
                    "cells": design.cells,
                    "dt_hours": dt_hours,
                    **{
                        key: value
                        for key, value in aggregate.items()
                        if key != "design"
                    },
                }
            )
    frame = pd.DataFrame(rows)
    metrics = [
        "l_max_kg_per_m",
        "s_max_kg_per_m",
        "mean_event_count",
        "mean_ssci",
    ]
    for _design, indices in frame.groupby("design").groups.items():
        group = frame.loc[indices]
        reference = group.loc[
            group["dt_hours"] == min(config["convergence"]["dt_hours"])
        ].iloc[0]
        for metric in metrics:
            denominator = max(abs(float(reference[metric])), 1e-12)
            frame.loc[indices, f"{metric}_relative_error"] = (
                frame.loc[indices, metric] - float(reference[metric])
            ).abs() / denominator
    relative_error_columns = [
        f"{metric}_relative_error" for metric in metrics
    ]
    frame["maximum_relative_error"] = frame[relative_error_columns].max(axis=1)
    frame["within_tolerance"] = (
        frame["maximum_relative_error"]
        <= config["convergence"]["relative_tolerance"]
    )
    frame.to_csv(
        RESULTS / "final_revision_selected_design_timestep_audit.csv",
        index=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=[
            "frontier",
            "knee",
            "robustness",
            "constructability",
            "jma",
            "literature",
            "targeted",
        ],
        required=True,
    )
    args = parser.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    if args.stage == "frontier":
        stage_frontier()
    elif args.stage == "knee":
        stage_knee()
    elif args.stage == "robustness":
        stage_robustness()
    elif args.stage == "constructability":
        stage_constructability()
    elif args.stage == "jma":
        stage_jma()
    elif args.stage == "literature":
        stage_literature()
    elif args.stage == "targeted":
        stage_targeted()


if __name__ == "__main__":
    main()
