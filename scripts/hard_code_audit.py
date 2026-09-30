from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    pipeline = (ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
    manuscript = (ROOT / "src" / "graded_roof" / "manuscript.py").read_text(
        encoding="utf-8"
    )
    study = (ROOT / "src" / "graded_roof" / "study.py").read_text(encoding="utf-8")
    checks = {
        "baseline_parameters_are_config_driven": not re.search(
            r"uniform_design\(\s*config,\s*\d+(?:\.\d+)?",
            pipeline,
        ),
        "manuscript_has_no_literal_latex": "$L_{" not in manuscript
        and "$S_{" not in manuscript,
        "manuscript_method_counts_are_config_driven": not any(
            phrase in manuscript
            for phrase in [
                "An 8 m long",
                "represented by 24 ridge",
                "A full 30",
                "population of 48",
                "used 250 deterministic",
            ]
        ),
        "generated_results_not_embedded_in_source": not re.search(
            r"Lmax\s*=\s*\d+(?:\.\d+)?",
            manuscript,
        ),
        "ablation_reference_is_config_driven": (
            'config["baselines"]["uniform_intermediate"]' in study
        ),
    }
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "scope": (
            "Automated guard against embedding baseline parameters, optimizer settings, "
            "or generated primary results in executable manuscript and pipeline source."
        ),
    }
    output = ROOT / "audit" / "HARD_CODE_AUDIT.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "PASS":
        raise SystemExit(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
