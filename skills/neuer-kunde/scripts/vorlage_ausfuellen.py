#!/usr/bin/env python3
"""Word-Vorlage mit {{PLATZHALTERN}} ausfüllen.

Aufruf:
    python vorlage_ausfuellen.py <vorlage.docx> <ziel.docx> <werte.json> [<weitere.json> ...]

Regeln für die Werte (mehrere JSON-Dateien werden zusammengeführt, spätere gewinnen):
    "Text"   -> Platzhalter wird ersetzt, gelbe Markierung verschwindet. "\n" wird Zeilenumbruch.
    ""       -> nur der Platzhalter verschwindet (z. B. KUNDE_FIRMA bei Privatkunden).
    null     -> der ganze Absatz verschwindet; steht er in einer Tabelle, die ganze Tabellenzeile
               (z. B. ungenutzte Rechnungsposition POS3_*, fehlende KUNDE_UID).
    fehlt    -> Platzhalter bleibt gelb stehen und wird am Ende als "offen" gemeldet.

Exit-Code 0 auch wenn etwas offen ist; die Liste steht in der Ausgabe.
"""
import json
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_COLOR_INDEX
except ImportError:
    sys.exit("python-docx fehlt: pip install python-docx")

MUSTER = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")
LOESCHEN = object()


def alle_absaetze(doc):
    """Absätze aus Text, Tabellen (auch verschachtelt), Kopf- und Fußzeilen."""
    def aus_container(c):
        for p in c.paragraphs:
            yield p, None
        for t in getattr(c, "tables", []):
            for row in t.rows:
                for cell in row.cells:
                    for p, r in aus_container(cell):
                        yield p, (r or row)
    yield from aus_container(doc)
    for s in doc.sections:
        for teil in (s.header, s.footer, s.first_page_header, s.first_page_footer):
            try:
                yield from aus_container(teil)
            except Exception:
                pass


def runs_zusammenfassen(p):
    """Platzhalter, die über mehrere Runs verteilt sind, in einen Run holen."""
    text = "".join(r.text for r in p.runs)
    if "{{" not in text:
        return
    sauber = all(
        len(MUSTER.findall(r.text)) == r.text.count("{{") == r.text.count("}}")
        and "{" not in MUSTER.sub("", r.text) and "}" not in MUSTER.sub("", r.text)
        for r in p.runs
    )
    if sauber:
        return
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""


def setze_text(run, wert):
    teile = str(wert).split("\n")
    run.text = teile[0]
    for t in teile[1:]:
        run.add_break()
        run.add_text(t)


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    vorlage, ziel = Path(sys.argv[1]), Path(sys.argv[2])
    werte = {}
    for f in sys.argv[3:]:
        werte.update(json.loads(Path(f).read_text(encoding="utf-8")))

    doc = Document(vorlage)
    ersetzt, offen = set(), set()
    zu_loeschen_absatz, zu_loeschen_zeile = [], []

    for p, zeile in list(alle_absaetze(doc)):
        runs_zusammenfassen(p)
        for run in p.runs:
            if "{{" not in run.text:
                continue
            loeschen = False

            def ersetze(m):
                nonlocal loeschen
                key = m.group(1)
                if key not in werte:
                    offen.add(key)
                    return m.group(0)
                if werte[key] is None:
                    loeschen = True
                    ersetzt.add(key)
                    return ""
                ersetzt.add(key)
                return "\x00" + str(werte[key]) + "\x01"

            neu = MUSTER.sub(ersetze, run.text)
            if loeschen:
                (zu_loeschen_zeile if zeile is not None else zu_loeschen_absatz).append(zeile if zeile is not None else p)
                continue
            if "\x00" in neu:
                neu = neu.replace("\x00", "").replace("\x01", "")
                setze_text(run, neu)
                if not MUSTER.search(neu):
                    run.font.highlight_color = None
            else:
                run.text = neu

    for p in zu_loeschen_absatz:
        el = p._element
        if el.getparent() is not None:
            el.getparent().remove(el)
    gesehen = set()
    for row in zu_loeschen_zeile:
        if id(row._tr) in gesehen:
            continue
        gesehen.add(id(row._tr))
        tr = row._tr
        if tr.getparent() is not None:
            tr.getparent().remove(tr)

    ziel.parent.mkdir(parents=True, exist_ok=True)
    doc.save(ziel)
    print(f"Gespeichert: {ziel}")
    print(f"Ersetzt: {len(ersetzt)} Platzhalter")
    unbenutzt = sorted(set(werte) - ersetzt - offen)
    if offen:
        print("OFFEN (bleibt gelb): " + ", ".join(sorted(offen)))
    else:
        print("Offen: nichts")
    if unbenutzt:
        print("Hinweis, nicht in der Vorlage: " + ", ".join(unbenutzt))


if __name__ == "__main__":
    main()
