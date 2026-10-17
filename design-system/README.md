# Bildblick · lokale Designreferenz

`index.html` direkt im Browser öffnen. Die Website braucht weder Internet noch einen Buildschritt zum Ansehen. CSS, JavaScript und SVG-Symbole sind direkt in index.html eingebettet. Auch eine einzeln kopierte HTML-Datei zeigt das vollständige Design. Es werden keine Bilder hochgeladen und keine App-Dateien verändert.

Optional über einen lokalen Server:

```sh
cd /home/obaidlinux/irfanview-linux/design-system
npm start
```

Anschließend http://127.0.0.1:4173 öffnen. Der Server bindet nur an localhost.

## Inhalt

17 Bereiche: Prinzipien, Tokens, Buttons und Zustände, direkte Auswahl, Slider, Formulare, Switches/Checkboxen/Radio, Farbe/Schrift/Details, Menüs/Toolbar, Bild/Vorschau, Bearbeitungsdialog, Exportdialog, Informationen/Listen, Rückmeldung, 32 Symbole, Inventar und verbindlicher Designvertrag.

Bedienbare Beispiele: Slider mit synchroner genauer Eingabe und Schrittbuttons, Werkzeugwahl mit Pfeiltasten, Schalter, Dateinamensvalidierung, Suchfilter, Originalvergleich, Zurücksetzen/Abbrechen/Übernahme, Exportformat und eigene Auflösung, modale Dialoge mit Fokusbindung und Escape. Die echten Bildoperationen bleiben in der GTK-App; Vorschau-Simulationen sind ausdrücklich beschriftet.

## Dateien und Bearbeitung

| Datei | Aufgabe |
| --- | --- |
| `src/catalog.html` | Editierbare HTML-Quelle der Komponenten und Beispiele |
| `index.html` | Erzeugte, eigenständige Website mit eingebettetem CSS und JavaScript |
| `tokens.json` | Verbindliche gemeinsame Designwerte |
| `tokens.css` | Erzeugte CSS-Variablen, nicht von Hand ändern |
| `styles.css` | Komponenten, Layout, Zustände, responsive Regeln |
| `src/app.ts` | TypeScript-Quellcode der Demonstrationen |
| `app.js` | Erzeugtes klassisches Browser-JavaScript; funktioniert auch über file:// |
| `scripts/build.mjs` | Lokaler Build mit Node.js 24+, ohne npm-Abhängigkeiten |
| `DESIGN.md` | Verbindliche Gestaltung und Arbeitsweise |
| `scripts/browser-check.js` | Browser-Prüfung der interaktiven Muster |
| `scripts/check_structure.py` | Referenzen, IDs und vollständige Elementzuordnung prüfen |

Nach Änderungen an HTML-Quelle, CSS, TypeScript oder Tokens:

```sh
npm run build
npm run check
node --check app.js
python3 scripts/check_structure.py
```

Der Build verwendet Nodes TypeScript-Typentfernung. Das ist kein vollständiger TypeScript-Typcheck; die Browser-Prüfung kontrolliert die tatsächlichen Abläufe. Kein Framework, Bundler, CDN, externer Font oder npm-Download ist zum Betrachten oder Bauen erforderlich.

## Verbindlichkeit

[DESIGN.md](DESIGN.md) ist der Designvertrag. Die projektweite `../AGENTS.md` verlangt seine Anwendung bei künftiger UI-Arbeit. Fehlende Komponenten werden zuerst hier ergänzt. Die Website ersetzt die native App nicht; bestehende Ansichten werden nicht allein durch diese Dateien automatisch migriert.

## Browserprüfung

```sh
python3 scripts/prepare_check.py
firefox --headless --screenshot /tmp/bildblick-design-check.png --window-size 1440,1000 "file://$PWD/.browser-check.html"
```

Die erzeugte, ignorierte `.browser-check.html` führt 13 Browserprüfungen aus und zeigt ihren Bericht direkt auf der Seite. Sie ist getrennt von der normalen Designreferenz. Für schmale Ansichten `--window-size 390,1400` verwenden. Der Bericht muss **PASS · 14/14** zeigen; der Firefox-Exitcode allein genügt nicht, um erfolgreiche Assertions zu belegen.

Geprüft am 16. Oktober 2026: beide Größen mit 14/14 erfolgreichen Prüfungen. Desktop-Übersicht, mobile Übersicht, Werkzeugauswahl, Export und Bearbeitungsdialog wurden visuell geprüft. Strukturprüfung, JavaScript-Syntaxprüfung und Übereinstimmung der generierten Dateien bestehen ebenfalls. Eine vollständige Screenreader-Abnahme und ein vollständiger TypeScript-Typcheck stehen aus.

## Gemeinsame Dialogmaße

Die Dialogbreite folgt der Zahl der Bedienelemente (480 px Grundbreite plus 64 px mal der Wurzel aus den Elementen ab dem fünften). Es gibt keine feste Dialogobergrenze; der Bildschirm begrenzt die Maße. Die Höhe wird aus der natürlichen Inhaltshöhe gemessen. Vorschau, Optionen und Abschlussaktion sollen ohne vertikales Scrollen sichtbar sein. Formel und Messprotokoll stehen in `../docs/DIALOG-SIZING.md` und der native Rahmen setzt sie in `dialog_layout.py` um.
