"""Minimal native Word (OMML) equation builder."""

from __future__ import annotations

from docx.oxml import OxmlElement


def _el(tag: str, *children):
    e = OxmlElement(tag)
    for c in children:
        e.append(c)
    return e


def r(text: str, italic: bool = True):
    run = OxmlElement("m:r")
    if not italic:
        rpr = OxmlElement("m:rPr")
        sty = OxmlElement("m:sty")
        sty.set("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", "p")
        rpr.append(sty)
        run.append(rpr)
    t = OxmlElement("m:t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    run.append(t)
    return run


def sub(base, subscript):
    return _el("m:sSub", _el("m:e", *_wrap(base)), _el("m:sub", *_wrap(subscript)))


def sup(base, superscript):
    return _el("m:sSup", _el("m:e", *_wrap(base)), _el("m:sup", *_wrap(superscript)))


def frac(num, den):
    return _el("m:f", _el("m:num", *_wrap(num)), _el("m:den", *_wrap(den)))


def nary(char: str, lower, upper, body):
    pr = OxmlElement("m:naryPr")
    ch = OxmlElement("m:chr")
    ch.set("{http://schemas.openxmlformats.org/officeDocument/2006/math}val", char)
    pr.append(ch)
    return _el("m:nary", pr, _el("m:sub", *_wrap(lower)), _el("m:sup", *_wrap(upper)),
               _el("m:e", *_wrap(body)))


def func(name: str, arg):
    return _el("m:func", _el("m:fName", r(name, italic=False)), _el("m:e", *_wrap(arg)))


def _wrap(x):
    if isinstance(x, str):
        return [r(x)]
    if isinstance(x, list | tuple):
        out = []
        for item in x:
            out.extend(_wrap(item))
        return out
    return [x]


def add_equation(paragraph, *parts, number: str | None = None):
    math = _el("m:oMath", *_wrap(list(parts)))
    if number:
        math.append(r(f"    ({number})", italic=False))
    paragraph._p.append(_el("m:oMathPara", math))
    return paragraph


def add_inline(paragraph, *parts):
    paragraph._p.append(_el("m:oMath", *_wrap(list(parts))))
    return paragraph
