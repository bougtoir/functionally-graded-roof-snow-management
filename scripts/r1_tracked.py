"""Marked-up R1 manuscript: clean R1 DOCX with additions red, deletions blue strikethrough.

The clean document is the base, so figures, tables, equations and line numbering match the clean
version. Paragraphs are aligned with the submitted baseline; closely similar paragraphs receive
word-level marks, other changed paragraphs appear as the deleted baseline paragraph followed by
the new paragraph in red. Baseline tables are reproduced as deleted text before the references.
"""

from __future__ import annotations

import copy
import difflib
import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import RGBColor

RED = RGBColor(0xC0, 0x00, 0x00)
BLUE = RGBColor(0x00, 0x33, 0xCC)
WORD_DIFF_RATIO = 0.85


def _mark(run, kind):
    if kind == "ins":
        run.font.color.rgb = RED
    elif kind == "del":
        run.font.color.rgb = BLUE
        run.font.strike = True


def _plain(par) -> bool:
    """True if the paragraph has only simple text runs (no drawing, equation or sub/superscript)."""
    if par._p.xpath(".//w:drawing") or par._p.xpath(".//m:oMath"):
        return False
    return not any(r.font.subscript or r.font.superscript for r in par.runs)


def _word_diff(par, old: str, new: str):
    style_run = copy.deepcopy(par.runs[0]._r.find(qn("w:rPr"))) if par.runs else None
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    wa, wb = re.findall(r"\S+\s*", old), re.findall(r"\S+\s*", new)
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_opcodes():
        parts = [("eq", wb[j1:j2])] if op == "equal" else [("del", wa[i1:i2]), ("ins", wb[j1:j2])]
        for kind, words in parts:
            if not words:
                continue
            run = par.add_run("".join(words))
            if style_run is not None:
                run._r.insert(0, copy.deepcopy(style_run))
            _mark(run, kind)


def _deleted_before(anchor, text: str, doc):
    p = doc.add_paragraph()
    _mark(p.add_run(text), "del")
    anchor._p.addprevious(p._p)
    return p


def _old_items(path: Path):
    d = Document(path)
    paras = [p.text.strip() for p in d.paragraphs if p.text.strip()]
    tables = [" | ".join(c.text.strip() for c in row.cells) for tb in d.tables for row in tb.rows]
    return paras, tables


def build(old: Path, new: Path, out: Path) -> dict:
    A, old_tables = _old_items(old)
    doc = Document(new)
    B = [p for p in doc.paragraphs if p.text.strip()]
    bt = [p.text.strip() for p in B]
    n = {"equal": 0, "word_marked": 0, "replaced": 0, "inserted": 0, "deleted": 0}
    sm = difflib.SequenceMatcher(None, A, bt, autojunk=False)
    refs = next(
        p for p in B if p.style.name.startswith("Heading") and p.text.strip() == "References"
    )
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            n["equal"] += j2 - j1
            continue
        olds, used = A[i1:i2], set()
        for par in B[j1:j2]:
            t = par.text.strip()
            best, bi = 0.0, None
            for k, u in enumerate(olds):
                if k not in used:
                    r = difflib.SequenceMatcher(None, u, t, autojunk=False).ratio()
                    if r > best:
                        best, bi = r, k
            if bi is not None and best >= WORD_DIFF_RATIO and _plain(par):
                used.add(bi)
                _word_diff(par, olds[bi], t)
                n["word_marked"] += 1
                continue
            if bi is not None and best >= 0.5:
                used.add(bi)
                _deleted_before(par, olds[bi], doc)
                n["replaced"] += 1
            else:
                n["inserted"] += 1
            for r in par.runs:
                _mark(r, "ins")
        anchor = B[j2] if j2 < len(B) else refs
        for k, u in enumerate(olds):
            if k not in used:
                _deleted_before(anchor, u, doc)
                n["deleted"] += 1
    head = _deleted_before(refs, "Tables of the submitted version (deleted)", doc)
    head.runs[0].font.bold = True
    for row in old_tables:
        _deleted_before(refs, row, doc)
    for tb in doc.tables:
        for row in tb.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        _mark(r, "ins")
    for m in doc.element.body.iter(qn("m:r")):
        rpr = m.find(qn("w:rPr"))
        if rpr is None:
            rpr = m.makeelement(qn("w:rPr"), {})
            m.insert(0, rpr)
        col = rpr.makeelement(qn("w:color"), {qn("w:val"): "C00000"})
        rpr.append(col)
    doc.save(out)
    return n


if __name__ == "__main__":
    print(build(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
