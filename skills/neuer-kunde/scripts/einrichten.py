#!/usr/bin/env python3
"""Hauptordner für /neuer-kunde einrichten (oder fehlende Teile ergänzen).

Aufruf:
    python einrichten.py <hauptordner> [--name "Vorname Nachname"] [--rechtsraum AT|DE|CH]
                         [--code-ordner projektordner|<pfad>] [--skill-repo <owner/repo>]

Legt nur an, was fehlt. Vorhandene Dateien werden nie überschrieben, damit ein bestehender
Ordner (mit eigenen Vorlagen und Werkzeugen) heil bleibt. Am Ende steht eine Liste:
"neu" und "war schon da".
"""
import argparse
import json
import re
import shutil
from pathlib import Path

HIER = Path(__file__).resolve().parent
neu, da = [], []


def merke(p, angelegt):
    (neu if angelegt else da).append(str(p))


def ordner(p):
    if p.exists():
        merke(p, False)
    else:
        p.mkdir(parents=True)
        (p / ".keep").write_text("", encoding="utf-8")
        merke(p, True)


def datei(p, inhalt):
    if p.exists():
        merke(p, False)
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(inhalt, encoding="utf-8")
    merke(p, True)
    return True


# ---------------------------------------------------------------- Excel
def finanzen(p):
    if p.exists():
        merke(p, False)
        return
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = openpyxl.Workbook()
    fett = Font(bold=True)
    kopf_fill = PatternFill("solid", fgColor="E8E8E8")

    def blatt(name, spalten, breiten):
        ws = wb.create_sheet(name)
        ws.append(spalten)
        for i, b in enumerate(breiten, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = b
            ws.cell(1, i).font = fett
            ws.cell(1, i).fill = kopf_fill
        ws.freeze_panes = "A2"
        return ws

    wb.remove(wb.active)
    ue = blatt("Übersicht", ["Projekt", "Vereinbart", "Bezahlt", "Offen", "Ausgaben", "davon weiterverrechnet", "Ergebnis"],
               [28, 13, 13, 13, 13, 16, 13])
    an = wb.create_sheet("Anleitung")
    pr = blatt("Projekte", ["Projekt", "Typ", "Ansprechpartner", "Start", "Status", "Vereinbarter Preis", "Ordner"],
               [28, 22, 22, 12, 14, 18, 40])
    ei = blatt("Einnahmen", ["Datum", "Projekt", "Beschreibung", "Rechnungsnr.", "Betrag", "Status", "Bezahlt am"],
               [12, 28, 36, 14, 12, 10, 12])
    au = blatt("Ausgaben", ["Datum", "Projekt", "Kategorie", "Beschreibung", "Betrag", "Rhythmus",
                            "Zahlt Kunde zurück?", "Beleg"], [12, 28, 18, 36, 12, 12, 18, 40])

    def dv(ws, spalte, werte):
        v = DataValidation(type="list", formula1='"' + ",".join(werte) + '"', allow_blank=True)
        ws.add_data_validation(v)
        v.add(f"{spalte}2:{spalte}1000")

    dv(pr, "B", ["Kunde bezahlt", "Kunde unentgeltlich", "Eigene Website"])
    dv(pr, "E", ["Anfrage", "Angebot", "Vertrag", "In Arbeit", "Abnahme", "Live", "Pausiert", "Abgebrochen"])
    dv(ei, "F", ["offen", "bezahlt"])
    dv(au, "C", ["Domain", "Hosting/Server", "E-Mail", "Software/Abo", "Lizenz (Schrift/Asset)", "Hardware",
                 "Werbung", "Sonstiges"])
    dv(au, "F", ["einmalig", "monatlich", "jährlich"])
    dv(au, "G", ["ja", "nein"])

    euro = '#,##0.00 "€"'
    for r in range(2, 102):
        q = f"Projekte!A{r}"
        ue[f"A{r}"] = f'=IF({q}="","",{q})'
        ue[f"B{r}"] = f'=IF($A{r}="","",N(Projekte!F{r}))'
        ue[f"C{r}"] = f'=IF($A{r}="","",SUMIFS(Einnahmen!E:E,Einnahmen!B:B,$A{r},Einnahmen!F:F,"bezahlt"))'
        ue[f"D{r}"] = f'=IF($A{r}="","",SUMIFS(Einnahmen!E:E,Einnahmen!B:B,$A{r},Einnahmen!F:F,"offen"))'
        ue[f"E{r}"] = f'=IF($A{r}="","",SUMIFS(Ausgaben!E:E,Ausgaben!B:B,$A{r}))'
        ue[f"F{r}"] = f'=IF($A{r}="","",SUMIFS(Ausgaben!E:E,Ausgaben!B:B,$A{r},Ausgaben!G:G,"ja"))'
        # Weiterverrechnete Ausgaben stecken schon in einer Rechnung (Einnahmen), nicht doppelt zählen
        ue[f"G{r}"] = f'=IF($A{r}="","",C{r}-E{r})'
        for c in "BCDEFG":
            ue[f"{c}{r}"].number_format = euro
    ue["I1"], ue["J1"] = "Gesamt", ""
    ue["I1"].font = fett
    zeilen = [("Bezahlt", "=SUMIFS(Einnahmen!E:E,Einnahmen!F:F,\"bezahlt\")"),
              ("Offen", "=SUMIFS(Einnahmen!E:E,Einnahmen!F:F,\"offen\")"),
              ("Ausgaben", "=SUM(Ausgaben!E:E)"),
              ("Allgemeine Ausgaben", "=SUMIFS(Ausgaben!E:E,Ausgaben!B:B,\"Allgemein\")"),
              ("Ergebnis (bezahlt minus Ausgaben)", "=J2-J4")]
    for i, (l, f) in enumerate(zeilen, 2):
        ue[f"I{i}"], ue[f"J{i}"] = l, f
        ue[f"J{i}"].number_format = euro
    ue.column_dimensions["I"].width = 34
    ue.column_dimensions["J"].width = 14

    an.column_dimensions["A"].width = 110
    for z in [
        "So funktioniert die Finanzdokumentation",
        "",
        "Projekte: eine Zeile pro Projekt. Der Projektname muss überall exakt gleich geschrieben sein, sonst zählt die Übersicht nicht.",
        "Einnahmen: jede Rechnung und Anzahlung. Status 'offen' bis das Geld da ist, dann 'bezahlt' und Datum bei 'Bezahlt am'.",
        "Ausgaben: Domain, Hosting, Abos, Lizenzen. 'Zahlt Kunde zurück?' = ja, wenn du es vorgestreckt hast und weiterverrechnest.",
        "Allgemeine Ausgaben (nicht für ein Projekt): bei Projekt 'Allgemein' eintragen.",
        "Übersicht: rechnet alles selbst. Dort nichts eintippen. Ergebnis = bezahlt minus Ausgaben (weiterverrechnete Ausgaben kommen über die Rechnung wieder rein).",
        "Rechnungsnummern: JJJJ-NNN, fortlaufend über alle Kunden (2026-001, 2026-002 ...).",
        "",
        "Claude trägt über _werkzeuge/finanzen_eintragen.py ein. Du kannst die Datei auch selbst in Excel bearbeiten.",
        "Keine Steuer- oder Rechtsberatung. Für Steuerfragen: Steuerberater oder WKO / IHK.",
    ]:
        an.append([z])
    an["A1"].font = Font(bold=True, size=14)
    wb.save(p)
    merke(p, True)


# ---------------------------------------------------------------- Word
def _docx_helfer():
    from docx import Document
    from docx.enum.text import WD_COLOR_INDEX
    from docx.shared import Pt

    def absatz(doc_or_cell, text, fett=False, groesse=None, stil=None):
        if hasattr(doc_or_cell, "_tc") and len(doc_or_cell.paragraphs) == 1 and not doc_or_cell.paragraphs[0].text:
            p = doc_or_cell.paragraphs[0]  # Tabellenzelle: ersten leeren Absatz nutzen
        else:
            p = doc_or_cell.add_paragraph(style=stil) if stil else doc_or_cell.add_paragraph()
        for teil in re.split(r"(\{\{[A-Z0-9_]+\}\})", text):
            if not teil:
                continue
            r = p.add_run(teil)
            r.bold = fett
            if groesse:
                r.font.size = Pt(groesse)
            if teil.startswith("{{"):
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        return p

    def neu_doc():
        d = Document()
        st = d.styles["Normal"]
        st.font.name = "Calibri"
        st.font.size = Pt(10.5)
        return d

    return neu_doc, absatz


def vertrag(p):
    if p.exists():
        merke(p, False)
        return
    neu_doc, absatz = _docx_helfer()
    d = neu_doc()
    absatz(d, "Werkvertrag Website-Erstellung", fett=True, groesse=18)
    absatz(d, "Projekt: {{PROJEKT}}")
    absatz(d, "")
    absatz(d, "zwischen", fett=True)
    absatz(d, "{{MEIN_NAME}}, {{MEINE_ADRESSE}}, {{MEINE_EMAIL}}")
    absatz(d, "{{MEINE_UID}}")
    absatz(d, "im Folgenden Auftragnehmer, und")
    absatz(d, "{{KUNDE_NAME}}")
    absatz(d, "{{KUNDE_FIRMA}}")
    absatz(d, "{{KUNDE_ADRESSE}}, {{KUNDE_EMAIL}}")
    absatz(d, "im Folgenden Auftraggeber.")
    abschnitte = [
        ("1. Leistungen", ["Der Auftragnehmer erstellt für den Auftraggeber folgende Leistungen:", "{{LEISTUNGEN}}",
                          "Nicht enthalten sind: {{NICHT_ENTHALTEN}}"]),
        ("2. Ablauf und Termine", [
            "Der Auftraggeber liefert Inhalte (Texte, Bilder, Logo, Zugänge) bis {{TERMIN_INHALTE}}.",
            "Design-Freigabe bis {{TERMIN_DESIGN}}. Geplanter Livegang: {{TERMIN_LAUNCH}}.",
            "Verzögern sich Inhalte oder Freigaben, verschieben sich die Termine entsprechend.",
            "Enthalten sind {{KORREKTURRUNDEN}} Korrekturrunden. Weitere Änderungen werden nach Aufwand verrechnet."]),
        ("3. Vergütung", ["{{VERGUETUNG}}"]),
        ("4. Abnahme", [
            "Der Auftraggeber prüft die fertige Website binnen {{ABNAHMEFRIST}} und meldet Mängel schriftlich. "
            "Meldet er sich in dieser Frist nicht oder nimmt er die Website in Betrieb, gilt sie als abgenommen."]),
        ("5. Hosting, Domain und Zugänge", ["{{HOSTING}}", "{{DOMAIN_INHABER}}"]),
        ("6. Gewährleistung und Wartung", ["{{WARTUNG}}"]),
        ("7. Mitwirkung und Rechte an Inhalten", [
            "Der Auftraggeber versichert, dass er an allen gelieferten Inhalten die nötigen Rechte hat, und stellt den "
            "Auftragnehmer von Ansprüchen Dritter frei.",
            "Nach vollständiger Bezahlung erhält der Auftraggeber das zeitlich und örtlich unbeschränkte Recht, die "
            "Website zu nutzen und zu ändern. Verwendete freie Bibliotheken und Schriften stehen unter ihren eigenen Lizenzen.",
            "Der Auftragnehmer darf die Website als Referenz in seinem Portfolio zeigen, sofern nichts anderes vereinbart ist."]),
        ("8. Datenschutz", [
            "Verarbeitet der Auftragnehmer personenbezogene Daten im Auftrag (z. B. beim Hosting oder bei Formularen), "
            "schließen die Parteien eine gesonderte Auftragsverarbeitungsvereinbarung."]),
        ("9. Schluss", [
            "Änderungen dieses Vertrags bedürfen der Schriftform (E-Mail genügt). Ist eine Bestimmung unwirksam, bleibt der "
            "Rest gültig. Gerichtsstand: {{GERICHTSSTAND}}."]),
    ]
    for titel, saetze in abschnitte:
        absatz(d, "")
        absatz(d, titel, fett=True, groesse=12)
        for s in saetze:
            absatz(d, s)
    absatz(d, "")
    absatz(d, "{{ORT}}, am {{DATUM}}")
    absatz(d, "")
    t = d.add_table(rows=2, cols=2)
    t.cell(0, 0).text = "\n\n______________________________"
    t.cell(0, 1).text = "\n\n______________________________"
    t.cell(1, 0).text = ""
    t.cell(1, 1).text = ""
    absatz(t.cell(1, 0), "{{MEIN_NAME}} (Auftragnehmer)")
    absatz(t.cell(1, 1), "{{KUNDE_NAME}} (Auftraggeber)")
    d.save(p)
    merke(p, True)


def rechnung(p):
    if p.exists():
        merke(p, False)
        return
    neu_doc, absatz = _docx_helfer()
    d = neu_doc()
    absatz(d, "{{MEIN_NAME}}", fett=True, groesse=14)
    absatz(d, "{{MEINE_ADRESSE}}")
    absatz(d, "{{MEINE_EMAIL}}")
    absatz(d, "{{MEINE_UID}}")
    absatz(d, "")
    absatz(d, "{{KUNDE_NAME}}")
    absatz(d, "{{KUNDE_FIRMA}}")
    absatz(d, "{{KUNDE_ADRESSE}}")
    absatz(d, "UID: {{KUNDE_UID}}")
    absatz(d, "")
    absatz(d, "Rechnung {{RECHNUNGSNR}}", fett=True, groesse=18)
    absatz(d, "Rechnungsdatum: {{DATUM}}")
    absatz(d, "Leistungszeitraum: {{LEISTUNGSZEITRAUM}}")
    absatz(d, "Projekt: {{PROJEKT}}")
    absatz(d, "")
    t = d.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    for i, h in enumerate(["Leistung", "Menge", "Betrag"]):
        t.cell(0, i).text = ""
        absatz(t.cell(0, i), h, fett=True)
    for n in (1, 2, 3, 4, 5):
        row = t.add_row()
        for i, f in enumerate(["BESCHREIBUNG", "MENGE", "BETRAG"]):
            row.cells[i].text = ""
            absatz(row.cells[i], "{{POS%d_%s}}" % (n, f))
    row = t.add_row()
    row.cells[0].text = ""
    absatz(row.cells[0], "Summe", fett=True)
    row.cells[2].text = ""
    absatz(row.cells[2], "{{SUMME}}", fett=True)
    absatz(d, "")
    absatz(d, "{{UST_HINWEIS}}")
    absatz(d, "Bitte überweise den Betrag bis {{ZAHLUNGSZIEL}} unter Angabe der Rechnungsnummer auf:")
    absatz(d, "{{MEIN_NAME}} · IBAN {{MEINE_IBAN}} · BIC {{MEINE_BIC}}")
    absatz(d, "")
    absatz(d, "Danke für die Zusammenarbeit.")
    d.save(p)
    merke(p, True)


# ---------------------------------------------------------------- Texte
PROJEKT_MD = """# {{PROJEKT}}

**Stand:** (ein Satz, was gerade dran ist)
**Status:** Anfrage
**Typ:** (Kunde bezahlt / Kunde unentgeltlich / Eigene Website)
**Code-Ordner:** (Pfad)
**Notion:** (Link oder nein)

## Geld (Kurzstand)
Vereinbart: ❓ · Bezahlt: 0 € · Offen: 0 € · Ausgaben: 0 €

## Antworten aus den Fragen
(alle Antworten aus Abschnitt 2 des Skills)

## Entscheidungen
| Datum | Was | Warum |
| --- | --- | --- |

## Offen
- ❓ (was noch fehlt)

## Verlauf
| Datum | Was |
| --- | --- |
"""

PROMPT_TXT = """STECKBRIEF FÜR /neuer-kunde
Ausfüllen, was du schon weißt, Rest leer lassen. Dann im Chat:  /neuer-kunde  und den Steckbrief einfügen.

Für wen:                 (Kunde bezahlt / Kunde unentgeltlich / eigene Website)
Name (Kunde/Projekt):
Was macht er, 1 Satz:
Ansprechpartner + Mail:
Adresse (für Vertrag):
Geld über die Seite:     (nein / extern, z. B. Etsy / eigener Shop)
Land:                    (AT / DE / CH)
Angebote + Preise:
Referenzen / Projekte:
Logo, Fotos, Texte:      (was gibt es, wer schreibt)
Domain, E-Mail:
Referenzseiten:          (Link + "Struktur" oder "Stimmung")
Stilwunsch:
Deadline, Stunden/Woche:
Preis, Anzahlung %, Korrekturrunden, Stundensatz (nur bei bezahlt):

KURZANLEITUNG
/neuer-kunde                      neues Projekt
/neuer-kunde weiter <Projekt>     am Projekt weitermachen
/neuer-kunde geld <Projekt> <Text>   Zahlung oder Ausgabe eintragen
/neuer-kunde vertrag <Projekt>    Vertrag erstellen
/neuer-kunde rechnung <Projekt>   Rechnung erstellen
/neuer-kunde fertig <Projekt>     Projekt abschließen, Skill lernt dazu
/neuer-kunde verbessern           Skill mit dem Gelernten verbessern (wird vorher getestet)
/neuer-kunde einrichten           Ordner einrichten oder Einstellungen ändern
"""

MEINE_DATEN = {
    "MEIN_NAME": "", "MEINE_ADRESSE": "", "MEINE_EMAIL": "", "MEINE_TELEFON": "",
    "MEINE_IBAN": "", "MEINE_BIC": "", "MEINE_UID": "",
    "UST_HINWEIS": "", "ORT": "", "GERICHTSSTAND": "",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hauptordner")
    ap.add_argument("--name", default="")
    ap.add_argument("--rechtsraum", default="")
    ap.add_argument("--ort", default="")
    ap.add_argument("--code-ordner", default="projektordner")
    ap.add_argument("--skill-repo", default="")
    a = ap.parse_args()

    h = Path(a.hauptordner).expanduser()
    h.mkdir(parents=True, exist_ok=True)
    w = h / "_werkzeuge"
    w.mkdir(exist_ok=True)

    for name in ("vorlage_ausfuellen.py", "finanzen_eintragen.py"):
        ziel = w / name
        if ziel.exists():
            merke(ziel, False)
        else:
            shutil.copy(HIER / name, ziel)
            merke(ziel, True)

    md = dict(MEINE_DATEN)
    md["MEIN_NAME"] = a.name
    md["ORT"] = a.ort
    md["GERICHTSSTAND"] = a.ort
    datei(w / "meine-daten.json", json.dumps(md, ensure_ascii=False, indent=2) + "\n")
    datei(w / "einstellungen.json", json.dumps({
        "version": 1,
        "hauptordner": str(h),
        "code_ordner": a.code_ordner,
        "rechtsraum": a.rechtsraum,
        "sprache": "de",
        "dev_port": 5000,
        "referenz_projekte": [],
        "skill_repo": a.skill_repo,
        "notion_elternseite": "Kunden",
    }, ensure_ascii=False, indent=2) + "\n")

    finanzen(h / "Finanzdokumentation.xlsx")
    vertrag(h / "Vertragvorlage.docx")
    rechnung(h / "Rechnungsvorlage.docx")
    datei(h / "Prompt.txt", PROMPT_TXT)

    kv = h / "Kunden" / "Kundenvorlage"
    for sub in ("Vertrag", "Rechnungen", "Belege", "Vom Kunden", "Notizen"):
        ordner(kv / sub)
    datei(kv / "Projekt.md", PROJEKT_MD)
    ordner(h / "Eigene Projekte")
    datei(h / "_skills" / "lernliste.md",
          "# Lernliste für /neuer-kunde\n\nPro Eintrag: Datum, Projekt, Runde, Korrektur wörtlich, was künftig gilt.\n\n")

    print(f"Hauptordner: {h}")
    print(f"\nNEU ({len(neu)}):")
    for x in neu:
        print("  + " + x)
    print(f"\nWAR SCHON DA ({len(da)}):")
    for x in da:
        print("  = " + x)
    leer = [k for k, v in json.loads((w / "meine-daten.json").read_text(encoding="utf-8")).items() if not v]
    if leer:
        print("\nNoch leer in meine-daten.json (vor dem ersten Vertrag abfragen): " + ", ".join(leer))


if __name__ == "__main__":
    main()
