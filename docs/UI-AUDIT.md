# Bildblick: Abgleich mit der Designreferenz

Referenz: `design-system/index.html`, `DESIGN.md` und `tokens.json`.

## Gemeinsamer Rahmen

Die frühere gemeinsame Dialoggröße von 520 × 760 px ist aufgehoben. `docs/DIALOG-SIZING.md` legt die neue Formel fest: Anzahl der Bedienelemente empfiehlt die Breite, die natürliche GTK-Messung bestimmt die Höhe, und die verfügbare Bildschirmfläche setzt die Obergrenze. Die Fenster bleiben größenveränderbar. Die Aktionsleiste bleibt fest; vertikales Scrollen ist nur bei Inhalten zulässig, die auch in der maximalen Bildschirmfläche nicht passen. Die Hauptansicht behält ihre eigene Startgröße und das Wachstum beim Zoomen.

`dialog_layout.StandardDialog` und `module_window` zählen Bedienelemente und messen den tatsächlichen Inhalt. Lange Pfade und Informationswerte umbrechen; sie dürfen die Dialogbreite nicht künstlich vergrößern.

## Inventar und Korrekturen

| Bereich | Abgleich / Änderung |
| --- | --- |
| Export | Gemeinsamer Rahmen statt 540 × 800; alle zehn Formate, eigene Abmessungen, Zusatzoptionen und Profile passen in die Breite. |
| Größe ändern | Gemeinsamer Rahmen statt 500 × 760; Einheiten, Maße, Interpolation, DPI und Vorgaben sind untereinander angeordnet. |
| Effekte | Gemeinsamer Rahmen statt 860 × 700; Vorschau über zehn direkt sichtbaren Auswahlbuttons, Intensität und Parameter bleiben Regler. |
| Bildanpassungen | Vorschau über Looks und Karten für Licht, Farbe und Effekte; gemeinsame Aktionsleiste. |
| Weitere Bearbeitung | Freie Drehung, Rahmen, Leinwand, eigene Auswahl, Text, neues Bild, automatischer Zuschnitt, Farben reduzieren, Kanaltausch und rote Augen verwenden denselben Werkzeugrahmen. |
| Zeichnen | Sechs Werkzeuge mit Symbol und Text in drei Spalten; Breitenregler mit genauer Eingabe; kompakte Farbwahl und Rückgängig-Aktion. |
| Bildinformationen | Bezeichnung über dem auswählbaren Wert; lange Pfade umbrechen; beide DPI-Werte und Ändern-Aktion passen ohne horizontales Scrollen. |
| Metadaten | EXIF, IPTC und Kommentar verwenden den gemeinsamen Rahmen und eine umbrechende Leseansicht. |
| Datei-/Arbeitsabläufe | Umbenennen, Öffnen mit, letzte Ordner, Zusammenfügen, Exportoptionen, Stapeloptionen und Meldungen verwenden den gemeinsamen Rahmen. Wasserzeichen und Dateiauswahl verwenden Systemdialoge. |
| Einstellungen / Drucken | Ansichtsoptionen, Diashow-Intervall und eigene Druckeinstellungen verwenden den gemeinsamen Rahmen. |
| Hilfe | Durchsuchbare Tastaturhilfe und Über-Meldung mit gleicher Größe und festen Abschlussaktionen. |
| Nebenfenster | Vorschaubilder/Suche, Histogramm und Medienwiedergabe mit inhaltsabhängiger Größe und eigener Schließen-Aktion. |
| Stapelfortschritt | Gleicher Rahmen, sichtbare Abbruchaktion und abgedunkeltes Elternfenster. |
| Menüs | Alle sechs Hauptmenüs mit 88 Aktionen: sinnvolle Abschnittstrenner, Kürzel rechts, doppelte Kürzel aus den Beschriftungen entfernt. |
| Gemeinsame Komponenten | Helle Flächen, 24-px-Dialogradius, 24-px-Außenabstand, Karten, direkte Auswahl, Slider, Fokus, deaktivierte Zustände und schwarze Hauptaktion aus dem bestehenden Designsystem. |

## Prüfung

`tests/ui_dialog_audit.py` öffnet 49 Fälle: 33 Dialog-/Modulvarianten, zehn zusätzliche Exportformatzustände einschließlich eigener Größe und sechs Menü-Popover. Es erfasst pro Dialog Bedienelementzahl, Breitenempfehlung, reale Maße und verbliebenen vertikalen Scrollbedarf. Zusätzlich werden tatsächliche Fenstergrenzen, horizontales Überlaufen, aufgeklappte Zusatzoptionen und die Position der Abschlussbuttons geprüft. Zielgrößen: 1440 × 1050 und 1024 × 640; die reale GTK-Prüfung für die neue Regel steht aus.

Der bestehende GTK-Integrationstest prüft weiterhin Bildoperationen, Vorschau, Abbrechen/Übernahme, Rückgängig, Druckausgabe und Tastaturbedienung. 108 Unit-Tests sichern die Bild- und Dateifunktionen. Die HTML-Referenz besitzt 14 Browserprüfungen einschließlich gleicher Modalgrößen und erreichbarer Fußleiste. Sie wird bei 1440 × 1050 und 390 × 1400 geprüft.

Die GTK-Geometrie wird unter Fedora 44, X11, Xvfb und Openbox überprüft. Die Screenshots verwenden ausschließlich erzeugte Testbilder. Das ist kein vollständiger Test aller realen Codecs, Drucker, Scanner, Screenreader, Skalierungsfaktoren oder der konkreten Wayland-Sitzung.

## Bewusste Systemgrenze

Linux-Datei-/Ordnerauswahl, Farb- und Schriftwahl, Drucker-/Papierauswahl sowie Portale werden vom System dargestellt. Ihre Fenstermaße und Gestaltung werden nicht von Bildblick erzwungen. Das entspricht der ausdrücklich dokumentierten Systemgrenze der Designvorlage. Die App-eigenen Auslöser und vorbereitenden Dialoge folgen dem gemeinsamen Design.

Ab 0.9.1 prüft der GTK-Funktionstest zusätzlich die kompakte Abfrage mit Speichern/Verwerfen/Abbrechen, Escape, Exportabbruch, Fortsetzung nach erfolgreichem Speichern und den Erhalt der Änderungen nach einem Schreibfehler.

0.9.2 prüft zusätzlich, dass der gesamte Text der kurzen Speicherabfrage ohne Scrollen sichtbar ist.


## Hierarchie und Aufgabenstruktur in 0.10.0

Die vollständige neue Bestandsaufnahme steht in [redesign.md](../redesign.md), mit Verweisen auf die Designprinzipien in [knowlede.md](../knowlede.md). Erste Änderungen betreffen gemeinsame Auswahl-/Feldkomponenten, Exportziel, Bildinformationen, Vorschauflächen und Leerzustände. Die Geometrie bleibt unverändert. Die neuen Browserprüfungen ergänzen die bisherige Abnahme um markierte Auswahlzustände, offen sichtbare Exportziele und gegliederte Informationen.
