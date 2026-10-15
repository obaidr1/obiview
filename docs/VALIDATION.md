# Prüfstand von Bildblick 0.5.0

## Automatisch geprüft

Auf Fedora 44 bestehen 86 Tests mit `/usr/bin/python3 -m unittest discover -s tests -v`.

- Pixelbearbeitung, Größenänderung, Zuschnitt, Undo und Redo.
- Physische Größen, DPI-Export mit erneutem Einlesen in JPEG/PNG/TIFF/BMP und DPI-Undo.
- Auswahlkanten, Verschieben, Rote Augen, zehn Effekte, Rahmen und getrennte Leinwandränder.
- Effektintensität: 0/50/100 Prozent, erhaltenes Alpha, unveränderte Quelle, gültige Parametergrenzen und abgewiesene ungültige Werte.
- Fontconfig-Schriftwahl, Textbegrenzung, Zeichenformen, Palettenreduktion und RGB-Tausch.
- Druckgeometrie für Einpassen, cm, Prozent und Position sowie nativer Zwischenablage-Datentyp.
- Alle neuen Regler und Looks: veränderte Pixel, erhaltenes Alpha, deterministische Körnung.
- Exportauflösung für PNG, JPEG, WebP und GIF ohne Änderung der Arbeitsdatei.
- Menüaktionen und Weiterleitung von `Strg+R` ohne Display.
- Exportdateien mit überprüften Pixelmaßen und Decoder-Roundtrips.
- JPEG-Qualität, progressive Speicherung, Farbunterabtastung und Graustufen.
- JPEG-Dateigrößenlimit einschließlich eines nicht erfüllbaren Limits.
- GIF-Interlacing und Transparenz, PNG-Kompression und verlustfreies WebP.
- EXIF, ICC, Kommentar und XMP mit einzeln überprüften Schaltern.
- Benannte Profile, beschädigte Profilkonfigurationen und Dateinamenprüfung.
- Kollisionsschutz, unveränderte Ziele bei Encoderfehlern und Stapelvorschau.
- Konkurrierende Ordnerabfragen und ausgewählte native Decoder.

Die nativen Testdateien werden während der Tests erzeugt. Für einzelne Kamera- und Spezialformatvarianten bedeutet dies keine umfassende Kompatibilitätszusage.

## Paket und Installation

Die Paketprüfung umfasst Archiv-Prüfsummen, eine Installation in ein temporäres Verzeichnis, erneute Installation, Starter-Aufruf und eine tatsächliche CLI-Konvertierung. Die Desktop-Datei wird mit `desktop-file-validate` geprüft. Installationspfade mit Leerzeichen und Sonderzeichen sind berücksichtigt.

Das Symbol besitzt einen transparenten Hintergrund. Eine kleine gerenderte Vorschau wurde geprüft. Der Installer installiert das Symbol und aktualisiert den Icon-Cache, wenn das entsprechende Systemprogramm verfügbar ist.

## Grafische Integration

Die GTK-Prüfung läuft erfolgreich unter Fedora 44 mit Xvfb, Openbox und dem Cairo-Renderer
in GitHub Actions. Sie prüft Laden, Zoom, Drehen, Zuschnitt, Rückgängig/Wiederholen,
Datei- und Seitennavigation, Diashow, Vollbild, Menüaktionen, Strg+R, Speicherdialog,
Vorschau, Zurücksetzen, Übernahme von Looks und verkleinerten Export.
Zusätzlich werden cm-/DPI-Resize, unveränderte Pixel beim Kopieren einer Auswahl,
Einfügen/Speichern ohne Quelldatei, Rote Augen, Rahmen, freie Drehung, Text,
Gamma/RGB, dauerhafte Ansichtsoptionen, PDF-Druck, Dateiumbenennung, Palette,
Zeichnen und die getrennten Kürzel für Zuschnitt und Redo geprüft.

Die Screenshots von Editor, Export, kompaktem Fenster und Größenänderung wurden geprüft.
Die GUI-Prüfung verlangt eine Startgröße von exakt 720 × 640 Pixeln, eine sichtbare
Menüleiste und eine Bildfläche über nahezu die volle Fensterbreite. Sie öffnet und schließt
Bildanpassungen und Vorschaubilder als separate Fenster.

Lokal bleibt der Desktop-Zugriff eingeschränkt. Ohne Display endet `tests/ui_smoke.py`
weiterhin mit Exit-Code 77 statt einen Erfolg vorzutäuschen.

## Noch nicht bestätigt

Noch ausstehend sind eine Prüfung in der konkreten Wayland-Sitzung des Nutzers, vollständige Maus-/Tastaturabläufe, Screenreader- und HiDPI-Tests sowie reale Druck-/Scanausgaben und Mediencodec-Varianten. Die Veröffentlichung ist deshalb als frühe Vorabversion vorgesehen.
