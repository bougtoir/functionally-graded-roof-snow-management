"""Automated text/figure/table consistency checks for the R1 package."""

from __future__ import annotations

import re
from pathlib import Path

import docx
import pandas as pd
import pptx
from PIL import Image

M = Path("manuscript/r1")
R = Path("results/r1")
FIG = Path("figures/r1")
OUT = Path("revision_r1/TEXT_FIGURE_TABLE_CONSISTENCY.md")
FIGS = [
    "figure_1_model_and_events",
    "figure_2_synthetic_forcing",
    "figure_3_timestep_convergence",
    "figure_4_constructable_pareto_fronts",
    "figure_5_intermediate_profiles",
    "figure_6_search_budget_hypervolume",
    "figure_7_robustness_q95",
    "figure_8_jma_station_winters",
]


def first_order(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def body_text(d) -> list[str]:
    out = []
    for p in d.paragraphs:
        if p.style.name.startswith("Heading") and p.text.strip() == "References":
            break
        out.append(p.text)
    return out


def tracked_kept_text(path: Path) -> list[str]:
    d = docx.Document(path)
    out = []
    for p in d.paragraphs:
        kept = "".join(r.text for r in p.runs if not r.font.strike)
        if p.text.strip() and not kept.strip():
            continue
        out.append(re.sub(r"\s+", " ", kept).strip())
    return [t for t in out if t]


def fmt0(x):
    return f"{x:,.0f}"


def fmt1(x):
    return f"{x:,.1f}"


def main() -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), str(detail)))

    d = docx.Document(M / "manuscript_R1_clean.docx")
    paras = [p.text for p in d.paragraphs]
    body = body_text(d)
    text = "\n".join(body)
    i = next(k for k, p in enumerate(paras) if p.strip() == "Abstract")
    aw = len(paras[i + 1].split())
    chk("Abstract <= 250 words", aw <= 250, f"{aw} words")
    hl = [
        h.lstrip("- ").strip()
        for h in (M / "highlights_R1.txt").read_text().splitlines()
        if h.strip()
    ]
    chk("3-5 highlights", 3 <= len(hl) <= 5, len(hl))
    chk("Highlights <= 85 characters", all(len(h) <= 85 for h in hl), [len(h) for h in hl])
    chk("Continuous line numbering", bool(d.sections[0]._sectPr.xpath("./w:lnNumType")))
    chk(
        "Native OMML equations",
        len(d.element.xpath("//m:oMath")) >= 3,
        len(d.element.xpath("//m:oMath")),
    )
    for pat, lab in (
        (r"\$", "$"),
        (r"\^\{", "^{"),
        (r"_\{", "_{"),
        (r"\\[a-zA-Z]+", "backslash command"),
        (r"\bnan\b", "nan"),
    ):
        hits = [p[:60] for p in paras if re.search(pat, p)]
        chk(f"No visible '{lab}' in text", not hits, hits[:2])
    req = [p[:60] for p in paras if "REQUIRED" in p]
    chk("No REQUIRED placeholders (author input)", not req, f"{len(req)} open: {req}")
    figs = [int(x) for x in re.findall(r"Figs?\. (\d+)", text)]
    tabs = [
        int(x)
        for x in re.findall(
            r"Tables? (\d+)", "\n".join(t for t in body if not t.startswith("Table "))
        )
    ]
    chk("Figures cited 1..8 in order", first_order(figs) == list(range(1, 9)), first_order(figs))
    chk("Tables cited 1..3 in order", first_order(tabs) == [1, 2, 3], first_order(tabs))
    chk("8 inline figures", len(d.inline_shapes) == 8, len(d.inline_shapes))
    pos = []
    for k, p in enumerate(d.paragraphs):
        if p._p.xpath(".//w:drawing"):
            pos.append(k)
    first_cite = []
    for n in range(1, 9):
        first_cite.append(
            next(
                k
                for k, p in enumerate(d.paragraphs)
                if re.search(rf"Fig\. {n}[a-z]?\b", p.text) and not p.text.startswith("Figure")
            )
        )
    chk(
        "Each figure placed after its first citation",
        all(a > b for a, b in zip(pos, first_cite, strict=True)),
        list(zip(first_cite, pos, strict=True)),
    )
    chk("3 inline tables", len(d.tables) == 3, len(d.tables))
    for name in FIGS:
        files = [
            FIG / "png" / f"{name}.png",
            FIG / "tiff" / f"{name}.tiff",
            FIG / "vector" / f"{name}.pdf",
            FIG / "vector" / f"{name}.svg",
        ]
        im = Image.open(files[1])
        chk(
            f"{name}: PNG/TIFF/PDF/SVG + data CSV",
            all(f.exists() for f in files) and (R / "figure_data" / f"{name}.csv").exists(),
        )
        chk(
            f"{name}: TIFF RGB >= 1000 dpi",
            im.mode == "RGB" and min(im.info.get("dpi", (0, 0))) >= 999,
            f"{im.mode} {im.info.get('dpi')}",
        )
    ra = pd.read_csv("revision_r1/REFERENCE_AUDIT_R1.csv")
    chk(
        "All references cited; Vancouver first-appearance order",
        ra.cited_in_text.all() and ra.order_of_first_appearance_ok.all(),
        f"{len(ra)} refs",
    )
    # numbers in text vs canonical CSVs
    fs = pd.read_csv(R / "pareto/front_summary.csv").set_index("set")
    gap = pd.read_csv(R / "pareto/uniform_gap_coverage.csv")
    rcs = pd.read_csv(R / "robustness/robustness_class_summary.csv").set_index("class")
    conv = pd.read_csv(R / "convergence/convergence_summary.csv")
    js = pd.read_csv(R / "jma/jma_station_summary.csv")
    expected = {
        "uniform HV": f"{fs.loc['uniform', 'hv_max_x1.1']:.3f}",
        "joint HV": f"{fs.loc['joint', 'hv_max_x1.1']:.3f}",
        "uniform gap lower L": fmt1(gap.uniform_gap_lo.iloc[0]),
        "uniform gap upper L": fmt0(gap.uniform_gap_hi.iloc[0]),
        "robust intermediate Q95 S max": fmt0(rcs.loc["graded_intermediate", "q95_s_max"]),
        "robust intermediate Q95 S median": fmt0(rcs.loc["graded_intermediate", "q95_s_median"]),
        "convergence pairs": str(int(conv.pairs.max())),
        "JMA graded gap S max": fmt1(js.gap_s_event_max.max()),
    }
    for k, v in expected.items():
        chk(f"Text contains canonical value: {k}", v in text, v)
    # derived files
    e = docx.Document(M / "editable_tables_R1.docx")
    chk("Editable tables DOCX has all tables", len(e.tables) == len(d.tables), len(e.tables))
    pr = pptx.Presentation(M / "editable_figures_R1.pptx")
    chk(
        "Editable figures PPTX: one slide per figure, 16:9",
        len(pr.slides) == 8 and abs(pr.slide_width / pr.slide_height - 16 / 9) < 0.01,
        len(pr.slides),
    )
    t = docx.Document(M / "manuscript_R1_tracked.docx")
    chk(
        "Tracked: same tables/figures/equations as clean",
        (len(t.tables), len(t.inline_shapes), len(t.element.xpath("//m:oMath")))
        == (len(d.tables), len(d.inline_shapes), len(d.element.xpath("//m:oMath"))),
    )
    clean = [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]
    kept = tracked_kept_text(M / "manuscript_R1_tracked.docx")
    kept = [k for k in kept if k != "Tables of the submitted version (deleted)"]
    chk(
        "Tracked minus deletions == clean text",
        kept == clean,
        f"{len(kept)} vs {len(clean)} paragraphs",
    )
    return checks


if __name__ == "__main__":
    c = main()
    lines = [
        "# TEXT_FIGURE_TABLE_CONSISTENCY (R1)",
        "",
        "Generated by `scripts/r1_qc.py` from the built package; rerun after any rebuild.",
        "",
        "| Check | Pass | Detail |",
        "|---|---|---|",
    ]
    lines += [
        f"| {n} | {'yes' if ok else 'NO'} | {str(det).replace('|', '/')[:200]} |"
        for n, ok, det in c
    ]
    OUT.write_text("\n".join(lines) + "\n")
    fails = [n for n, ok, _ in c if not ok]
    print(f"{len(c) - len(fails)}/{len(c)} passed")
    for n in fails:
        print("FAIL", n)
