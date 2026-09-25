from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PHASES = [
    ("00", "Inventory and freeze"),
    ("01", "Hostile CRST review"),
    ("02", "Reproducibility and provenance"),
    ("03", "Primary Pareto audit"),
    ("04", "Knee and matched trade-offs"),
    ("05", "Robustness"),
    ("06", "Complexity and constructability"),
    ("07", "JMA scenarios"),
    ("08", "Non-shedding roofs and literature"),
    ("09", "Targeted corrective analysis"),
    ("10", "Manuscript revision"),
    ("11", "Figures and tables"),
    ("12", "Fabrication, numerical, and reference audit"),
    ("13", "Format and language"),
    ("14", "Fresh reproducibility"),
    ("15", "Final hostile review"),
    ("16", "CRST package"),
]


def main() -> None:
    state_path = ROOT / "PROJECT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    handoff_directory = ROOT / "handoffs" / "final_revision"
    phases = []
    for number, name in PHASES:
        handoff = handoff_directory / f"PHASE_{number}_HANDOFF.md"
        phases.append(
            {
                "phase": number,
                "name": name,
                "status": "completed" if handoff.exists() else "pending",
                "evidence": [str(handoff.relative_to(ROOT))],
            }
        )
    state["updated_utc"] = datetime.now(UTC).isoformat()
    state["final_revision"] = {
        "source_prompt": "Devin_CRST_final_revision_hostile_review_one_shot.txt",
        "phases": phases,
        "completed_phases": sum(phase["status"] == "completed" for phase in phases),
        "total_phases": len(phases),
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
