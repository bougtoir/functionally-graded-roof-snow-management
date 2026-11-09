"""R1 supplement, highlights, cover letter and tracked comparison."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml
from docx import Document
from docx.shared import Pt

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
from r1_tracked import build as tracked  # noqa: E402

from graded_roof.manuscript import _add_line_numbering  # noqa: E402

OUT = Path("manuscript/r1")
HIGHLIGHTS = [
    "Physical event metric replaces a timestep-dependent shedding endpoint",
    "Constructability is enforced inside the optimiser by a feasible encoding",
    "Uniform roofs either shed nearly all snow or retain all of it",
    "Graded roofs add intermediate retention-release options in every seed",
    "Frontier-wide gains over uniform roofs are small; no roof validation",
]


def doc_base():
    d = Document()
    d.styles["Normal"].font.name = "Arial"
    d.styles["Normal"].font.size = Pt(10)
    return d


def supplement(path: Path):
    d = doc_base()
    _add_line_numbering(d)
    d.add_heading("Supplementary material", 0)
    d.add_heading("Table S1. Model parameters, classification and evidence status", 1)
    p = pd.read_csv("revision_r1/PHYSICAL_PARAMETER_PROVENANCE.csv")
    cols = ["parameter", "value", "unit", "classification_R1", "evidence_status"]
    t = d.add_table(rows=1, cols=len(cols))
    t.style = "Table Grid"
    for i, c in enumerate(["Parameter", "Value", "Unit", "Classification", "Evidence status"]):
        t.rows[0].cells[i].text = c
    for row in p[cols].itertuples(index=False):
        cells = t.add_row().cells
        for i, x in enumerate(row):
            cells[i].text = str(x)
    d.add_heading("Table S2. Optimisation run diagnostics", 1)
    g = pd.read_csv("results/r1/pareto/run_diagnostics.csv")
    g = g[
        [
            "mode",
            "seed",
            "objective_evaluations",
            "unique_designs_simulated",
            "runtime_s",
            "feasible_fraction",
        ]
    ]
    t = d.add_table(rows=1, cols=len(g.columns))
    t.style = "Table Grid"
    for i, c in enumerate(
        ["Mode", "Seed", "Evaluations", "Unique designs", "Runtime (s)", "Feasible fraction"]
    ):
        t.rows[0].cells[i].text = c
    for row in g.itertuples(index=False):
        cells = t.add_row().cells
        for i, x in enumerate(row):
            cells[i].text = f"{x:.1f}" if isinstance(x, float) else str(x)
    d.add_heading("S3. Data, code and reproduction", 1)
    d.add_paragraph(
        "All tables and figures are regenerated from results/r1 by scripts/r1_*.py (see revision_r1/REPRODUCIBILITY_AUDIT.md). "
        "Raw public sources are stored under data/raw with an acquisition ledger (URL, retrieval time, size, SHA-256)."
    )
    d.save(path)


def cover(path: Path):
    m = yaml.safe_load(open("manuscript/author_metadata.yaml"))
    a = m["authors"][0]
    d = doc_base()
    for t in (
        "Editor, Cold Regions Science and Technology",
        "Re: Revision of manuscript CRST-D-26-01129",
        "Dear Editor,",
        "Thank you for the opportunity to revise the manuscript. In response to the Editor's and reviewers' comments, the analysis was rebuilt "
        "rather than edited: the release endpoint is now a pre-specified physical event metric whose timestep independence was tested on "
        "543 design-winter pairs; constructability is enforced inside the optimiser; uniform, geometry-only, surface-only and joint designs are "
        "compared with equal budgets over five seeds; robustness and observed JMA station-winter scenarios were re-run with the new metric; "
        "and the Japanese heavy-snowfall and Building Standards context is documented from official sources.",
        "The revised results are more limited than the submitted ones. Graded roofs reproducibly provide intermediate retention-release options "
        "that constructable uniform roofs cannot, but frontier-wide gains are small, and the model is numerically verified but not validated "
        "against roof observations. The title, abstract and conclusions were revised accordingly. A point-by-point response and a marked-up "
        "manuscript (additions red, deletions blue strikethrough) are provided.",
        "The work is original and is not under consideration elsewhere. Competing interests: "
        + str(m["competing_interests"])
        + ".",
        "Sincerely,",
        a["name"],
        a["affiliation"],
        a["email"],
    ):
        d.add_paragraph(t)
    d.save(path)


def editable_tables(src: Path, path: Path):
    """Copy every manuscript table (with its caption) into a standalone editable docx."""
    import copy

    s = Document(src)
    d = doc_base()
    body = s.element.body
    for el in body.iterchildren():
        if el.tag.endswith("}tbl"):
            prev = el.getprevious()
            d.element.body.append(copy.deepcopy(prev))
            d.element.body.append(copy.deepcopy(el))
            d.add_paragraph()
    d.save(path)


def editable_figures(captions: list[str], path: Path):
    from PIL import Image
    from pptx import Presentation
    from pptx.util import Inches
    from pptx.util import Pt as PPt

    sys.path.insert(0, "scripts")
    from r1_build_manuscript import FIGS

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for name, cap in zip(FIGS, captions, strict=True):
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        tb = sl.shapes.add_textbox(Inches(0.4), Inches(0.2), Inches(12.5), Inches(0.6))
        tb.text_frame.text = cap.split(".")[0]
        tb.text_frame.paragraphs[0].runs[0].font.size = PPt(20)
        img = Path("figures/r1/png") / f"{name}.png"
        w, h = Image.open(img).size
        scale = min(12.5 / (w / 1000), 5.4 / (h / 1000))
        ww, hh = w / 1000 * scale, h / 1000 * scale
        sl.shapes.add_picture(
            str(img), Inches((13.333 - ww) / 2), Inches(0.9), Inches(ww), Inches(hh)
        )
        cb = sl.shapes.add_textbox(Inches(0.4), Inches(6.5), Inches(12.5), Inches(0.9))
        cb.text_frame.word_wrap = True
        cb.text_frame.text = cap
        cb.text_frame.paragraphs[0].runs[0].font.size = PPt(12)
    prs.save(path)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    assert all(len(h) <= 85 for h in HIGHLIGHTS), [len(h) for h in HIGHLIGHTS]
    (OUT / "highlights_R1.txt").write_text("\n".join(f"- {h}" for h in HIGHLIGHTS) + "\n")
    supplement(OUT / "supplementary_material_R1.docx")
    cover(OUT / "cover_letter_R1.docx")
    clean = OUT / "manuscript_R1_clean.docx"
    caps = [
        par.text
        for par in Document(clean).paragraphs
        if par.text.startswith("Figure ") and par.style.name == "Normal"
    ][-8:]
    editable_tables(clean, OUT / "editable_tables_R1.docx")
    editable_figures(caps, OUT / "editable_figures_R1.pptx")
    print(
        tracked(
            Path("revision_r1/baseline/manuscript_CRST_submitted_v1.docx"),
            OUT / "manuscript_R1_clean.docx",
            OUT / "manuscript_R1_tracked.docx",
        )
    )
