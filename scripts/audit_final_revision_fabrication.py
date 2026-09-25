from __future__ import annotations

import re
import shutil
from pathlib import Path

import pandas as pd
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "generated"
OUTPUT = ROOT / "audit" / "FABRICATION_AUDIT.md"
REFERENCE_OUTPUT = ROOT / "references" / "reference_audit.csv"


def expand_numbered_mentions(text: str, label: str) -> list[int]:
    numbers: list[int] = []
    pattern = re.compile(rf"\b{label}s?\s+(\d+)(?:-(\d+))?")
    for match in pattern.finditer(text):
        start = int(match.group(1))
        end = int(match.group(2) or start)
        numbers.extend(range(start, end + 1))
    return numbers


def first_unique(values: list[int]) -> list[int]:
    output: list[int] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def formatted(value: float, digits: int) -> str:
    return f"{value:.{digits}f}"


def citation_author(entry: str) -> str:
    if " et al." in entry:
        return entry.split()[0] + " et al."
    parts = entry.split()
    if len(parts) == 2 and parts[1].isupper():
        return parts[0]
    return entry


def citation_label(row: pd.Series) -> str:
    authors = [
        citation_author(entry.strip())
        for entry in str(row["authors"]).split(";")
    ]
    if len(authors) == 1:
        author_text = authors[0]
    elif len(authors) == 2:
        author_text = f"{authors[0]} and {authors[1]}"
    else:
        author_text = f"{authors[0]} et al."
    return f"{author_text}, {int(row['year'])}"


def main() -> None:
    manuscript = Document(ROOT / "manuscript" / "manuscript_CRST.docx")
    paragraphs = [paragraph.text for paragraph in manuscript.paragraphs]
    reference_index = paragraphs.index("References")
    editable_index = paragraphs.index("Editable tables")
    body = "\n".join(paragraphs[:reference_index])
    reference_text = "\n".join(paragraphs[reference_index + 1 : editable_index])

    figure_mentions = expand_numbered_mentions(body, "Figure")
    table_mentions = expand_numbered_mentions(body, "Table")
    reference_audit = pd.read_csv(
        ROOT / "references" / "final_revision_reference_audit.csv"
    )
    reference_audit["citation_label"] = reference_audit.apply(
        citation_label,
        axis=1,
    )
    alphabetical_references = reference_audit.assign(
        sort_author=reference_audit["authors"].str.casefold()
    ).sort_values(["sort_author", "year", "record_id"])
    manuscript_title_order = sorted(
        (
            reference_text.index(row.title),
            row.record_id,
        )
        for row in reference_audit.itertuples(index=False)
    )
    manuscript_reference_ids = [
        record_id for _, record_id in manuscript_title_order
    ]
    expected_reference_ids = alphabetical_references["record_id"].tolist()
    number_provenance = pd.read_csv(
        ROOT / "audit" / "final_revision" / "number_provenance.csv"
    )
    provenance_paths = [
        ROOT / item.strip()
        for source in number_provenance["canonical_source"]
        for item in source.split(";")
    ]
    shutil.copyfile(
        ROOT / "references" / "final_revision_reference_audit.csv",
        REFERENCE_OUTPUT,
    )

    frontier = pd.read_csv(
        RESULTS / "final_revision_frontier_summary.csv"
    ).set_index("design_class")
    metric = pd.read_csv(
        RESULTS / "final_revision_frontier_metric_sensitivity.csv"
    )
    metric = metric.loc[
        metric["normalization_origin"].eq("zero")
        & metric["reference_margin"].eq(1.05)
    ].set_index("design_class")
    knee = pd.read_csv(RESULTS / "final_revision_knee_audit.csv")
    joint_knee = knee.loc[
        knee["design_class"].eq("joint")
        & knee["normalization"].eq("front_specific_minmax")
    ].iloc[0]
    robustness = pd.read_csv(
        RESULTS / "final_revision_objective_equivalent_robustness.csv"
    )
    largest_equivalent_group = robustness.sort_values(
        "candidate_count", ascending=False
    ).iloc[0]
    ties = pd.read_csv(RESULTS / "final_revision_robust_selection_ties.csv")
    mapping = pd.read_csv(
        RESULTS / "final_revision_discretization_loss.csv"
    ).iloc[0]
    timestep = pd.read_csv(
        RESULTS / "final_revision_selected_design_timestep_audit.csv"
    )
    jma = pd.read_csv(RESULTS / "final_revision_jma_paired_tradeoffs.csv")

    expected_fragments = {
        "uniform objective-pair count": (
            f"only {int(frontier.loc['uniform', 'unique_objective_pairs'])} "
            "objective pairs"
        ),
        "joint objective-pair count": (
            f"joint set contained "
            f"{int(frontier.loc['joint', 'unique_objective_pairs'])}"
        ),
        "uniform hypervolume": formatted(
            metric.loc["uniform", "normalized_hypervolume_fraction"], 3
        ),
        "joint hypervolume": formatted(
            metric.loc["joint", "normalized_hypervolume_fraction"], 3
        ),
        "joint descriptive knee Lmax": formatted(
            joint_knee["l_max_kg_per_m"], 1
        ),
        "joint descriptive knee Smax": formatted(
            joint_knee["s_max_kg_per_m"], 2
        ),
        "robustness Q95 Lmax lower bound": formatted(
            largest_equivalent_group["q95_l_min_kg_per_m"], 1
        ),
        "robustness Q95 Lmax upper bound": formatted(
            largest_equivalent_group["q95_l_max_kg_per_m"], 1
        ),
        "robustness tie count": f"shared by {len(ties)} candidates",
        "mapping Lmax percent": formatted(mapping["l_max_percent_change"], 2),
        "mapping Smax percent": formatted(mapping["s_max_percent_change"], 2),
        "JMA Lmax ratio minimum": formatted(
            jma["joint_to_uniform_l_max_ratio"].min(), 2
        ),
        "JMA Lmax ratio maximum": formatted(
            jma["joint_to_uniform_l_max_ratio"].max(), 2
        ),
        "JMA Smax reduction minimum": formatted(
            jma["s_max_reduction_percent"].min(), 2
        ),
        "JMA Smax reduction maximum": formatted(
            jma["s_max_reduction_percent"].max(), 2
        ),
    }
    fragment_checks = {
        name: fragment in body for name, fragment in expected_fragments.items()
    }

    production = timestep.loc[timestep["dt_hours"].eq(1.0)]
    checks = {
        "figures 1-9 cited in order": (
            first_unique(figure_mentions) == list(range(1, 10))
        ),
        "tables 1-9 cited in order": (
            first_unique(table_mentions) == list(range(1, 10))
        ),
        "nine figure captions present": sum(
            bool(re.match(r"^Figure \d+\.", text)) for text in paragraphs
        )
        == 9,
        "nine table captions present": sum(
            bool(re.match(r"^Table \d+(?:\.| \()", text))
            for text in paragraphs
        )
        == 9,
        "references use CRST author-year style": (
            not re.search(r"^\d+\.", reference_text, flags=re.MULTILINE)
            and not re.search(r"\[\d+(?:[-–,]\d+)*\]", body)
        ),
        "all listed references cited": (
            reference_audit["citation_label"].map(
                lambda label: label in body
            ).all()
        ),
        "reference list is alphabetical": (
            manuscript_reference_ids == expected_reference_ids
        ),
        "reference audit rows match manuscript references": (
            len(reference_audit) == len(manuscript_reference_ids)
            and len(set(manuscript_reference_ids)) == len(reference_audit)
        ),
        "reference snapshots verified": (
            reference_audit["source_local_status"].eq("verified").all()
        ),
        "reference titles verified": (
            reference_audit["title_verification_status"]
            .isin(["exact", "verified_metadata_variant"])
            .all()
        ),
        "reference years verified": (
            reference_audit["year_matches_snapshot"].astype(bool).all()
        ),
        "reference claims and transfer limits populated": (
            reference_audit["claim_supported"].notna().all()
            and reference_audit["transfer_limit"].notna().all()
        ),
        "all audited headline fragments present": all(fragment_checks.values()),
        "number-provenance rows are verified": (
            number_provenance["status"].eq("verified").all()
        ),
        "number-provenance sources exist": all(
            path.exists() for path in provenance_paths
        ),
        "all three production-timestep designs fail": (
            len(production) == 3 and not production["within_tolerance"].any()
        ),
        "Lmax is defined as modeled mass rather than structural load": (
            "modeled unit-width masses, not structural loads" in body
        ),
        "Smax is defined with its timestep": (
            "Smax is release mass in one model interval" in body
        ),
        "JMA is framed as scenario forcing": (
            "supplementary forcing, not roof-scale validation" in body
        ),
        "robustness intervals are not empirical confidence intervals": (
            "not interpreted as empirical confidence intervals" in body
        ),
    }

    lines = [
        "# Fabrication, numerical, and reference audit",
        "",
        f"Overall status: {'PASS' if all(checks.values()) else 'FAIL'}",
        "",
        "## Audit gates",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    lines.extend(
        f"| {name} | {'PASS' if passed else 'FAIL'} |"
        for name, passed in checks.items()
    )
    lines.extend(
        [
            "",
            "## Headline-number trace",
            "",
            "| Quantity | Canonical value fragment | Manuscript match |",
            "|---|---:|---|",
        ]
    )
    lines.extend(
        f"| {name} | {fragment} | {'PASS' if fragment_checks[name] else 'FAIL'} |"
        for name, fragment in expected_fragments.items()
    )
    lines.extend(
        [
            "",
            "## Reference audit",
            "",
            f"- Manuscript references: {len(manuscript_reference_ids)}.",
            f"- Verified reference snapshots: {len(reference_audit)}.",
            "- Each audited record contains its supported claim, transfer limit, "
            "local snapshot path, and SHA-256.",
            f"- Machine-readable output: `{REFERENCE_OUTPUT.relative_to(ROOT)}`.",
            "",
            "## Interpretation",
            "",
            "- No synthetic output is represented as an observation.",
            "- JMA ground observations are scenario forcing, not roof-load or "
            "roof-shedding validation.",
            "- Generic mapped surface classes are not commercial product claims.",
            "- Monte Carlo quantiles are conditional model outputs, not empirical "
            "confidence intervals.",
            "- The 1-h production frontier remains explicitly qualified by the failed "
            "four-metric convergence criterion.",
        ]
    )
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"fabrication audit failed: {failed}")


if __name__ == "__main__":
    main()
