# Bildblick 0.4.0

Die native Linux-Oberfläche wurde vollständig neu gestaltet: helle Flächen,
abgerundete Karten, schwarze Hauptaktionen und eine großzügige Bildansicht.

- Rechte Bearbeitungsleiste mit vier Looks, zehn Bildreglern und RGB-Histogramm.
- Asynchrone Vorschau, Anwenden und Zurücksetzen; Übernahme in voller Auflösung.
- Neuer Exportdialog mit direkten JPG-/PNG-/WebP-Karten, Qualität und Auflösung.
- Tatsächlich berechnete Dateigröße und gemeinsamer Schalter zum Entfernen von Metadaten.
- Speicherort, weitere Formate, Spezialoptionen und Profile aufklappbar.
- Überarbeiteter Größenänderungsdialog; Strg+R bleibt erhalten.
- Kompakte Werkzeugzeile, untere Zoomsteuerung und ausblendbare Bearbeitungsleiste.
- 62 Funktionstests sowie echte GTK-Integrationstests mit Screenshots in GitHub Actions.

Das Archiv entpacken und `./install.sh` ausführen. Eine laufende ältere Version
schließen und Bildblick erneut über das Anwendungsmenü öffnen. Exportprofile bleiben
bei der Installation erhalten. Python 3, GTK 4, PyGObject, Pycairo und Pillow ab 12
werden weiterhin als Systembibliotheken benötigt.

Diese Veröffentlichung bleibt eine Vorabversion. Screenreader, andere Desktop-Themes,
HiDPI-Konfigurationen und physische Druckausgabe sind nicht umfassend validiert.
