# Menü- und Funktionsübersicht

Stand: Bildblick 0.9.2. Alle hier als verfügbar bezeichneten Menüeinträge rufen implementierte Funktionen auf. Optionale Integrationen benötigen das jeweils genannte Linux-Systemmodul. Die Hauptansicht startet mit 720 × 640 Pixeln und wächst beim manuellen Zoom bis zur verfügbaren Bildschirmfläche; Werkzeuge öffnen eigene Dialoge.

## Datei

| Menüaktion | Verhalten |
| --- | --- |
| Neues Fenster | Leeres, unabhängiges Bildfenster |
| Öffnen / Ordner öffnen | Native Dateiauswahl, Ordnernavigation |
| Erneut öffnen | Gespeicherte Datei laden, Änderungen vorher abfragen |
| Öffnen mit | Andere für das Format registrierte Linux-Anwendung wählen |
| Audio / Video öffnen | Separate GTK-Wiedergabe; Systemcodecs erforderlich |
| Dateien suchen | Namenssuche im Vorschaubildfenster des aktuellen Ordners |
| Letzte Ordner | Die letzten zehn erfolgreich gelesenen Ordner |
| Umbenennen / Verschieben / Kopieren | Gespeicherte Datei verwalten; keine vorhandenen Ziele überschreiben |
| In den Papierkorb | Nach Bestätigung über den Linux-Papierkorb; kein permanentes Löschen als Ersatz |
| Speichern | Aktuelle Datei nach Ersetzungsabfrage; neue Dokumente über Speichern unter |
| Speichern unter | Dateiname, Ordner, Format, Qualität, Auflösung, Metadaten und Profile |
| Alle Seiten exportieren | Mehrseitiges TIFF, GIF, WebP oder PDF, abhängig von Format und Seitengrößen |
| Exportoptionen | Vorgaben für spätere Ausgaben |
| Drucken | Größe, Orientierung, Skalierung, Position und nativer Druckdialog |
| Scannen | Geräteauswahl, DPI und Modus über SANE (`scanimage`) |
| Scannen und drucken | Scan übernehmen und Druckanordnung öffnen |
| Bild schließen | Anzeige leeren, Originaldatei behalten; Änderungen abfragen |
| Schließen | Fenster schließen; Änderungen abfragen |

Dateisuche ist ein Namensfilter im aktuellen Ordner, keine rekursive Volltext- oder Metadatensuche. Scannen ist Einzelbild-Erfassung; ein automatischer ADF-Stapelscan ist nicht enthalten. Druck bezieht sich auf die aktuelle Bildseite.

## Bearbeiten

| Menüaktion | Verhalten |
| --- | --- |
| Rückgängig / Wiederholen | Pixelzustände und zugehörige DPI wiederherstellen |
| Zeichnen | Sechs beschriftete Symbole: Stift, weicher Pinsel, Linie, Pfeil, Rechteck, Ellipse; Breite, Farbe, letzter Strich zurück |
| Bild einfügen | Bild aus der Zwischenablage als neues, ungespeichertes Dokument |
| Auswahl / Bild kopieren | Rechteck kopieren, ohne Auswahl das ganze Bild |
| Zwischenablage leeren | Aktuellen Inhalt der System-Zwischenablage leeren |
| Alles auswählen | Gesamte Bildfläche markieren |
| Auswahl maximieren und zentrieren | Mit gleichem Seitenverhältnis bis an den Bildrand vergrößern |
| Auswahl ausschneiden | Auswahl kopieren und auf Weiß setzen; Leinwand bleibt gleich |
| Außerhalb der Auswahl löschen | Auswahl behalten und ihre Umgebung weiß füllen |
| Einfarbige Ränder entfernen | Transparente oder gleichfarbige Außenränder mit Toleranz erkennen |
| Eigene Auswahl | Position, Abmessungen, Einheiten, DPI und feste Verhältnisse |
| Ausschnitt auswählen | Auswahlmodus aktivieren; direkte Mausauswahl funktioniert auch ohne Vorwahl |
| Zuschneiden | Auswahl als neue Bildabmessungen übernehmen |

Kanten und Ecken sind mit links veränderbar, der Rahmen mit rechts verschiebbar. Umschalt+Pfeil verschiebt um einen Pixel. **Enter** schaltet Vollbild; **Strg+Y** ist Zuschneiden; Wiederholen liegt auf **Strg+Umschalt+Z**. Eine Auswahl dient Text und Rote-Augen-Korrektur als Begrenzung. Die normalen Farbeffekte betreffen das ganze Bild.

## Bild

| Menüaktion | Verhalten |
| --- | --- |
| Größe ändern / Resample | Pixel, Prozent, cm, Zoll, DPI, Verhältnis, Vorlagen, vier Interpolationen |
| Neues Bild | Leere Bildfläche mit eigener Größe und Farbe |
| Farben reduzieren | 2–256 sichtbare RGB-Farben, wahlweise Dithering |
| Farbkanäle tauschen | Fünf alternative RGB-Reihenfolgen, Alpha erhalten |
| Histogramm | RGB-Verteilung der vollen Bildauflösung |
| 90° links / rechts | Vierteldrehung |
| Frei drehen | −360° bis 360°, erweiterte Fläche oder feste Größe, Randfarbe |
| Rote Augen korrigieren | Rot dominierte Pixel in der markierten Augenregion neutralisieren |
| Effekte | 3D-Schaltfläche, Weichzeichnen, Relief, Ölgemälde, Kanten, Median, Explosion, Pixelieren, Sepia, Regentropfen; direkte Schaltflächen, Live-Vorschau, Intensität und passende Regler, Originalvergleich |
| Leinwand erweitern | Links, rechts, oben, unten getrennt; negative Werte kürzen |
| Rahmen hinzufügen | Einfacher, doppelter oder plastischer Rahmen; Breiten und Farben |
| Horizontal spiegeln / Vertikal spiegeln | Ganze Bildfläche spiegeln |
| Graustufen / Negativ / Automatischer Kontrast | Direkte, rückgängig machbare Farboperationen |
| Bildanpassungen | Vorschau mit vier Looks und 14 Reglern, darunter Gamma und RGB-Balance |
| Helligkeit / Kontrast / Farbe | Breite Slider, Live-Vorschau und Originalvergleich für die drei Grundanpassungen |
| Schärfen / Weichzeichnen | Schärfe und Gauß-Radius per Slider mit Live-Vorschau |
| Text einfügen | Schriftfamilie, Stil, Punktgröße und Farbe; Umbruch innerhalb der Auswahl |
| Wasserzeichen | Bild unten rechts mit halber Deckkraft und begrenzter Größe einsetzen |
| Bildinformationen | I: Pfade, Format, X-/Y-DPI ändern, Original-/aktuelle Größe und Farben, Druckmaße, RGB-Farbzählung, Datei-/Pixel-Speicher, Ordnerposition, Datum, Ladezeit, Seitenzahl; EXIF/IPTC/Kommentar lesen |

Die Bearbeitung verwendet 8-Bit-RGBA. „Farben reduzieren“ erzeugt daher keine fortlaufend editierbare indizierte Palette. Schriftgrößen in Punkt werden über die Bild-DPI in Pixel umgerechnet. Eine reine DPI-Änderung verbessert keine Bilddetails. JPEG-Neukodierung ist keine verlustfreie JPEG-Transformation.

## Ansicht und Extras

- **Ansicht:** Zoom hinein/heraus, Einpassen, 100 %, Vollbild, Vorschaubilder, Diashow starten/stoppen, Intervall und Animation.
- **Extras → Ansicht einstellen:** Hintergrundfarbe und Vergrößern kleiner Bilder beim Einpassen; lokal gespeichert.
- **Extras → Bilder zusammenfügen:** Mehrere Bilder horizontal oder vertikal, mit Abstand und Hintergrund. Keine perspektivische Verschmelzung.
- **Extras → Stapelverarbeitung:** Quellen, Ziele, Namensmuster, Format, begrenzte Größenänderung, Drehung, Metadaten, Vorschau, Abbruch und Ergebnisliste.

## Ausgabeoptionen

- JPEG: Qualität 1–100, progressiv, Graustufen, 4:4:4, Zielvolumen.
- PNG: verlustfreie Kompression 0–9; höhere Stufen bedeuten keine schlechtere Qualität.
- GIF: Interlacing, 256-Farben-Grenze, binäre Transparenz; kein JPEG-artiger Qualitätsregler.
- WebP: Qualität und verlustfreier Modus.
- Weitere Formate: TIFF, BMP, ICO, PDF, JPEG 2000, PPM gemäß installiertem Pillow-Build.
- EXIF, ICC, Kommentar und XMP selektiv erhalten; keine vollständige IPTC-/Metadatenbearbeitung.
- Verkleinerte Exportdatei erstellen, ohne die Bildabmessungen des Editors zu ändern.
- DPI für JPEG, PNG, TIFF, BMP und PDF; technische Druckauflösung bleibt beim Entfernen privater Metadaten erhalten.

## Noch nicht enthalten

Kontaktbögen, HTML-Galerieexport, OCR, Bildschirmaufnahme, frei belegbare Tastenkürzel, vollständige Palettenbearbeitung/-dateien, vollständiger IPTC-Editor, nahtloses Panorama, ADF-Stapelscannen, Druck mehrerer Bildseiten in einem Auftrag, verlustfreie JPEG-Operationen und durchgehende Farbverwaltung gehören noch nicht zum Umfang. Eine Windows-Plugin-Schnittstelle, EXE-/SCR-Diashows oder eine vollständige Kompatibilität mit fremden Kommandozeilenparametern werden nicht angeboten.

Die native CLI bietet die mit `python3 cli.py --help` aufgeführten Optionen. Ein vorhandener Menüeintrag bedeutet keine gleichnamige CLI-Option.

## Prüfung

103 lokale automatisierte Tests prüfen Pixeloperationen, Metadaten, DPI-Rundreisen, Auswahlgeometrie, Druckmaße, Schrift-/Zeichenoperationen, Exporte, Controller und Decoder. Der GTK-Integrationstest prüft unter anderem Fenstergröße, Menüs, Tastenkürzel, Vorschau, physische Größenänderung, Zwischenablage, Dialoge und Druck als PDF. Reale Scanner und Drucker, distributionsabhängige Mediencodecs sowie eine vollständige Screenreader-Abnahme benötigen zusätzliche manuelle Prüfung.

## Gemeinsame Bedienung der Werkzeuge

Freie Drehung, Rahmen, Rote Augen, Farbanzahl, Farbkanäle, automatischer Zuschnitt, Leinwand und Text verwenden ebenso wie Helligkeit/Kontrast und Schärfen einen eigenen Dialog mit Live-Vorschau, Originalvergleich und Zurücksetzen. Anwenden erzeugt einen Undo-Schritt, Abbrechen lässt Bild und Historie unverändert. Visuelle Stärkeparameter haben Slider; exakte Abmessungen und Positionen bleiben Zahleneingaben. Auswahloptionen stehen als Schaltflächen bereit, darunter Zeichenwerkzeuge, Interpolation, Einheiten, Größenvorgaben, Druckmodi und Exportformate.


## Tastatur und Vollbild

Die vollständige Belegung steht in [SHORTCUTS.md](SHORTCUTS.md) und unter Hilfe → Tastenkürzel (F1). Dazu gehören kontextabhängiges Scrollen/Navigieren, 1–9-Dateisprünge, Markierungen, Zoomsperre, sechs Vollbildmodi, Maus-/Textanzeige im Vollbild sowie einblendbare Leisten. F5 aktualisiert die Ansicht, F9 steuert die Diashow. Strg+S öffnet den Speicherdialog; Enter schaltet Vollbild.
