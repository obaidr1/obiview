# Bildblick – Gestaltung der nativen Oberfläche

## Richtung

Die vom Nutzer bereitgestellte Referenz bestimmt die Gestaltung: eine helle Bildfläche,
schmale rechte Kartenleiste, schwarze pillenförmige Hauptaktionen und ein konzentrierter
Exportdialog. Bildpixel werden weder abgerundet noch durch dekorative Effekte verändert.

Verwendet wurde [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill),
insbesondere dessen SKILL.md, `references/pro-rules.md` und die ersten drei Prioritätsgruppen
aus `references/quick-reference.md`.

Die Designsystem-Abfrage `photo editor minimal monochrome` fand „Minimalism & Swiss Style“.
Die dazu automatisch gelieferten dunklen, violetten Produktfarben und Landingpage-Muster
passten nicht zur Referenz. Die gezielte Stilabfrage `minimal monochrome light` bestätigte
die monochrome Richtung. Die konkrete Farbgebung und runden Formen folgen der Referenz.
Die Abfrage `keyboard focus modal` ergänzte die Anforderungen an sichtbaren Tastaturfokus.
GTK 4 hat keinen eigenen Stack-Datensatz in diesem Skill; es wurden allgemeine
Interaktionsregeln auf die vorhandenen nativen Widgets übertragen.

## Gemeinsame Regeln

- Hintergrund: `#f5f5f3`; Karten: `#fafaf9`; Haupttext: `#242424`;
  sekundärer Text: `#626262`; Linien: `#dededb`.
- Textkontrast liegt für beide Textfarben auf diesen Hintergründen über 4,5:1.
- Kartenradius 20 px, Buttons als Pillen, 8-/16-/24-px-Abstände.
- Systemschrift mit Inter/Cantarell als bevorzugten lokalen Schriften; keine Font-Downloads.
- Symbolische Systemicons, beschriftete Bedienelemente und zusätzliche zugängliche Namen.
- Sichtbarer Fokus, native Auswahlzustände und Rückmeldung bei Hintergrundaufträgen.
- Keine dekorativen Animationen. Das helle Farbsystem bleibt auch bei dunklem Desktop-Thema aktiv.

## Anordnung

Die Kopfzeile enthält Marke, Öffnen, aktuellen Dateinamen, vollständiges Anwendungsmenü
und Speichern. Die Werkzeugzeile konzentriert Drehen, Zuschneiden, Größenänderung und
Historie. Navigation und Dateistatus stehen unten. Die rechte Leiste ist ausblendbar
und vertikal scrollbar. Das Exportfenster ist modal; sein Hintergrund wird abgedunkelt.
Speicherort, seltene Formatoptionen und Profile werden bei Bedarf aufgeklappt.

## Verifikation

`tests/ui_smoke.py` prüft echte GTK-Dialoge, Bearbeitungen, Vorschau und Export in einer
X11-Sitzung mit Xvfb/Openbox. Screenshots dienen zur Prüfung von Proportionen, Dialogen
und kompaktem Fenster. Die Modelltests prüfen die tatsächlichen Ausgabepixel und
Metadaten. Die verbleibenden Grenzen sind in [VALIDATION.md](VALIDATION.md) dokumentiert.
