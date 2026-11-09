"""Marked-up comparison: additions red, deletions blue strikethrough (baseline vs R1 clean)."""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

sys.path.insert(0, "src")
from graded_roof.manuscript import _add_line_numbering  # noqa: E402

RED = RGBColor(0xC0, 0x00, 0x00)
BLUE = RGBColor(0x00, 0x33, 0xCC)


def paras(path: Path) -> list[tuple[str, str]]:
    d = Document(path)
    out = []
    for p in d.paragraphs:
        t = p.text.strip()
        if t:
            out.append((p.style.name, t))
    for tb in d.tables:
        for row in tb.rows:
            out.append(("Normal", " | ".join(c.text.strip() for c in row.cells)))
    return out


def add(p, text, kind):
    r = p.add_run(text)
    if kind == "ins":
        r.font.color.rgb = RED
    elif kind == "del":
        r.font.color.rgb = BLUE
        r.font.strike = True


def word_diff(p, a: str, b: str):
    wa, wb = re.findall(r"\S+\s*", a), re.findall(r"\S+\s*", b)
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_opcodes():
        if op == "equal":
            add(p, "".join(wb[j1:j2]), "eq")
        else:
            if i2 > i1:
                add(p, "".join(wa[i1:i2]), "del")
            if j2 > j1:
                add(p, "".join(wb[j1:j2]), "ins")


def style_of(doc, name):
    try:
        return doc.styles[name]
    except KeyError:
        return doc.styles["Normal"]


def build(old: Path, new: Path, out: Path) -> dict:
    A, B = paras(old), paras(new)
    doc = Document()
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(10)
    _add_line_numbering(doc)
    n = {"equal": 0, "ins": 0, "del": 0, "mod": 0}
    sm = difflib.SequenceMatcher(None, [t for _, t in A], [t for _, t in B], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for s, t in B[j1:j2]:
                add(doc.add_paragraph(style=style_of(doc, s)), t, "eq")
                n["equal"] += 1
            continue
        olds, news = A[i1:i2], B[j1:j2]
        used = set()
        for s, t in news:
            best, bi = 0.0, None
            for k, (_, u) in enumerate(olds):
                if k in used:
                    continue
                r = difflib.SequenceMatcher(None, u, t, autojunk=False).quick_ratio()
                if r > best:
                    best, bi = r, k
            p = doc.add_paragraph(style=style_of(doc, s))
            if bi is not None and best >= 0.6:
                used.add(bi)
                word_diff(p, olds[bi][1], t)
                n["mod"] += 1
            else:
                add(p, t, "ins")
                n["ins"] += 1
        for k, (s, u) in enumerate(olds):
            if k not in used:
                add(doc.add_paragraph(style=style_of(doc, s)), u, "del")
                n["del"] += 1
    doc.save(out)
    return n


if __name__ == "__main__":
    print(build(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
