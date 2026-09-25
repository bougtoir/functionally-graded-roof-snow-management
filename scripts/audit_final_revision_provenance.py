from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "audit" / "final_revision"

TRACE_ROWS = [
    (
        "synthetic weather",
        "config/production.yaml",
        "src/graded_roof/weather.py; src/graded_roof/study.py",
        "results/generated/baseline_aggregate.csv; results/generated/*_pareto.csv",
        "tables/generated/table_1_pareto_summary.csv",
        "src/graded_roof/manuscript.py",
    ),
    (
        "uniform design space",
        "config/production.yaml",
        "scripts/run_pipeline.py:stage_uniform",
        "results/generated/uniform_design_space.csv; results/generated/uniform_pareto.csv",
        "tables/generated/table_1_pareto_summary.csv",
        "src/graded_roof/manuscript.py",
    ),
    (
        "heterogeneous optimization",
        "analysis_freeze.yaml; config/production.yaml",
        "src/graded_roof/optimization.py; scripts/run_pipeline.py:stage_optimize",
        "results/generated/geometry_pareto.csv; "
        "results/generated/surface_pareto.csv; "
        "results/generated/joint_pareto.csv",
        "tables/generated/table_1_pareto_summary.csv; "
        "tables/generated/supplement_optimizer_stochasticity.csv",
        "src/graded_roof/manuscript.py",
    ),
    (
        "robustness",
        "config/production.yaml#robustness",
        "scripts/run_pipeline.py:stage_robustness",
        "results/generated/robustness.csv; results/generated/robustness_summary.csv",
        "tables/generated/table_8_robustness_summary.csv",
        "src/graded_roof/manuscript.py",
    ),
    (
        "JMA daily scenarios",
        "data/raw/jma_daily/20260924T120000Z; data/metadata/jma_daily_20260924T120000Z.json",
        "src/graded_roof/jma.py; scripts/run_pipeline.py:stage_jma",
        "data/processed/jma_daily_observations.csv; results/generated/jma_daily_evaluation.csv",
        "tables/generated/table_9_jma_daily_evaluation.csv",
        "src/graded_roof/manuscript.py",
    ),
    (
        "figures",
        "results/generated; tables/generated",
        "src/graded_roof/reporting.py:generate_figures",
        "figures/png; figures/tiff; figures/vector",
        "manuscript/editable_figures_CRST.pptx",
        "src/graded_roof/manuscript.py",
    ),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_trace() -> None:
    path = OUTPUT / "provenance_trace.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "analysis",
                "raw_or_configuration",
                "processing",
                "canonical_result",
                "figure_or_table",
                "manuscript_generator",
            ]
        )
        writer.writerows(TRACE_ROWS)


def write_checksums() -> int:
    patterns = [
        "analysis_freeze.yaml",
        "config/*.yaml",
        "data/metadata/*",
        "data/processed/*",
        "data/raw/jma_daily/20260924T120000Z/*",
        "references/*.csv",
        "results/generated/*.csv",
        "tables/generated/*.csv",
    ]
    paths = sorted(
        {
            path
            for pattern in patterns
            for path in ROOT.glob(pattern)
            if path.is_file()
        }
    )
    output = OUTPUT / "canonical_artifact_checksums.csv"
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "size_bytes", "sha256"])
        for path in paths:
            writer.writerow(
                [path.relative_to(ROOT), path.stat().st_size, digest(path)]
            )
    return len(paths)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_trace()
    checksum_count = write_checksums()
    ledger = pd.read_csv(ROOT / "data" / "metadata" / "acquisition_ledger.csv")
    jma = ledger[
        ledger["storage_path"].fillna("").str.contains("data/raw/jma_daily/")
    ]
    status_counts = {
        str(status): int(count)
        for status, count in ledger["local_status"].value_counts(
            dropna=False
        ).items()
    }
    bad_statuses = {"size_mismatch", "checksum_mismatch"}
    source_paths = [
        path
        for base in (ROOT / "src", ROOT / "scripts")
        for path in base.rglob("*.py")
        if path.name != Path(__file__).name
    ]
    source_text = "\n".join(
        path.read_text(encoding="utf-8") for path in source_paths
    )
    embedded_results = [
        value
        for value in ("3210.6", "3913.3", "6417.0", "4200.4", "226.0")
        if value in source_text
    ]
    checks = {
        "freeze_record_present": (ROOT / "analysis_freeze.yaml").exists(),
        "production_config_present": (ROOT / "config" / "production.yaml").exists(),
        "ledger_has_no_corrupt_local_files": not any(
            status in bad_statuses for status in status_counts
        ),
        "jma_quantitative_inputs_verified": bool(
            len(jma) > 0 and jma["local_status"].eq("verified").all()
        ),
        "optimizer_checkpoint_count_is_nine": (
            len(list((ROOT / "checkpoints").glob("*_seed_*.pkl"))) == 9
        ),
        "generated_primary_results_present": all(
            (ROOT / "results" / "generated" / name).exists()
            for name in [
                "uniform_pareto.csv",
                "geometry_pareto.csv",
                "surface_pareto.csv",
                "joint_pareto.csv",
                "robustness.csv",
                "jma_daily_evaluation.csv",
            ]
        ),
        "no_primary_result_literals_in_python": not embedded_results,
    }
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "acquisition_status_counts": status_counts,
        "jma_ledger_records": int(len(jma)),
        "canonical_checksum_records": checksum_count,
        "embedded_result_literals": embedded_results,
        "note": (
            "Unavailable historical records are disclosed but are not quantitative "
            "analysis inputs. Final-revision outputs supersede the current manuscript "
            "and package only after Phase 16."
        ),
    }
    (OUTPUT / "provenance_checks.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    if report["status"] != "PASS":
        raise SystemExit(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
