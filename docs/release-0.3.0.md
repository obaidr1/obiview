# Bildblick 0.3.0

Bildblick bringt lokale Bildanzeige, grundlegende Bearbeitung und gezielte Exportoptionen auf den Linux-Desktop.

## Enthalten

- GTK-4-Oberfläche mit Ordnernavigation, Vorschaubildern, Zoom und Vollbild.
- Drehen, Zuschneiden, Größenänderung mit `Strg+R`, Farbkorrekturen und Undo/Redo.
- Speichern unter mit JPEG-/GIF-/PNG-/WebP-Optionen, Metadaten-Schaltern und benannten Profilen.
- JPEG-Dateigrößenlimit mit Fehlerbehandlung, wenn die gewünschte Größe nicht erreichbar ist.
- Stapelverarbeitung und CLI mit Vorschau, JSON-Ergebnissen und Kollisionsschutz.
- Seiten-/Framewechsel, Diashow und Mehrseitenexport.
- Benutzerinstallation mit Anwendungsmenü-Eintrag und neuem Eisvogel-Symbol.
- Ausführliche README, Produktdokumentation und MIT-Lizenz.

## Installation

`Bildblick-0.3.0-linux.tar.gz` herunterladen, entpacken und `./install.sh` ausführen. Danach Bildblick über das Anwendungsmenü starten.

Das Paket benötigt vorhandene Systembibliotheken: Python 3, GTK 4, PyGObject, Pycairo und Pillow ab Version 12. Es enthält keine gebündelte Laufzeit. Fedora 44 ist das Referenzsystem. Die SHA-256-Datei erlaubt die Kontrolle des heruntergeladenen Archivs.

## Prüfstand und bekannte Grenzen

57 automatische Tests bestehen auf dem Referenzsystem. Eine sichtbare GUI-Abnahme und physische Druckausgabe sind noch offen; diese frühe Version ist entsprechend als Vorabversion gekennzeichnet.

Die Bearbeitung erfolgt mit 8-Bit-RGBA. Keine Ebenen, kein vollständiger Farbmanagement-Workflow und keine verlustfreie JPEG-Bearbeitung. Metadatenübernahme und zusätzliche Bildformate sind abhängig von Format und installierten Decodern. Weitere Einzelheiten stehen in README.md und PRODUCT.md.
