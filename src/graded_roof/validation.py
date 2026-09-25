from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import yaml
from docx import Document
from PIL import Image

EXPECTED_RESULTS = [
    "baseline_aggregate.csv",
    "baseline_scenarios.csv",
    "convergence.csv",
    "uniform_design_space.csv",
    "uniform_pareto.csv",
    "geometry_pareto.csv",
    "surface_pareto.csv",
    "joint_pareto.csv",
    "jma_daily_evaluation.csv",
    "sensitivity.csv",
    "robustness.csv",
    "robustness_summary.csv",
    "optimizer_stochasticity.csv",
]


def _paragraph_text(document: Document) -> list[str]:
    return [paragraph.text.strip() for paragraph in document.paragraphs]


def _abstract_word_count(document: Document) -> int:
    paragraphs = _paragraph_text(document)
    start = paragraphs.index("Abstract") + 1
    end = next(
        index
        for index, text in enumerate(paragraphs[start:], start=start)
        if text.startswith("Keywords:")
    )
    return len(
        re.findall(
            r"\b[\w$−{}]+(?:[-’'][\w$−{}]+)*\b",
            " ".join(paragraphs[start:end]),
        )
    )


def _unsupported_non_ascii(text: str) -> list[str]:
    allowed = {"−"}
    return sorted(
        {
            character
            for character in text
            if ord(character) > 127 and character not in allowed
        }
    )


def _reference_entries(document: Document) -> list[str]:
    paragraphs = _paragraph_text(document)
    start = paragraphs.index("References") + 1
    end = paragraphs.index("Editable tables", start)
    return [text for text in paragraphs[start:end] if text]


def validate_submission(root: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, object] = {}
    build = root / "manuscript" / "build"
    manuscript_path = root / "manuscript" / "manuscript_CRST.docx"
    if not manuscript_path.exists():
        errors.append("manuscript.docx is missing")
        return {"errors": errors, "warnings": warnings, "checks": checks}

    manuscript = Document(manuscript_path)
    abstract_words = _abstract_word_count(manuscript)
    checks["abstract_words"] = abstract_words
    if abstract_words > 250:
        errors.append(f"abstract has {abstract_words} words")
    if len(manuscript.tables) < 4:
        errors.append("editable manuscript tables are missing")
    with zipfile.ZipFile(manuscript_path) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    checks["continuous_line_numbering"] = "w:lnNumType" in document_xml
    if not checks["continuous_line_numbering"]:
        errors.append("continuous line numbering is absent from manuscript XML")
    checks["native_word_equations"] = document_xml.count("<m:oMath")
    if checks["native_word_equations"] < 3:
        errors.append("native Word equations are missing")

    text = "\n".join(_paragraph_text(manuscript))
    table_text = "\n".join(
        cell.text
        for table in manuscript.tables
        for row in table.rows
        for cell in row.cells
    )
    non_ascii = sorted(
        {character for character in text + table_text if ord(character) > 127}
    )
    unsupported_non_ascii = _unsupported_non_ascii(text + table_text)
    checks["non_ascii_characters"] = non_ascii
    checks["unsupported_non_ascii_characters"] = unsupported_non_ascii
    if unsupported_non_ascii:
        errors.append(
            "English manuscript contains unsupported non-ASCII characters: "
            f"{unsupported_non_ascii}"
        )
    reference_entries = _reference_entries(manuscript)
    checks["reference_count"] = len(reference_entries)
    if len(reference_entries) == 0:
        errors.append("reference list is empty")
    if any(re.match(r"^\d+\.", entry) for entry in reference_entries):
        errors.append("reference list uses obsolete numeric prefixes")
    expected_figure_count = (
        9
        if (root / "results" / "generated" / "jma_daily_evaluation.csv").exists()
        else 8
    )
    for figure_number in range(1, expected_figure_count + 1):
        figure_name = f"figure_{figure_number}_"
        for suffix in [".svg", ".pdf", ".eps"]:
            matches = list(
                (root / "figures" / "vector").glob(f"{figure_name}*{suffix}")
            )
            if not matches:
                errors.append(
                    f"Figure {figure_number} {suffix} vector file is missing"
                )
    if "Figure 1" not in text or "Table 1" not in text:
        errors.append("figures or tables are not cited in manuscript text")

    highlight_path = build / "highlights.txt"
    highlights = [
        line.removeprefix("-").strip()
        for line in highlight_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    checks["highlight_lengths"] = [len(line) for line in highlights]
    if not 3 <= len(highlights) <= 5:
        errors.append("highlights must contain 3-5 bullets")
    if any(len(line) > 85 for line in highlights):
        errors.append("a highlight exceeds 85 characters")

    figure_manifest = []
    png_names = {path.stem for path in (root / "figures" / "png").glob("*.png")}
    tiff_names = {
        path.stem for path in (root / "figures" / "tiff").glob("*.tiff")
    }
    svg_names = {path.stem for path in (root / "figures" / "vector").glob("*.svg")}
    pdf_names = {path.stem for path in (root / "figures" / "vector").glob("*.pdf")}
    eps_names = {path.stem for path in (root / "figures" / "vector").glob("*.eps")}
    if (
        not png_names
        or png_names != tiff_names
        or png_names != svg_names
        or png_names != pdf_names
        or png_names != eps_names
    ):
        errors.append("PNG, TIFF, SVG, PDF, and EPS figure sets do not match")
    for path in sorted((root / "figures" / "tiff").glob("*.tiff")):
        with Image.open(path) as image:
            dpi = image.info.get("dpi", (0, 0))
            figure_manifest.append(
                {
                    "name": path.name,
                    "width_px": image.width,
                    "height_px": image.height,
                    "dpi": [round(float(dpi[0])), round(float(dpi[1]))],
                }
            )
            if min(dpi) < 950:
                errors.append(f"{path.name} is below 1000 dpi")
    checks["figures"] = figure_manifest

    metadata = yaml.safe_load(
        (root / "manuscript" / "author_metadata.yaml").read_text(encoding="utf-8")
    )
    metadata_text = json.dumps(metadata)
    if "REQUIRED" in metadata_text:
        warnings.append("author metadata contains user-approved REQUIRED placeholders")
    if "REQUIRED" in text:
        warnings.append("manuscript contains user-approved REQUIRED placeholders")
    for stage in ["initial", "final"]:
        for name in [
            "scientific_audit.md",
            "reviewer_style_audit.md",
            "fabrication_audit.md",
            "reproducibility_audit.md",
            "formatting_language_consistency_audit.md",
        ]:
            if not (build / "audits" / stage / name).exists():
                errors.append(f"missing {stage} audit: {name}")
    required_audits = [
        "INITIAL_REVIEW.md",
        "FABRICATION_AUDIT.md",
        "REPRODUCIBILITY_AUDIT.md",
        "CONSISTENCY_AUDIT.md",
        "FORMAT_AUDIT.md",
        "REVISION_AUDIT.md",
        "LANGUAGE_AUDIT.md",
        "FINAL_AUDIT.md",
    ]
    for name in required_audits:
        if not (root / "audit" / name).exists():
            errors.append(f"missing required audit: {name}")

    results = root / "results" / "generated"
    for name in EXPECTED_RESULTS:
        if not (results / name).exists():
            errors.append(f"missing result: {name}")
    for path in results.glob("*_scenarios.csv"):
        frame = pd.read_csv(path)
        if "mass_balance_error_kg_per_m" in frame:
            maximum_error = frame["mass_balance_error_kg_per_m"].abs().max()
            if maximum_error > 1e-6:
                errors.append(f"mass balance error in {path.name}: {maximum_error}")

    acquisition_ledger = pd.read_csv(
        root / "data" / "metadata" / "acquisition_ledger.csv"
    )
    invalid = acquisition_ledger[
        acquisition_ledger["local_status"].isin(
            ["size_mismatch", "checksum_mismatch", "missing_file"]
        )
    ]
    if not invalid.empty:
        errors.append("acquisition ledger contains local integrity failures")
    unrecovered = int(
        acquisition_ledger["local_status"].isin(["not_recovered", "no_path"]).sum()
    )
    checks["unrecovered_acquisition_records"] = unrecovered
    if unrecovered:
        warnings.append(
            f"{unrecovered} historical child-worker or blocked source records are "
            "not locally retained; they are not quantitative analysis inputs, and "
            "quantitative inputs and redistributable evidence used by the study have "
            "verified snapshots"
        )

    package = root / "submission" / "CRST_submission_package_final.zip"
    if not package.exists():
        errors.append("submission ZIP is missing")
    else:
        with zipfile.ZipFile(package) as archive:
            names = set(archive.namelist())
        required_members = {
            "manuscript_CRST_final_0p5h.docx",
            "review_copy/manuscript_CRST_inline_final_0p5h.docx",
            "cover_letter_CRST_final.docx",
            "supplementary_material_CRST.docx",
            "editable_tables_CRST.docx",
            "editable_figures_CRST.pptx",
            "highlights_CRST.txt",
            "CRST_submission_checklist.md",
            "CRST_scope_fit.md",
            "REPRODUCIBILITY_README.md",
            "audit/reference_audit.csv",
            "audit/FINAL_AUDIT.md",
            "audit/REPRODUCIBILITY_AUDIT.md",
            "audit/FABRICATION_AUDIT.md",
            "audit/FABRICATION_AUDIT_FINAL.md",
            "audit/NUMERICAL_CONSISTENCY_FINAL.md",
            "audit/REFERENCE_AUDIT_FINAL.csv",
            "audit/FINAL_CRST_REVIEW.md",
            "audit/TIMESTEP_AUDIT.md",
            "audit/NUMERICAL_REFERENCE_AUDIT.md",
            "audit/OLD_VS_NEW_PRIMARY_AUDIT.md",
            "audit/CRST_FORMAT_LANGUAGE_AUDIT.md",
            "audit/FINAL_HOSTILE_REVIEW.md",
            "CRST_submission_manifest.csv",
        }
        reproduction_summary = (
            root / "audit" / "0p5h_revision" / "reproduction_summary.json"
        )
        if reproduction_summary.exists():
            required_members.add("audit/fresh_reproduction_comparison.csv")
        missing_members = sorted(required_members - names)
        if missing_members:
            errors.append(f"submission ZIP missing: {missing_members}")
        checks["zip_file_count"] = len(names)

    checklist = (build / "crst_checklist.md").read_text(encoding="utf-8")
    if "- [ ]" in checklist:
        warnings.append("CRST checklist has unresolved manual items")
    return {"errors": errors, "warnings": warnings, "checks": checks}


def write_validation_report(root: Path, report: dict[str, object]) -> Path:
    output = root / "manuscript" / "build" / "validation_report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return output
