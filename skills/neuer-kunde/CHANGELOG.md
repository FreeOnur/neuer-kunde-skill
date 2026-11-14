# CHANGELOG neuer-kunde

## v6 (03.11.2026): Taste Skill als Design-Gate, Kundensicht, kurze Texte

Aus einer gemeinsamen Agentur-Seite (Löwen Webdesign, Runden 12 bis 18).

**Neu**
- Taste Skill (`Leonxlnx/taste-skill`) ist Pflicht für jede öffentliche Seite: Hausregeln gelten zusätzlich zur Stilrichtung, Gate mit `lint.mjs` und `inspect.mjs` vor jeder Abgabe, zwei bekannte Fehlalarme mit Ausweg (Abschnitt 5.1).
- 3D-Option „Welt aus dem Logo“: dieselben Flächen ordnen sich pro Abschnitt neu, prozedural statt GLB, unter 1 MB.
- Formular mit einem Klick über Resend plus Bestätigung an den Kunden, bei statischem Export als kleiner Dienst neben der Seite.
- Ton-Frage als Leiste, die nichts sperrt (kein Tor mehr vor dem ersten Bild).
- Kundensicht: jede Überschrift ist eine Frage des Kunden. Kurze Texte mit festen Grenzen als Unit-Test.
- Arbeiten im Querformat 16:10 im Browserfenster, Bilder in passenden Größen, Kopfzeile oben durchsichtig.
- Rechtsseiten (AT/DE/CH), Suchmaschinen- und KI-Dateien (robots, sitemap, llms.txt, JSON-LD), Seiten ohne WebGL.

**Test**
- Formaler A/B-Lauf gegen v4 steht noch aus (Abschnitt 11, Schritt 4).

## v4 (29.10.2026): Blender-3D, simulierte Kunden

Aus Onur-Portfolio (Oktober 2026).

**Neu**
- Begehbare Echtzeit-Szenen aus Blender (gebackenes Licht, Three.js), Kamerafahrt als Geschichte.
- Qualitäts-Rundgang: E2E mit Playwright, Lighthouse, vier simulierte Kunden (Persona-Agents) mit Klick-Heatmap, Blindtest bei Änderungen.
- Die Fassung v4 liegt unverändert unter `versionen/v4-2026-10-29.md`.

## v3 (24.10.2026): für alle nutzbar, Testpflicht

**Neu**
- Keine festen Pfade mehr. Der Hauptordner wird gesucht (Nachricht, verbundene Ordner, Memory) oder beim ersten Start eingerichtet. Pfade und Vorlieben stehen in `<Hauptordner>/_werkzeuge/einstellungen.json`.
- Modus `einrichten` mit mitgelieferten Werkzeugen in `scripts/`:
  - `einrichten.py`: Ordnerbaum, Finanzdokumentation mit Formeln, Vertrags- und Rechnungsvorlage, Steckbrief. Überschreibt nichts.
  - `vorlage_ausfuellen.py` und `finanzen_eintragen.py`, inkl. `--naechste-rechnungsnr` und `--liste`.
- Referenzprojekte (SMTN, Onur-Portfolio) sind jetzt optional, die Bausteine sind als Bauanleitung beschrieben.
- Ablauf ohne Rückfragen: empfohlene Option nehmen, als „nicht bestätigt“ markieren, Fakten nie erfinden. Status-Reihenfolge im Blatt Projekte festgelegt.
- Schlussrechnung fest aufgebaut: Pauschale, minus Anzahlung, Weiterverrechnungen als eigene Positionen. Die Vorlage hat 5 Positionen.
- Abschnitt 11: neue Version nur nach Test gegen die alte (Testfälle in `testfaelle/`, Freigabe-Regel), Übergabe als `.skill`-Paket.

**Behoben (im Test gefunden)**
- Ergebnis in der Excel-Übersicht hat weiterverrechnete Ausgaben doppelt gezählt. Neu: Ergebnis = bezahlt − Ausgaben.

**Test**
- v3: 20/20 bestanden. v2 (alt): 19/20.
- v2 hat beim Einrichten für einen fremden User die Pfade des Autors in dessen Ordner kopiert und brauchte für denselben Fall etwa 6× so lange (437 s statt 64 bis 72 s).

## v2 (24.10.2026)
Stand aus SMTN und Onur-Portfolio, feste Pfade auf den Rechner des Autors.
