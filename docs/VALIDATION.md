# Prüfstand von Bildblick 0.8.0

## Automatisch geprüft

Auf Fedora 44 bestehen 103 Tests mit `/usr/bin/python3 -m unittest discover -s tests -v`.

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
Der Effekte-Dialog wird mit allen zehn direkten Schaltflächen, passenden Reglern,
Intensität, Originalvergleich, Einstellungswechsel, Zurücksetzen, Abbrechen und
Anwenden mit genau einem Undo-Schritt geprüft. Verspätete Vorschau-Ergebnisse
werden vor und nach dem Schließen simuliert. Alle Effekte und Regler liegen im gemeinsamen 520-px-Dialog; umfangreiche Inhalte scrollen vertikal, die Abschlussleiste bleibt sichtbar.

Die Screenshots von Editor, Effekten, Export, kompaktem Fenster und Größenänderung wurden geprüft.
Die GUI-Prüfung verlangt eine Startgröße von exakt 720 × 640 Pixeln, eine sichtbare
Menüleiste und eine Bildfläche über nahezu die volle Fensterbreite. Sie öffnet und schließt
Bildanpassungen und Vorschaubilder als separate Fenster.

Lokal bleibt der Desktop-Zugriff eingeschränkt. Ohne Display endet `tests/ui_smoke.py`
weiterhin mit Exit-Code 77 statt einen Erfolg vorzutäuschen.

## Noch nicht bestätigt

Noch ausstehend sind eine Prüfung in der konkreten Wayland-Sitzung des Nutzers, vollständige Maus-/Tastaturabläufe, Screenreader- und HiDPI-Tests sowie reale Druck-/Scanausgaben und Mediencodec-Varianten. Die Veröffentlichung ist deshalb als frühe Vorabversion vorgesehen.

## Werkzeugdialoge ab 0.6.0

Der native GTK-Test prüft neun weitere Bearbeitungsdialoge durch direkte Änderung ihrer Bedienelemente. Die resultierenden Vorschaubilder und angewendeten Bildpixel werden mit den erwarteten Operationen verglichen. Geprüft werden außerdem Sliderwerte, gekoppelte genaue Eingaben, direkte Variantenwahl, Originalvergleich, Zurücksetzen, unverändertes Arbeitsbild vor Anwenden und nach Abbrechen sowie genau ein Undo-Schritt. Ein zusätzlicher Test verwirft veraltete und nach dem Schließen eintreffende Ergebnisse. Eine ungültige Leinwandgröße blockiert Anwenden; eine korrigierte Eingabe stellt die Vorschau wieder her. Text und neue Zeichen-/Resize-Bedienelemente sind Teil des bestehenden GTK-Ablaufs.


## Bildinformationen, Fensterwachstum und Symbole ab 0.7.0

Sechs zusätzliche Funktionstests prüfen Originaldaten nach Bearbeitung, tatsächliche EXIF-/IPTC-Lesedaten, unabhängige X-/Y-DPI mit Export-Rundreisen und Druckmaßen, fehlende Quelldaten, exakte RGB-Zählung einschließlich sehr breiter Bilder und Abbruch, Fenstergeometrie sowie weiche Pinselränder ohne Veränderung der Quelle.

Der GTK-Test öffnet die Bildinformationen über I, kontrolliert Felder, DPI-Änderung ohne neue Pixel, Farbzählung, alle drei Metadaten-Leseansichten und Rückgängig. Er prüft reales Fensterwachstum bei 100 % und weiterem Zoom, Maximierung an der Bildschirmgrenze, unveränderten Zoom und Scrollbarkeit nach Erreichen dieser Grenze. Die sechs Zeichen-Symbole, weiche Pinselstriche, Anwenden und Rückgängig werden geprüft. Screenshots der Informationsübersicht, Zeichenwerkzeuge und vergrößerten Fenster wurden visuell kontrolliert. Diese Fensterprüfung verwendet X11/Openbox; eine tatsächliche Wayland-/Mehrmonitor-/HiDPI-Prüfung bleibt offen.


## Tastaturbelegung und Designreferenz ab 0.8.0

Elf zusätzliche Funktionstests prüfen die vollständige Aktionszuordnung, genaue Modifikator-Kombinationen, kollidierende Altbelegungen, leere Dokumente, Vollbildkontext, Dateisprünge, reale Scroll-Adjustments, sechs Skalierungsarten, persistente Markierungen, Zoomsperre, Auswahlwechsel, isolierte Bildkopien und Direktdruck-Weiterleitung ohne reale Druckausgabe.

Der erweiterte GTK-Test prüft Vollbildwechsel über Enter/Escape, Strecken/Breite/Höhe, Maus- und Bildtextanzeige, Leisten, Scrollen ohne Dateisprung, Zoomsperre über einen Ladevorgang, Markierungen und Filter, Tastaturhilfe, Dateinamen-Zwischenablage und Strg+S-Speicherdialog. Die Monitorüberspannung wird als GDK-Anforderung geprüft; ein tatsächliches Mehrmonitor-/Wayland-Setup bleibt ungeprüft.

Die Designreferenz wurde als alleinstehende HTML-Datei in einem fremden Ordner geprüft. Ihre 13 Browserprüfungen bestehen bei 1440 px und 390 px Breite; Screenshots wurden kontrolliert. CSS und JavaScript sind eingebettet. Ein vollständiger TypeScript-Typcheck und eine Screenreader-Abnahme bleiben offen.

## Einheitliche Dialoge

Der vollständige Abgleich, die erfassten Module und die Systemgrenze stehen in [UI-AUDIT.md](UI-AUDIT.md). Die gerenderten Größen und Inhalte werden durch `tests/ui_dialog_audit.py` zusätzlich zum funktionalen Integrationstest geprüft.
