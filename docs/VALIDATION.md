# Prüfstand von Bildblick 0.3.0

## Automatisch geprüft

Auf Fedora 44 bestehen 57 Tests mit `/usr/bin/python3 -m unittest discover -s tests -v`.

- Pixelbearbeitung, Größenänderung, Zuschnitt, Undo und Redo.
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

## Noch nicht bestätigt

Die grafische Integration konnte in der bisherigen Entwicklungsumgebung wegen gesperrter Display-Verbindungen nicht ausgeführt werden. `tests/ui_smoke.py` beendet sich dann mit Exit-Code 77. Dieser Zustand ist ausdrücklich kein bestandener GUI-Test.

Noch ausstehend sind die Sichtprüfung auf einem normalen Desktop, vollständige Maus-/Tastaturabläufe, Screenreader- und Skalierungstests sowie eine reale Druckausgabe. Die Veröffentlichung ist deshalb als frühe Vorabversion vorgesehen.
