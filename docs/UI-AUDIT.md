# Bildblick: Abgleich mit der Designreferenz

Referenz: `design-system/index.html`, `DESIGN.md` und `tokens.json`.

## Gemeinsamer Rahmen

Werkzeugdialoge und Nebenfenster verwenden **520 × 760 logische Pixel**. Kurze Meldungen und Sicherheitsabfragen verwenden dieselbe Maximalbreite, passen ihre Höhe aber an den Inhalt an. Die Maximalbreite entspricht dem Exportdialog der HTML-Vorlage. Auf einem kleineren Bildschirm begrenzt der gemeinsame Rahmen beide Maße auf die Bildschirmfläche abzüglich 32 Pixel. Die Fenster können nicht über diese gemeinsame Größe hinaus aufgezogen werden. Die Hauptansicht behält ihre eigene Startgröße und das Wachstum beim Zoomen.

`dialog_layout.StandardDialog` und `module_window` lesen die Größen direkt aus den Designtokens. Eine nachträgliche Breitenänderung an einem einzelnen Fachdialog ist damit nicht mehr vorgesehen. Körper und feste Abschlussleiste sind getrennt; lange Inhalte scrollen vertikal. Vorschauen und Einstellungen stehen untereinander. Lange Pfade und Informationswerte umbrechen, Dateinamen in der Exportzusammenfassung werden gekürzt dargestellt.

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
| Nebenfenster | Vorschaubilder/Suche, Histogramm und Medienwiedergabe mit 520 × 760 und eigener Schließen-Aktion. |
| Stapelfortschritt | Gleicher Rahmen, sichtbare Abbruchaktion und abgedunkeltes Elternfenster. |
| Menüs | Alle sechs Hauptmenüs mit 88 Aktionen: sinnvolle Abschnittstrenner, Kürzel rechts, doppelte Kürzel aus den Beschriftungen entfernt. |
| Gemeinsame Komponenten | Helle Flächen, 24-px-Dialogradius, 24-px-Außenabstand, Karten, direkte Auswahl, Slider, Fokus, deaktivierte Zustände und schwarze Hauptaktion aus dem bestehenden Designsystem. |

## Prüfung

`tests/ui_dialog_audit.py` öffnet 49 Fälle: 33 Dialog-/Modulvarianten, zehn zusätzliche Exportformatzustände einschließlich eigener Größe und sechs Menü-Popover. Geprüft werden die tatsächlichen Fensterflächen, horizontales Überlaufen der gerenderten Kinder, aufgeklappte Zusatzoptionen und die Position der Abschlussbuttons. Der Test läuft bei 1440 × 1050 und 1024 × 640; bei letzterer Größe beträgt die gemeinsame Dialoghöhe 608 Pixel.

Der bestehende GTK-Integrationstest prüft weiterhin Bildoperationen, Vorschau, Abbrechen/Übernahme, Rückgängig, Druckausgabe und Tastaturbedienung. 108 Unit-Tests sichern die Bild- und Dateifunktionen. Die HTML-Referenz besitzt 14 Browserprüfungen einschließlich gleicher Modalgrößen und erreichbarer Fußleiste. Sie wird bei 1440 × 1050 und 390 × 1400 geprüft.

Die GTK-Geometrie wird unter Fedora 44, X11, Xvfb und Openbox überprüft. Die Screenshots verwenden ausschließlich erzeugte Testbilder. Das ist kein vollständiger Test aller realen Codecs, Drucker, Scanner, Screenreader, Skalierungsfaktoren oder der konkreten Wayland-Sitzung.

## Bewusste Systemgrenze

Linux-Datei-/Ordnerauswahl, Farb- und Schriftwahl, Drucker-/Papierauswahl sowie Portale werden vom System dargestellt. Ihre Fenstermaße und Gestaltung werden nicht von Bildblick erzwungen. Das entspricht der ausdrücklich dokumentierten Systemgrenze der Designvorlage. Die App-eigenen Auslöser und vorbereitenden Dialoge folgen dem gemeinsamen Design.

Ab 0.9.1 prüft der GTK-Funktionstest zusätzlich die kompakte Abfrage mit Speichern/Verwerfen/Abbrechen, Escape, Exportabbruch, Fortsetzung nach erfolgreichem Speichern und den Erhalt der Änderungen nach einem Schreibfehler.
