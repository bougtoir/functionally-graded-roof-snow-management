from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PHASES = [
    ("00", "Bootstrap and target journal", ["README.md", "analysis_plan.md"]),
    (
        "01",
        "Literature and parameter provenance",
        ["references/literature_database.csv", "references/parameter_sources.csv"],
    ),
    ("02", "Physics and unit tests", ["src/graded_roof/simulation.py", "tests"]),
    (
        "03",
        "Synthetic weather and fair baselines",
        ["results/generated/baseline_aggregate.csv"],
    ),
    ("04", "Numerical convergence", ["results/generated/convergence.csv"]),
    ("05", "Optimized uniform space", ["results/generated/uniform_pareto.csv"]),
    ("06", "Heterogeneous optimization", ["results/generated/joint_pareto.csv"]),
    (
        "07",
        "Ablation",
        [
            "results/generated/geometry_pareto.csv",
            "results/generated/surface_pareto.csv",
        ],
    ),
    (
        "08",
        "Complexity and discrete materials",
        [
            "tables/generated/table_6_complexity_analysis.csv",
            "tables/generated/table_7_complexity_penalty.csv",
        ],
    ),
    ("09", "Sensitivity", ["results/generated/sensitivity.csv"]),
    (
        "10",
        "Robustness",
        [
            "results/generated/robustness.csv",
            "results/generated/robustness_summary.csv",
        ],
    ),
    ("11", "Japanese weather", ["results/generated/jma_daily_evaluation.csv"]),
    (
        "12",
        "Strategy phase diagram",
        ["tables/generated/table_4_strategy_phase_diagram.csv"],
    ),
    ("13", "Labor scarcity", ["tables/generated/table_5_labor_scarcity.csv"]),
    (
        "14",
        "Secondary outcomes",
        ["results/generated/baseline_scenarios.csv"],
    ),
    ("15", "Figures and tables", ["figures/png", "tables/generated"]),
    (
        "16",
        "Manuscript and submission files",
        [
            "manuscript/manuscript_CRST_submission_final.docx",
            "submission/CRST_submission_package_FINAL.zip",
        ],
    ),
    ("17", "Initial review", ["audit/INITIAL_REVIEW.md"]),
    ("18", "Mandatory final QC", ["audit/FINAL_AUDIT.md"]),
]


def main() -> None:
    state_path = ROOT / "PROJECT_STATE.json"
    previous_state = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists()
        else {}
    )
    handoff_directory = ROOT / "handoffs"
    handoff_directory.mkdir(parents=True, exist_ok=True)
    phases = []
    for number, name, relative_paths in PHASES:
        evidence = [ROOT / relative_path for relative_path in relative_paths]
        complete = all(path.exists() for path in evidence)
        status = "completed" if complete else "pending"
        phases.append(
            {
                "phase": number,
                "name": name,
                "status": status,
                "evidence": relative_paths,
            }
        )
        content = (
            f"# Phase {number} handoff: {name}\n\n"
            f"Status: {status}\n\n"
            "This handoff is regenerated from persistent repository artifacts; it does "
            "not rely on hidden session state.\n\n"
            "## Evidence\n\n"
            + "".join(
                f"- `{relative_path}`: "
                f"{'present' if path.exists() else 'missing'}\n"
                for relative_path, path in zip(
                    relative_paths,
                    evidence,
                    strict=True,
                )
            )
            + "\n## Unresolved items\n\n"
            + (
                "None at this phase gate.\n"
                if complete
                else "One or more evidence paths are not yet present.\n"
            )
        )
        (handoff_directory / f"PHASE_{number}_HANDOFF.md").write_text(
            content,
            encoding="utf-8",
        )
    state = {
        "updated_utc": datetime.now(UTC).isoformat(),
        "research_question": (
            "How spatial variation in roof geometry and snow-surface interaction "
            "changes the modeled retained-load versus shedding-event trade-off."
        ),
        "phases": phases,
        "completed_phases": sum(phase["status"] == "completed" for phase in phases),
        "total_phases": len(phases),
    }
    if "final_revision" in previous_state:
        state["final_revision"] = previous_state["final_revision"]
    state_path.write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
