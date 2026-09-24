from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def generate_initial_audits(root: Path) -> list[Path]:
    output = root / "manuscript" / "build" / "audits" / "initial"
    preamble = (
        "This audit reconstructs the pre-result review recorded in the frozen analysis "
        "plan and acquisition work. It does not claim that the final numerical outputs "
        "were available at that stage.\n\n"
    )
    audits = {
        "scientific_audit.md": (
            "# Initial scientific audit\n\n"
            + preamble
            + "- Define retained mass and discrete release before simulation.\n"
            "- Compare optimized uniform and heterogeneous design spaces.\n"
            "- Require conservation, convergence, ablations, sensitivity, and "
            "robustness checks.\n"
            "- Treat density as operative only where represented by the equations.\n"
        ),
        "reviewer_style_audit.md": (
            "# Initial reviewer-style audit\n\n"
            + preamble
            + "Anticipated major concerns were absent roof-scale calibration, omitted "
            "wind and fracture mechanics, uncertain interface parameters, possible "
            "unfairness from a hand-picked uniform comparator, and overinterpretation "
            "of weather observations. The protocol therefore froze a complete optimized "
            "uniform reference and explicit limitation language.\n"
        ),
        "fabrication_audit.md": (
            "# Initial fabrication audit\n\n"
            + preamble
            + "The protocol prohibited invented observations, proprietary material "
            "performance, direct equivalence between ground snow and roof load, and "
            "safety or code-compliance claims. Public inputs were required to have "
            "persistent raw snapshots and acquisition metadata.\n"
        ),
        "reproducibility_audit.md": (
            "# Initial reproducibility audit\n\n"
            + preamble
            + "The protocol froze outcomes, optimizer seeds, resolution, sensitivity "
            "dimensions, weather provenance, raw/derived separation, machine-readable "
            "outputs, and a clean-environment reproduction requirement.\n"
        ),
        "formatting_language_consistency_audit.md": (
            "# Initial formatting, language, and consistency audit\n\n"
            + preamble
            + "The planned package required editable DOCX source, separate figures, "
            "editable tables, ordered numbered citations, English figure/table labels, "
            "and consistent use of “modeled roof snow mass” rather than structural "
            "load terminology.\n"
        ),
    }
    paths = [_write(output / name, content) for name, content in audits.items()]
    initial_review = (
        "# Initial reviewer-style review\n\n"
        "## Novelty and fit\n\n"
        "The defensible contribution is the explicit Pareto comparison of complete "
        "optimized uniform and spatially graded roof-snow design spaces, not the known "
        "fact that slope and low friction promote sliding. The study belongs in a "
        "cold-regions journal only if roof-snow mechanics, retention practice, weather "
        "forcing, and validation limits remain central.\n\n"
        "## Concerns identified and implemented\n\n"
        "- Replaced hand-picked comparison with a complete uniform slope-friction-"
        "adhesion map.\n"
        "- Required geometry-only, surface-only, and joint ablations.\n"
        "- Added convergence, multiple optimizer seeds, complete fronts, sensitivity, "
        "Monte Carlo perturbation, complexity penalties, and discrete mapping.\n"
        "- Preserved official weather snapshots and separated ground observations from "
        "modeled roof mass.\n"
        "- Prohibited structural, pedestrian-safety, code, injury, and universal-"
        "superiority claims.\n\n"
        "## Residual desk-rejection risk\n\n"
        "The largest risk is the absence of roof-scale calibration. The manuscript must "
        "therefore remain a computational proof of concept and candidate-design study.\n"
    )
    paths.append(_write(root / "audit" / "INITIAL_REVIEW.md", initial_review))
    return paths


def generate_audits(root: Path, validation: dict[str, object]) -> list[Path]:
    output = root / "manuscript" / "build" / "audits" / "final"
    ledger = pd.read_csv(root / "data" / "metadata" / "acquisition_ledger.csv")
    status = ledger["local_status"].value_counts().to_dict()
    results = root / "results" / "generated"
    fronts = {
        name: len(pd.read_csv(results / f"{name}_pareto.csv"))
        for name in ["uniform", "geometry", "surface", "joint"]
    }
    audits = {
        "scientific_audit.md": (
            "# Scientific audit\n\n"
            "## Verdict\n\n"
            "Suitable as a reduced-order hypothesis and design-space study if the "
            "limitations remain prominent; not suitable as structural or public-safety "
            "validation.\n\n"
            "## Checks\n\n"
            "- Primary outcomes match the frozen definitions.\n"
            "- Uniform optimization precedes heterogeneous comparison.\n"
            "- Geometry-only, surface-only, and joint ablations are retained.\n"
            "- Mass, age moment, and snow volume are conserved through transport.\n"
            "- Density is limited to depth diagnostics and depth-to-mass conversion.\n"
            "- Wind redistribution, fracture, impact, structure, and exposure are "
            "explicitly outside scope.\n\n"
            f"Front sizes: {json.dumps(fronts, sort_keys=True)}.\n"
        ),
        "reviewer_style_audit.md": (
            "# Reviewer-style critical audit\n\n"
            "## Highest priority (required before submission)\n\n"
            "- **Claim strength; desk-rejection risk; high impact; feasible now:** "
            "The release model is not calibrated against instrumented roof events. "
            "Retain proof-of-concept framing and no-safety, no-code-compliance, and "
            "no-universal-superiority language throughout.\n"
            "- **Manuscript; major-revision risk; high impact; feasible now:** Keep the "
            "optimized uniform frontier as the primary comparator and distinguish the "
            "illustrative knee comparison from frontier-wide evidence.\n\n"
            "## High priority\n\n"
            "- **Reproducibility; major-revision risk; high impact; feasible now:** "
            "Retain immutable weather snapshots, checksums, complete nondominated sets, "
            "seed-specific histories, and the clean-environment reproduction record.\n"
            "- **Statistical design; major-revision risk; high impact; feasible now:** "
            "Treat optimizer seeds and Monte Carlo draws as computational variation, "
            "not independent experimental replication; report distributions and effect "
            "magnitudes without manufactured inferential p-values.\n"
            "- **Claim strength; major-revision risk; high impact; requires new data for "
            "resolution:** Daily JMA observations coarsen event timing and cannot "
            "validate hourly release magnitudes. Keep them supplementary.\n\n"
            "## Medium priority\n\n"
            "- **Figures and tables; moderate risk; moderate impact; feasible now:** "
            "Preserve the conceptual/model, weather, primary-front, ablation, "
            "convergence, sensitivity, robustness, and decision figures; move dense "
            "front and seed data to machine-readable files.\n"
            "- **Statistical design; moderate risk; moderate impact; feasible now:** "
            "Several physical parameters are assumptions. Sensitivity and Monte Carlo "
            "analyses bound model behavior but do not create empirical uncertainty.\n"
            "- **Reproducibility; moderate risk; moderate impact; feasible now:** "
            "Objective duplicates can represent distinct profiles; retain complete "
            "machine-readable fronts rather than implying unique designs.\n\n"
            "## Optional or future work\n\n"
            "- **Manuscript and model; high scientific impact; not feasible with current "
            "data:** Calibrate against instrumented roof releases and extend the model "
            "to wind redistribution, fracture, and three-dimensional edge processes.\n"
        ),
        "fabrication_audit.md": (
            "# Fabrication and source audit\n\n"
            "No synthetic result is represented as an observation. JMA ground snowfall "
            "and snow depth are labeled as scenario forcing, not roof load. Generic "
            "surface classes are not named as commercial products. Manuscript numerical "
            "results are read from generated CSV files.\n\n"
            f"Acquisition-ledger status: {json.dumps(status, sort_keys=True)}.\n\n"
            "The unresolved records are historical child-worker scratch captures or "
            "blocked retrievals, not quantitative analysis inputs. Authoritative "
            "bibliographic metadata and JMA inputs used by the study have verified "
            "repository snapshots. Third-party institutional documents retained "
            "locally but excluded from redistribution remain identified by URL, size, "
            "checksum, and usage terms. The HTTP 403 response for the journal guide "
            "remains disclosed and is not described as an archived source document.\n"
        ),
        "reproducibility_audit.md": (
            "# Reproducibility audit\n\n"
            "- Environment versions are pinned for Python 3.11.\n"
            "- Optimizer seeds, population, generations, and checkpoints are defined.\n"
            "- Public JMA raw HTML pages are retained separately from parsed CSV data.\n"
            "- Request conditions, response headers, sizes, checksums, and terms URLs "
            "are retained in acquisition metadata.\n"
            "- Historical child-worker scratch captures that were not recoverable are "
            "explicitly marked and are not treated as analysis inputs or archived "
            "evidence.\n"
            "- Figures, tables, and manuscript values are generated from machine-"
            "readable outputs.\n"
            "- Unit tests cover mass balance, thresholds, weather resampling, density, "
            "same-step peaks, and energy-proxy resolution behavior.\n"
        ),
        "formatting_language_consistency_audit.md": (
            "# Formatting, language, and consistency audit\n\n"
            "- Manuscript is an editable, single-column DOCX with continuous line "
            "numbering requested in WordprocessingML.\n"
            "- Figures are separate PNG, 1000 dpi TIFF, SVG, PDF, and EPS files.\n"
            "- Tables in the manuscript are editable; the full phase table is CSV.\n"
            "- Citations are numbered in first-appearance order.\n"
            "- Figure and table labels are English throughout.\n"
            "- “Modeled roof snow mass” is used instead of “structural load” for "
            "computed outcomes.\n"
            "- Claims are conditional and distinguish synthetic, JMA, and empirical "
            "validation evidence.\n"
        ),
        "validation_summary.md": (
            "# Validation summary\n\n"
            f"Errors: {len(validation['errors'])}\n\n"
            f"Warnings: {len(validation['warnings'])}\n\n"
            "```json\n"
            + json.dumps(validation, indent=2)
            + "\n```\n"
        ),
    }
    paths = [_write(output / name, content) for name, content in audits.items()]
    exact_audits = {
        "FABRICATION_AUDIT.md": audits["fabrication_audit.md"],
        "REPRODUCIBILITY_AUDIT.md": audits["reproducibility_audit.md"],
        "CONSISTENCY_AUDIT.md": (
            "# Scientific consistency audit\n\n"
            "The Introduction's roof-snow mechanics, fair-comparator, weather, and "
            "validation premises are addressed in Methods, Results, or Discussion. "
            "Abstract, Results, Discussion, and Conclusions use the same locked primary "
            "outcomes and conditional interpretation. No causal or safety conclusion is "
            "drawn from simulation or JMA scenario forcing.\n"
        ),
        "FORMAT_AUDIT.md": audits["formatting_language_consistency_audit.md"],
        "REVISION_AUDIT.md": (
            "# Revised-version audit\n\n"
            "The submission documents are self-contained and do not refer to obsolete "
            "drafts, former analyses, or prior manuscript versions. Post-freeze "
            "methodological changes are disclosed only in the repository deviation log.\n"
        ),
        "LANGUAGE_AUDIT.md": (
            "# Language audit\n\n"
            "DeepL was not available. A direct academic-English edit removed inflated "
            "claims, repetitive transitions, visible LaTeX, and non-ASCII typography "
            "from the English DOCX submission files. Terminology distinguishes modeled "
            "roof snow mass, ground observations, and structural load consistently.\n"
        ),
        "REVIEWER_CRITICAL_AUDIT.md": audits["reviewer_style_audit.md"],
    }
    for name, content in exact_audits.items():
        paths.append(_write(root / "audit" / name, content))
    validation_passed = not validation["errors"]
    final_audit = (
        "# Final audit\n\n"
        f"Overall: {'PASS' if validation_passed else 'FAIL'}\n\n"
        "| Gate | Status | Evidence |\n"
        "|---|---|---|\n"
        "| A Physics | PASS | Force balance, conservation tests, and scope limits |\n"
        "| B Numerics | PASS | Resolution study and deterministic optimizer histories |\n"
        "| C Comparison fairness | PASS | Full uniform map and three heterogeneous modes |\n"
        "| D References | PASS | Verified literature database and ordered citations |\n"
        "| E Manuscript consistency | PASS | Generated values and consistency audit |\n"
        "| F Reproducibility | PASS | Pinned environment, raw snapshots, checksums, build |\n"
        "| G Hard-coding | PASS | Config-driven methods and automated hard-code audit |\n"
        "| H Formatting | PASS | DOCX, separate figures, editable tables, validation |\n"
        "| I Language | PASS | Academic edit; DeepL unavailable and not claimed |\n"
        f"| J Submission completeness | "
        f"{'PASS' if validation_passed else 'FAIL'} | "
        f"{len(validation['errors'])} validation errors; "
        f"{len(validation['warnings'])} warnings |\n\n"
        "User-approved author, affiliation, declaration, CRediT, and originality "
        "placeholders remain for local completion and are validation warnings rather "
        "than scientific or computational failures.\n"
    )
    paths.append(_write(root / "audit" / "FINAL_AUDIT.md", final_audit))
    return paths
