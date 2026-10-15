# Bildblick 0.5.0 – Werkzeuge und Menüs

Das kompakte Hauptfenster startet weiterhin mit 720 × 640 Pixeln. Zusätzliche Funktionen öffnen eigene Dialoge im hellen, monochromen Design.

## Neue Bearbeitungsabläufe

- Direkt aufgezogene Auswahl mit veränderbaren Kanten, Rechtsziehen zum Verschieben, Verhältnis- und Maßvorgaben.
- Auswahl/Bild kopieren, einfügen und ausschneiden; unabhängige neue Fenster und neue leere Bilder.
- Resize in Pixel, Prozent, cm und Zoll, DPI, Auflösungsvorgaben und Bildschirmgröße. Korrektes Bestätigen gerundeter physischer Maße ohne Pixelsprung.
- Freie Drehung, Gamma/RGB-Balance, Rote Augen, zehn Effekte, Farbreduktion, Kanaltausch und Histogramm.
- Einfache/doppelte/plastische Rahmen, getrennte Leinwandränder einschließlich negativer Randwerte.
- Schriftfamilien, Stile, Punktgröße und Farbe mit Textumbruch im Auswahlrechteck.
- Eigener Zeichendialog mit Stift, Linie, Pfeil, Rechteck und Ellipse.
- Horizontales/vertikales Zusammenfügen mit Abstand und Hintergrund.

## Dateien und Ausgabe

Erneut öffnen, externe Anwendungen, Namenssuche, letzte Ordner, Umbenennen, Kopieren, Verschieben und Papierkorb sind im Menü erreichbar. Dateiziele werden nicht still überschrieben. Druck bietet Orientierung, cm-Größe, Skalierung und Position vor dem nativen Druckdialog. Scanner verwenden optional SANE; lokale Medien optional GTK/GStreamer.

**Geänderte Kürzel:** Strg+Y schneidet zu; Strg+Umschalt+Z wiederholt. Strg+S speichert die aktuelle Datei mit Ersetzungsabfrage. S und Strg+Umschalt+S öffnen Speichern unter. Strg+R bleibt Größe ändern.

82 automatisierte Tests prüfen Bild-, Export-, DPI-, Auswahl- und Drucklogik. Der GTK-Integrationstest deckt die neuen Dialoge, Zwischenablage und PDF-Druck zusätzlich ab. Physische Scanner-/Druckerausgaben und alle Mediencodecs sind noch nicht manuell abgenommen. Der genaue Umfang und die offenen Spezialfunktionen stehen in `docs/FEATURES.md`.

Installation: Archiv entpacken, `./install.sh` ausführen, eine alte laufende App schließen und Bildblick erneut öffnen. Das Paket benötigt die in der README genannten Linux-Systembibliotheken; es ist kein eigenständiges AppImage.
