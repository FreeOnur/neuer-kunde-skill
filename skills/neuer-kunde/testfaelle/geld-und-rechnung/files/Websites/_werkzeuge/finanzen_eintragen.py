#!/usr/bin/env python3
"""Finanzdokumentation.xlsx pflegen, ohne Formeln kaputt zu machen.

Aufrufe:
    python finanzen_eintragen.py <xlsx> <Blatt> --zeile '<JSON-Liste>'
        Hängt eine Zeile unten an (erste leere Zeile in Spalte A).
        Projekte : [Projekt, Typ, Ansprechpartner, Start, Status, Vereinbarter Preis, Ordner]
        Einnahmen: [Datum, Projekt, Beschreibung, Rechnungsnr., Betrag, "offen"|"bezahlt", Bezahlt am]
        Ausgaben : [Datum, Projekt|"Allgemein", Kategorie, Beschreibung, Betrag, Rhythmus, "ja"|"nein", Beleg]
        Datumsangaben als "JJJJ-MM-TT" oder "heute". Beträge als Zahl.

    python finanzen_eintragen.py <xlsx> <Blatt> --setze <Schlüssel> <Spalte> <Wert>
        Ändert eine Zelle. Schlüssel = Rechnungsnr. (Einnahmen) bzw. Projektname (Projekte).
        Einnahmen + Status "bezahlt": "Bezahlt am" wird auf heute gesetzt, wenn leer.

    python finanzen_eintragen.py <xlsx> --naechste-rechnungsnr [JAHR]
        Gibt die nächste fortlaufende Nummer im Format JJJJ-NNN aus.

    python finanzen_eintragen.py <xlsx> --liste <Blatt> [--projekt <Name>]
        Gibt die Zeilen eines Blatts als JSON aus (zum Lesen des Stands).
"""
import json
import re
import sys
from datetime import date, datetime

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl fehlt: pip install openpyxl")

SCHLUESSEL_SPALTE = {"Einnahmen": "Rechnungsnr.", "Projekte": "Projekt", "Ausgaben": "Beschreibung"}
DATUM_SPALTEN = {"Datum", "Start", "Bezahlt am"}
BETRAG_SPALTEN = {"Betrag", "Vereinbarter Preis"}


def kopf(ws):
    return [c.value for c in ws[1]]


def letzte_zeile(ws):
    r = ws.max_row
    while r > 1 and all(ws.cell(r, c).value in (None, "") for c in range(1, ws.max_column + 1)):
        r -= 1
    return r


def wert_umwandeln(spalte, v):
    if v is None:
        return None
    if spalte in DATUM_SPALTEN and isinstance(v, str) and v:
        if v.lower() == "heute":
            return date.today()
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(v, "%d.%m.%Y").date()
            except ValueError:
                return v
    if spalte in BETRAG_SPALTEN and isinstance(v, str):
        s = v.replace("€", "").replace(" ", "").strip()
        if re.fullmatch(r"-?\d{1,3}(\.\d{3})*(,\d+)?", s):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return v
    return v


def formatieren(cell, spalte):
    if spalte in DATUM_SPALTEN:
        cell.number_format = "DD.MM.YYYY"
    elif spalte in BETRAG_SPALTEN:
        cell.number_format = '#,##0.00 "€"'


def zeile_anhaengen(wb, blatt, werte):
    ws = wb[blatt]
    k = kopf(ws)
    if len(werte) > len(k):
        sys.exit(f"Zu viele Werte ({len(werte)}) für {blatt} mit Spalten {k}")
    r = letzte_zeile(ws) + 1
    for i, v in enumerate(werte):
        spalte = k[i]
        c = ws.cell(r, i + 1, wert_umwandeln(spalte, v))
        formatieren(c, spalte)
    return r, dict(zip(k, werte))


def setze(wb, blatt, schluessel, spalte, wert):
    ws = wb[blatt]
    k = kopf(ws)
    if spalte not in k:
        sys.exit(f"Spalte '{spalte}' gibt es in {blatt} nicht. Spalten: {k}")
    ks = k.index(SCHLUESSEL_SPALTE.get(blatt, k[0])) + 1
    ziel = k.index(spalte) + 1
    treffer = [r for r in range(2, letzte_zeile(ws) + 1) if str(ws.cell(r, ks).value).strip() == schluessel]
    if not treffer:
        sys.exit(f"'{schluessel}' nicht gefunden in {blatt}")
    for r in treffer:
        c = ws.cell(r, ziel, wert_umwandeln(spalte, wert))
        formatieren(c, spalte)
        if blatt == "Einnahmen" and spalte == "Status" and str(wert).lower() == "bezahlt" and "Bezahlt am" in k:
            bc = ws.cell(r, k.index("Bezahlt am") + 1)
            if bc.value in (None, ""):
                bc.value = date.today()
                formatieren(bc, "Bezahlt am")
    return treffer


def naechste_nr(wb, jahr):
    ws = wb["Einnahmen"]
    k = kopf(ws)
    sp = k.index("Rechnungsnr.") + 1
    hoechste = 0
    for r in range(2, letzte_zeile(ws) + 1):
        m = re.fullmatch(rf"{jahr}-(\d+)", str(ws.cell(r, sp).value or "").strip())
        if m:
            hoechste = max(hoechste, int(m.group(1)))
    return f"{jahr}-{hoechste + 1:03d}"


def liste(wb, blatt, projekt=None):
    ws = wb[blatt]
    k = kopf(ws)
    out = []
    for r in range(2, letzte_zeile(ws) + 1):
        z = {}
        for i, name in enumerate(k):
            v = ws.cell(r, i + 1).value
            z[name] = v.isoformat()[:10] if isinstance(v, (date, datetime)) else v
        if projekt and z.get("Projekt") != projekt:
            continue
        out.append(z)
    return out


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    pfad = a[0]
    wb = openpyxl.load_workbook(pfad)
    if a[1] == "--naechste-rechnungsnr":
        jahr = a[2] if len(a) > 2 else str(date.today().year)
        print(naechste_nr(wb, jahr))
        return
    if a[1] == "--liste":
        projekt = a[a.index("--projekt") + 1] if "--projekt" in a else None
        print(json.dumps(liste(wb, a[2], projekt), ensure_ascii=False, indent=1))
        return
    blatt = a[1]
    if blatt not in wb.sheetnames:
        sys.exit(f"Blatt '{blatt}' fehlt. Vorhanden: {wb.sheetnames}")
    if len(a) >= 4 and a[2] == "--zeile":
        r, z = zeile_anhaengen(wb, blatt, json.loads(a[3]))
        wb.save(pfad)
        print(f"{blatt}: Zeile {r} eingetragen: {json.dumps(z, ensure_ascii=False)}")
    elif len(a) >= 6 and a[2] == "--setze":
        rows = setze(wb, blatt, a[3], a[4], a[5])
        wb.save(pfad)
        print(f"{blatt}: '{a[3]}' -> {a[4]} = {a[5]} (Zeile {', '.join(map(str, rows))})")
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
