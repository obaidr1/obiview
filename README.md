<p align="center">
  <img src="assets/bildblick-kingfisher.png" width="160" alt="Bildblick: ein Eisvogel in Blau und Orange">
</p>

# Bildblick

**Bilder ansehen, schnell bearbeiten und gezielt exportieren – direkt auf deinem Linux-Desktop.**

Bildblick ist eine lokale Desktop-Anwendung mit GTK 4. Du kannst durch Bildordner blättern, Bilder zuschneiden oder skalieren, Farben anpassen und Ergebnisse mit passenden Formatoptionen speichern. Für wiederkehrende Aufgaben gibt es Stapelverarbeitung, benannte Exportprofile und eine Kommandozeilenschnittstelle.

Die Oberfläche ist deutschsprachig. Ein Konto oder Cloud-Dienst ist für die Bildbearbeitung nicht erforderlich.

**Stand: 0.3.0 · frühe Version · MIT-Lizenz · Referenzsystem: Fedora 44**

## Inhalt

- [Funktionen](#funktionen)
- [Installation](#installation)
- [Erste Schritte](#erste-schritte)
- [Tastenkürzel](#tastenkürzel)
- [Größe ändern](#größe-ändern)
- [Speichern und Exportprofile](#speichern-und-exportprofile)
- [Stapelverarbeitung und CLI](#stapelverarbeitung-und-cli)
- [Formate und Mehrseiten-Dateien](#formate-und-mehrseiten-dateien)
- [Datenspeicherung und Grenzen](#datenspeicherung-und-grenzen)
- [Entwicklung und Tests](#entwicklung-und-tests)
- [Fehler melden und mitarbeiten](#fehler-melden-und-mitarbeiten)

Das [Produktdokument](PRODUCT.md) beschreibt Zielgruppe, Bedienkonzept, Produktumfang und nächste Entwicklungsschritte.

## Funktionen

| Bereich | Verfügbar |
| --- | --- |
| Anzeige | Zoom, Einpassen, 100-%-Ansicht, Vollbild, Transparenzraster |
| Navigation | Ordner öffnen, natürlich sortierte Dateinamen, Vorschaubilder, Namensfilter |
| Bearbeitung | Drehen, Spiegeln, Zuschneiden, Größe ändern, Rückgängig und Wiederholen |
| Farben und Details | Graustufen, Negativ, Autokontrast, Helligkeit, Kontrast, Sättigung, Schärfen, Weichzeichnen |
| Ergänzungen | Text mit Position, Größe und Farbe; Bildwasserzeichen |
| Export | Formatwahl, JPEG-/GIF-/PNG-/WebP-Optionen, Metadaten-Schalter, Profile |
| Serien | Stapelkonvertierung, skalierte Ausgaben, umbenannte Kopien, Vorschau und Abbruch |
| Mehrere Seiten | Seiten-/Framewechsel, Animation, Export nach TIFF, GIF, WebP oder PDF |
| Desktop | Anwendungsmenü, eigenes Symbol, „Öffnen mit“, GTK-Druckdialog |
| Automatisierung | CLI mit JSON-Ergebnis, Vorschau und Fehlerstatus |

Die Druckanbindung ist implementiert; eine physische Druckausgabe wurde bislang nicht bestätigt. Auch die vollständige grafische Bedienprüfung steht noch aus. Details zum Teststand findest du unter [Entwicklung und Tests](#entwicklung-und-tests).

## Installation

### Voraussetzungen

Bildblick benötigt eine grafische Linux-Sitzung und folgende Systembibliotheken:

| Komponente | Zweck |
| --- | --- |
| `/usr/bin/python3` | Anwendung und Installer ausführen |
| GTK 4 und PyGObject | Native Fenster und Dialoge |
| Pycairo | Bildfläche und Druckanbindung |
| Pillow ab Version 12 | Bildoperationen und Standard-Codecs |
| GdkPixbuf | Darstellung von Bilddaten und Symbolen |

Auf dem Referenzsystem wurden Python 3.14, GTK 4.22 und Pillow 12.3 verwendet. Andere Distributionen können funktionieren, sind jedoch noch nicht als vollständige Konfiguration geprüft.

Fedora-Pakete für die Grundausstattung:

```bash
sudo dnf install python3 python3-gobject python3-cairo python3-pillow gtk4
```

Zusätzliche Formate nutzen optional installierte Decoder:

```bash
sudo dnf install ImageMagick poppler-utils ffmpeg-free util-linux
```

Die Ausgabeformate und Zusatzdecoder hängen von den tatsächlich vorhandenen Codec-Builds ab. Der Installer lädt keine Abhängigkeiten herunter und installiert keine Systempakete.

### Fertiges Paket installieren

1. `Bildblick-0.3.0-linux.tar.gz` aus den [GitHub-Releases](https://github.com/obaidr1/obiview/releases) herunterladen.
2. Archiv entpacken.
3. Im entpackten Ordner `install.sh` ausführen.
4. Im Anwendungsmenü nach **Bildblick** suchen.

```bash
tar -xzf Bildblick-0.3.0-linux.tar.gz
cd Bildblick-0.3.0
./install.sh
```

Die Installation erfolgt im eigenen Benutzerkonto und benötigt kein `sudo`. Ein vorhandener Standard-Bildbetrachter bleibt unverändert. Bildblick wird zusätzlich als Anwendung unter **Öffnen mit** angeboten.

Das Archiv enthält Anwendungscode, Dokumentation und Symbol. Die Python-/GTK-Laufzeit wird vom System bereitgestellt; das Paket ist kein eigenständiges AppImage.

### Aus dem Quellcode starten oder installieren

Im Projektverzeichnis:

```bash
./start.sh
./start.sh /pfad/zum/bild.jpg
./start.sh /pfad/zum/bildordner
```

Für einen dauerhaften Menüeintrag:

```bash
/usr/bin/python3 packaging/install.py --source .
```

Nach einer Aktualisierung eine laufende Instanz schließen und Bildblick erneut über das Anwendungsmenü öffnen. Änderungen im Quellcodeverzeichnis werden erst nach erneutem Installieren in die installierte Kopie übernommen.

### Installationsorte

| Inhalt | Standardpfad |
| --- | --- |
| Anwendungsdateien | `~/.local/share/bildblick/app/` |
| Terminal-Starter | `~/.local/bin/bildblick` |
| Menüeintrag | `~/.local/share/applications/local.bildblick.Viewer.desktop` |
| Symbol | `~/.local/share/icons/hicolor/scalable/apps/local.bildblick.Viewer.svg` |
| Exportprofile | `~/.config/bildblick/save-profiles.json` |

`XDG_DATA_HOME` und `XDG_CONFIG_HOME` werden für die entsprechenden Daten- und Konfigurationsorte berücksichtigt. Der Terminal-Starter liegt unabhängig davon unter `~/.local/bin`.

Zur Deinstallation die oben genannten Anwendungsdateien, den Starter, Menüeintrag und das Symbol entfernen. Exportprofile können separat aufbewahrt werden. Eigene Bilddateien liegen außerhalb der Installation.

## Erste Schritte

1. **Bild öffnen:** `Strg+O` verwenden oder eine einzelne Datei ins Fenster ziehen.
2. **Ordner durchsuchen:** Über **Datei → Ordner öffnen** einen Bildordner wählen. Vorschaubilder lassen sich im Menü **Ansicht** einblenden und nach Dateinamen filtern.
3. **Ansicht einstellen:** Mit `F` einpassen, mit `1` auf 100 % wechseln oder mit `+` und `−` zoomen.
4. **Bearbeiten:** Eine Auswahl aufziehen und zuschneiden, das Bild drehen oder mit `Strg+R` die Pixelgröße ändern.
5. **Speichern:** Mit `Strg+Umschalt+S` Dateiname, Zielordner, Format und Optionen festlegen.

Beim Wechseln zu einem anderen Bild oder beim Schließen fragt Bildblick nach, wenn ungespeicherte Änderungen vorhanden sind. Speichern erfolgt erst durch eine ausdrückliche Speicheraktion.

## Tastenkürzel

| Kürzel | Aktion |
| --- | --- |
| `Strg+O` | Bild öffnen |
| `Strg+S`, `Strg+Umschalt+S` | Speichern unter |
| `Strg+R` | Größe ändern |
| `Strg+Z` / `Strg+Y` | Rückgängig / Wiederholen |
| `Strg+P` | Drucken |
| `R` | 90° im Uhrzeigersinn drehen |
| `+` / `−` | Vergrößern / Verkleinern |
| `F` / `1` | Einpassen / 100 % |
| `←` / `→` | Vorherige / nächste Datei im Ordner |
| `Bild auf` / `Bild ab` | Vorherige / nächste Seite oder Frame |
| `Enter` | Aktuelle Auswahl zuschneiden |
| `Esc` | Auswahlmodus verlassen |
| `F5` | Diashow starten oder stoppen |
| `F11` | Vollbild umschalten |

## Größe ändern

**Bild → Größe ändern**, der sichtbare Größen-Button und `Strg+R` öffnen denselben Dialog.

- Breite und Höhe lassen sich in **Pixeln** oder **Prozent** eingeben.
- Bei aktiviertem Seitenverhältnis passt die Änderung eines Feldes das andere an.
- Prozentwerte beziehen sich auf die Bildgröße beim Öffnen des Dialogs.
- Vorlagen bieten 25, 50, 75, 100, 150 und 200 Prozent.
- Als Interpolation stehen Lanczos, bikubisch, bilinear und nächster Nachbar bereit.
- Die Zielgröße und Megapixelzahl werden vor dem Anwenden angezeigt.

Die Größenänderung verändert den Bearbeitungsstand und kann rückgängig gemacht werden. Eine Änderung des Zoomfaktors verändert dagegen nur die Ansicht.

## Speichern und Exportprofile

Der Speicherdialog enthält Dateiname, Zielordner, Formatauswahl und passende Optionen. Der vorgeschlagene Name lautet `<name>-bearbeitet` im unterstützten Quellformat; andernfalls wird PNG verwendet. Die Dateiendung wird an das ausgewählte Format angepasst.

### Formatoptionen

| Format | Einstellmöglichkeiten |
| --- | --- |
| JPEG | Qualität 1–100, progressive Ausgabe, Graustufen, Farbunterabtastung deaktivieren (4:4:4), maximales Dateivolumen |
| GIF | Interlacing, Transparenz erhalten oder auf Weiß reduzieren |
| PNG | Verlustfreie Kompression von 0 bis 9 |
| WebP | Qualität und verlustfreier Modus |
| TIFF, BMP, ICO, PDF, JPEG 2000, PPM | Ausgabe mit den jeweiligen Standardoptionen |

Das JPEG-Größenlimit wird in **KiB** angegeben: 1 KiB entspricht 1.024 Bytes. Bildblick reduziert bei Bedarf die Qualität unterhalb des gewählten Ausgangswerts. Ist das Limit selbst bei Qualität 1 nicht erreichbar, schlägt der Export mit einer verständlichen Meldung fehl; eine vorhandene Zieldatei bleibt erhalten. Das Limit verändert nicht automatisch die Pixelmaße.

GIF unterstützt höchstens 256 Farben und nur binäre Transparenz. Bei aktivierter Transparenz werden Pixel mit Alpha unter 50 % transparent. Die übrigen Pixel werden bei Teiltransparenz mit Weiß verrechnet. Interlacing wird vom verwendeten Encoder erst ab 16 × 16 Pixeln eingesetzt.

JPEG, BMP, PDF und PPM erhalten bei Transparenz einen weißen Hintergrund. ICO-Ausgaben werden auf die unterstützten Icon-Größen reduziert. Exportoptionen wie JPEG-Graustufen verändern das Bild im Editor nicht.

### Metadaten

EXIF, ICC-Farbprofil, Original-Kommentar und XMP lassen sich getrennt übernehmen. Nur Daten, die eingelesen wurden und vom Zielformat unterstützt werden, können erhalten bleiben.

| Daten | Unterstützte Einzelbild-Ausgaben |
| --- | --- |
| EXIF | JPEG, PNG, WebP |
| ICC | JPEG, PNG, WebP, TIFF, PDF, soweit vom Encoder unterstützt |
| Kommentar | JPEG, GIF |
| XMP | JPEG, WebP |

Die EXIF-Ausrichtung wird beim Laden normalisiert. Ein ursprüngliches RGB-Farbprofil wird nicht an ein Graustufen-JPEG angehängt. IPTC, eingebettete Vorschaubilder und spezielle Formatmetadaten werden nicht vollständig erhalten. Bildblick enthält keinen Metadaten-Editor.

### Profile

Im Bereich **Profile** einen Namen eingeben und die aktuellen Einstellungen speichern. **Laden** übernimmt ein vorhandenes Profil; **Löschen** entfernt es. Ein vorhandener Name wird beim Speichern aktualisiert.

Profile enthalten Format und Speicheroptionen, jedoch keine Bilddateien oder Zielpfade. Sie bleiben nach einem Neustart erhalten. Die zuletzt gewählten Optionen ohne benanntes Profil gelten nur für die laufende Sitzung.

## Stapelverarbeitung und CLI

Unter **Extras → Stapelverarbeitung** werden Quelldateien, Zielordner, Format, maximale Größe und Namensvorlage gewählt. Vor dem Start zeigt Bildblick die Zuordnung von Quell- zu Zieldateien. Existierende Ziele und Namenskollisionen werden abgelehnt.

Erlaubte Platzhalter sind `{stem}`, `{index}` und numerisch formatierte Indizes wie `{index:04d}`. Beispiel: `Urlaub-{index:04d}-{stem}`.

Der Modus `copy` erstellt umbenannte, bitgenaue Kopien. Die Bildkonvertierung kann zusätzlich skalieren und um 90° drehen. Ein Abbruch beendet die Verarbeitung nach der aktuellen Datei. Mehrseitige Quellen werden bei einer Einzelbild-Konvertierung abgelehnt, damit Seiten nicht unbemerkt entfallen.

### Vorschau ohne Dateien zu schreiben

Der Zielordner muss bereits existieren:

```bash
/usr/bin/python3 cli.py ./bilder --output ./export \
  --format jpg --max-width 1920 --quality 90 \
  --pattern 'Bild-{index:04d}' --dry-run
```

Ohne `--dry-run` wird der geplante Auftrag ausgeführt. Ordner werden ohne Unterordner eingelesen. Mehrere Dateien und Ordner können gemeinsam als Quellen angegeben werden.

### Weitere Beispiele

```bash
# In ein 1600 × 1200 großes Rechteck einpassen, ohne kleine Bilder hochzuskalieren
/usr/bin/python3 cli.py foto.png --output ./export \
  --format webp --max-width 1600 --max-height 1200

# Bitgenaue Kopien mit fortlaufenden Namen
/usr/bin/python3 cli.py ./bilder --output ./kopien \
  --format copy --pattern 'Archiv-{index:04d}-{stem}'

# JPEG-Ausgaben ohne übernommene Metadaten
/usr/bin/python3 cli.py ./bilder --output ./export \
  --format jpg --quality 85 --strip-metadata
```

Die CLI schreibt JSON mit Quellpfad, Zielpfad und Ergebnis. Exit-Code `0` bedeutet Erfolg, `1` mindestens einen Fehler während der Verarbeitung und `2` einen Fehler bei Argumenten oder Planung. Der erweiterte Speicherdialog und seine Profile werden nicht vollständig durch CLI-Parameter abgebildet.

## Formate und Mehrseiten-Dateien

Standardformate werden über Pillow gelesen. Weitere Formate nutzen vorhandene native Decoder. Eine erkannte Dateiendung garantiert nicht, dass jede Variante des Formats unterstützt ist.

| Bereich | Stand |
| --- | --- |
| PNG, JPEG, WebP, GIF, BMP, TIFF | Zentrale Lese-/Schreibformate |
| ICO, JPEG 2000, PPM | Export über die installierten Pillow-Codecs |
| PDF | Lesen über Poppler mit Rasterisierung bei 150 dpi; Raster-PDF-Ausgabe |
| SVG/SVGZ | Rasterisierung über einen vorhandenen ImageMagick-SVG-Decoder |
| JPEG XL, EXR, DPX, CIN, MNG | Zusatzdecoder mit erzeugten Testdateien geprüft |
| AVIF | Native Dekodierung einfacher Standbilder und Animationen geprüft |
| RAW, DICOM, XCF, WPG | Je nach System gemeldete Decoder; keine umfassende Variantenprüfung |
| HEIC/HEIF | In der Referenzkonfiguration nicht unterstützt |

Bei mehrseitigen Dateien zeigt Bildblick die aktuelle Seite beziehungsweise den aktuellen Frame. **Speichern unter** exportiert nur diese Seite und verhindert damit das Überschreiben des mehrseitigen Originals am ursprünglichen Quellpfad.

**Datei → Alle Seiten exportieren** kombiniert die aktuell bearbeitete Seite mit den übrigen Originalseiten. TIFF, GIF, WebP und PDF sind als Ziele vorgesehen. GIF/WebP erfordern identische Framegrößen. Animationsausgaben laufen in einer Endlosschleife.

Es gibt derzeit kein Dokumentmodell, das beliebig viele separat bearbeitete Seiten gleichzeitig verwaltet. Ein Mehrseitenexport markiert den einzelnen Bearbeitungsstand nicht als gespeichert.

## Datenspeicherung und Grenzen

Bildblick verarbeitet Bilder lokal. Die Anwendung enthält keinen Kontozwang, Cloud-Upload, Telemetrie-Client oder automatischen Update-Download. Externe Decoder werden als lokale Prozesse aufgerufen.

Ausgabedateien werden zunächst im Zielverzeichnis vollständig temporär geschrieben. Erst danach wird das Ergebnis veröffentlicht. Das Ersetzen vorhandener Dateien verlangt im Dialog eine Bestätigung; Stapelverarbeitung überschreibt vorhandene Ziele nicht.

Aktuelle Grenzen:

- Bearbeitung intern mit 8-Bit-RGBA; keine Ebenen oder durchgehende HDR-/16-Bit-Verarbeitung.
- Bis zu 20 Undo-Schritte, bei großen Bildern durch das Speicherbudget reduziert.
- Größenänderungen und normale Bildladung auf höchstens 80 Megapixel begrenzt; native Zusatzdecoder haben strengere Grenzen.
- Native Decoder begrenzen Laufzeit, Speicher und Dateigröße; große Eingaben können abgelehnt werden.
- Vektorgrafiken und PDF-Seiten werden gerastert. Externe relative SVG-Ressourcen werden nicht übernommen.
- AVIF-Hilfsbilder und bestimmte Alpha-Varianten werden nicht vollständig unterstützt.
- Kein validierter, monitorprofilierter Farbmanagement-Workflow.
- JPEG wird neu kodiert; keine verlustfreie JPEG-Rotation oder automatische Ermittlung der Originalqualität.
- Keine freien Malwerkzeuge, Rote-Augen-Korrektur, Scanner- oder Bildschirmaufnahme.
- Druckausgabe, sichtbare Desktop-Integration und sämtliche Maus-/Tastaturabläufe benötigen noch eine vollständige manuelle Prüfung.

## Entwicklung und Tests

### Projektaufbau

| Datei/Ordner | Aufgabe |
| --- | --- |
| `bildblick.py` | Fenster, Zeichenfläche, Öffnen/Speichern und Eingabe |
| `advanced_ui.py`, `menus.py` | Menüaktionen, Navigation, Dialoge und Hintergrundaufträge |
| `image_model.py` | Bildzustand, Bearbeitung, Undo/Redo und Seitenexport |
| `image_export.py`, `save_options.py`, `save_dialog.py` | Encoderoptionen, Profile und Speicherdialog |
| `resize_settings.py`, `resize_dialog.py` | Größenberechnung und Größenänderungsdialog |
| `native_codecs.py` | Begrenzte Aufrufe zusätzlicher Decoder |
| `batch.py`, `cli.py` | Auftragsplanung und Stapelverarbeitung |
| `assets/` | Eisvogel-Symbol und zugehörige Asset-Dokumentation |
| `packaging/` | Benutzerinstallation, Paketbau und Veröffentlichung |
| `tests/` | Modell-, Controller-, Export- und Decoder-Prüfungen |

### Automatische Tests

```bash
/usr/bin/python3 -m unittest discover -s tests -v
```

Auf dem Referenzsystem bestehen **57 Tests**. Geprüft werden unter anderem tatsächliche Exportdateien, Pixeloperationen, JPEG-Optionen, GIF-Transparenz, Metadaten-Schalter, Profile, Zielkollisionen und native Decoder. Auf anderen Systemen können codecabhängige Prüfungen übersprungen werden.

### Grafischer Integrationstest

```bash
PYTHONPATH=. GDK_BACKEND=x11 GSK_RENDERER=cairo xvfb-run -a \
  -s '-screen 0 1280x900x24' /usr/bin/python3 tests/ui_smoke.py
```

Dieser Test benötigt eine erreichbare grafische Umgebung. Ohne Display endet er mit Status `77`, nicht mit einem erfolgreichen Test. In der bisherigen eingeschränkten Entwicklungsumgebung war die Display-Verbindung blockiert. Ein bestandener Modelltest ersetzt deshalb keine bestätigte Sichtprüfung der Oberfläche.

### Paket bauen

```bash
/usr/bin/python3 packaging/build.py
```

Der Build erzeugt `dist/Bildblick-0.3.0-linux.tar.gz` und die zugehörige SHA-256-Datei. Das Archiv enthält zusätzlich eine Liste der Prüfsummen seiner Dateien. Die Benutzerdaten und Exportprofile werden nicht eingepackt.

Der GitHub-Workflow prüft Änderungen auf `main` in einem Fedora-Container,
baut das Paket und veröffentlicht die Vorabversion, sofern der Versionstag
noch keinen Release besitzt. Bereits veröffentlichte Dateien werden dabei
nicht ersetzt. Für künftige Versionen müssen Versionsnummern in Paketbau,
Veröffentlichungsskript, Workflow und Release-Text gemeinsam aktualisiert werden.

## Fehler melden und mitarbeiten

Bitte bei Fehlerberichten Distribution, Python-/GTK-/Pillow-Version, Bildformat, erwartetes Verhalten und nachvollziehbare Schritte angeben. Beispieldateien nur teilen, wenn du sie veröffentlichen möchtest; Bildmetadaten können persönliche Informationen enthalten.

Beiträge sollten einen klaren Anwendungsfall behandeln und passende Prüfungen mitbringen. Funktionsversprechen müssen zwischen implementiert, automatisch geprüft und manuell bestätigt unterscheiden. Die nächste Produktentwicklung steht in [PRODUCT.md](PRODUCT.md).

## Lizenz und verwendete Komponenten

Bildblick wird unter der [MIT-Lizenz](LICENSE) veröffentlicht. Das Eisvogel-Symbol wurde generiert; der [Asset-Prompt](assets/ICON_PROMPT.txt) ist dokumentiert. Die installierten Bibliotheken und optionalen Decoder bleiben eigenständige Komponenten mit ihren jeweiligen Lizenzen; sie werden nicht in das Anwendungspaket gebündelt.
