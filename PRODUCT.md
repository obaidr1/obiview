# Bildblick – Produktbeschreibung

## Kurzbeschreibung

Bildblick ist eine native Linux-Anwendung für das Ansehen, einfache Bearbeiten und gezielte Exportieren von Bildern. Sie verbindet eine direkt bedienbare Bildfläche mit nachvollziehbaren Speicheroptionen und einer kleinen Automatisierungsschicht für wiederkehrende Aufgaben.

Die aktuelle Version 0.10.0 richtet sich an Menschen, die Bilder auf dem eigenen Rechner bearbeiten möchten. Der Schwerpunkt liegt auf alltäglichen Abläufen: eine Datei öffnen, prüfen, drehen oder zuschneiden, die Ausgabegröße festlegen und das Ergebnis im gewünschten Format speichern.

Die Anwendung ist in einer frühen Entwicklungsphase. Dieses Dokument beschreibt sowohl den verfügbaren Umfang als auch die noch ausstehende Produktarbeit. Geplante Funktionen sind keine Zusage, dass sie bereits implementiert sind.

## Problem und Nutzen

Ein einzelnes Bild für eine Nachricht, eine Webseite oder eine Dokumentation vorzubereiten sollte wenig Aufwand erfordern. In diesem Ablauf sind drei Dinge besonders wichtig:

1. Die aktuelle Datei und ihr Bearbeitungsstand müssen erkennbar sein.
2. Häufige Aktionen müssen ohne lange Suche erreichbar sein.
3. Beim Export müssen Format, Dateigröße und Metadaten verständlich steuerbar sein.

Bildblick bündelt diese Aufgaben in einer Desktop-Anwendung. Kleine Bildserien können im gleichen Arbeitsumfeld verarbeitet werden; größere wiederkehrende Abläufe lassen sich über die CLI anstoßen.

## Zielgruppen

| Zielgruppe | Typische Aufgabe | Nutzen |
| --- | --- | --- |
| Linux-Anwender im Alltag | Bilder ansehen, drehen und weitergeben | Kurzer Weg von der Datei zum gespeicherten Ergebnis |
| Menschen mit Dokumentationsaufgaben | Bildausschnitte und passende Auflösungen vorbereiten | Präzise Pixelmaße, Text und wiederverwendbare Exportoptionen |
| Web- und Content-Arbeit | Kleinere JPEG-/WebP-Ausgaben erzeugen | Qualitätskontrolle und optionales JPEG-Größenlimit |
| Nutzer kleiner Bildarchive | Ordner sichten und Dateien einheitlich exportieren | Vorschaubilder, natürliche Sortierung und Stapelverarbeitung |
| Technische Anwender | Wiederholbare Konvertierungen automatisieren | Vorschau, JSON-Ergebnisse und Prozess-Exit-Codes |

Professionelle Druckvorstufe, medizinische Diagnose, komplexe Fotoretusche und die Bearbeitung von Ebenendokumenten gehören nicht zum bestätigten Einsatzumfang.

## Produktprinzipien

### Lokal arbeiten

Die wesentlichen Bildoperationen finden auf dem eigenen Rechner statt. Es gibt keinen erforderlichen Account und keine Upload-Stufe im Bearbeitungsablauf. Native Zusatzdecoder werden als lokale Programme verwendet.

### Aktionen sichtbar und per Tastatur erreichbar machen

Die dauerhaft sichtbare Menüleiste gliedert sich in **Datei**, **Bearbeiten**, **Bild**, **Ansicht** und **Extras**. Häufige Aktionen besitzen sichtbare Schaltflächen oder Tastenkürzel. Größe ändern ist sowohl über das Bild-Menü und einen direkten Button als auch über `Strg+R` erreichbar.

### Anzeige, Bearbeitung und Export unterscheiden

Zoom verändert die Darstellung. Skalieren verändert den Bildzustand. Speicheroptionen bestimmen die Ausgabe. Diese drei Vorgänge sollen für Anwender unterscheidbar bleiben, damit beispielsweise eine JPEG-Graustufenausgabe nicht überraschend das geöffnete Farbbild verändert.

### Entscheidungen vor dem Schreiben zeigen

Der Speicherdialog nennt Zielordner, Dateiname und Format. Die Stapelverarbeitung zeigt vor dem Start die Zuordnung der Dateien. Vorhandene Ziele sollen nicht durch versteckte Standardaktionen ersetzt werden.

### Grenzen offen benennen

Ein installierter Decoder ist noch keine Garantie für alle Varianten seines Formats. Bildblick dokumentiert begrenzte Metadatenübernahme, Rasterisierung und noch unbestätigte grafische Abläufe. Produkttexte sollen die tatsächliche Implementierung und ihren Prüfstand widerspiegeln.

## Zentrale Arbeitsabläufe

### 1. Ein Bild öffnen und prüfen

Ein Bild wird über den Öffnen-Dialog, ein einzelnes Drag-and-drop-Objekt, einen Startparameter oder den Desktop-Eintrag „Öffnen mit“ geladen. Die Bildfläche zeigt den Inhalt, die Statuszeile unter anderem Pixelmaße und Zoom.

Anwender können zwischen Einpassen, Originalgröße und freiem Zoom wechseln. Über die Bildinformationen sind gelesene EXIF-Werte und Dateiinformationen zugänglich.

**Erwartetes Ergebnis:** Die Datei ist sichtbar, und grundlegende Orientierung im Bild ist ohne Bearbeitung möglich.

### 2. Einen Ordner sichten

Der Benutzer öffnet einen Ordner und blättert mit den Pfeiltasten oder Navigationsbuttons. Die Vorschaubildleiste lässt sich einblenden und nach Dateinamen filtern. Natürlich sortierte Namen halten nummerierte Dateien in einer nachvollziehbaren Reihenfolge.

Vorschaubilder werden zunächst für 100 Dateien geladen; weitere können angefordert werden. Laufende Ordnerabfragen werden durch Generationszähler abgesichert, damit verspätete Ergebnisse keinen neueren Ordnerzustand ersetzen.

**Erwartetes Ergebnis:** Ein Ordner kann gesichtet werden, ohne jede Datei erneut über einen Dateidialog wählen zu müssen.

### 3. Zuschnitt und Ausgabegröße festlegen

Eine rechteckige Auswahl wird mit der Maus aufgezogen und ausdrücklich als Zuschnitt übernommen. Die Größenänderung bietet Pixel, Prozent, cm, Zoll, DPI, ein gekoppeltes Seitenverhältnis, Auflösungsvorlagen und Interpolation. Auswahlrahmen besitzen veränderbare Kanten, Maus-/Tastaturverschiebung und feste Verhältnisvorgaben.

Undo und Redo ermöglichen die Rückkehr zu vorherigen Bildzuständen. Die Historie ist auf höchstens 20 Schritte begrenzt und wird bei großen Bildern durch ein Speicherbudget reduziert.

**Erwartetes Ergebnis:** Die Bildabmessungen können kontrolliert geändert werden, bevor eine Ausgabedatei entsteht.

### 4. Eine Datei mit passenden Optionen speichern

Der Speicherdialog kombiniert Zielangaben mit Formatoptionen. JPEG bietet unter anderem Qualität, progressive Speicherung, Graustufen und ein optionales Dateigrößenlimit. GIF bietet Transparenz und Interlacing, PNG eine Kompressionsstufe und WebP einen verlustfreien Modus.

Metadaten lassen sich nach Typ auswählen. Das gewählte Format bestimmt, welche Optionen relevant sind. Benannte Profile speichern häufig verwendete Kombinationen dauerhaft.

**Erwartetes Ergebnis:** Eine überprüfbare Ausgabedatei entsteht am gewählten Ziel. Ein unerreichbares JPEG-Größenlimit liefert einen Fehler und ersetzt keine vorhandene Datei.

### 5. Eine Bildserie verarbeiten

Nach Auswahl von Quellen und Zielordner legt der Benutzer Format, Namensvorlage und optionale Transformationen fest. Die Vorschau prüft Kollisionen. Während der Verarbeitung werden Fortschritt und anschließend Fehler oder nicht bearbeitete Dateien angezeigt.

Der Kopiermodus erstellt bitgenaue Kopien mit neuen Namen. Die CLI verwendet denselben Planungs- und Verarbeitungskern und ergänzt ihn um JSON-Ausgabe und Exit-Codes.

**Erwartetes Ergebnis:** Wiederkehrende Konvertierungen können mit einer einheitlichen Konfiguration ausgeführt werden, ohne die Quelldateien umzubenennen oder zu überschreiben.

## Bildanpassungen und Export in Version 0.5.0

Der separate Bildanpassungsdialog enthält vier Looks und vierzehn Regler für Licht, Farbe und Effekte. Änderungen werden zunächst als Vorschau gezeigt. Eine ausdrückliche Übernahme erzeugt einen Bearbeitungsschritt in der Historie. Zurücksetzen verwirft nur offene Anpassungen. Vor dem Speichern oder weiteren Bildoperationen werden ausstehende Anpassungen in voller Auflösung übernommen. Der Bildwechsel berücksichtigt auch ungespeicherte Vorschauen.

Der Exportdialog stellt JPG, PNG und WebP direkt dar und ordnet weitere Formate, Spezialoptionen und Profile in aufklappbare Bereiche. Qualität, Zielauflösung und die gemeinsame Metadatenentfernung sind unmittelbar zugänglich. Die Dateigrößenanzeige entsteht durch echtes Kodieren im Hintergrund. Ein Export mit anderen Pixelmaßen erhält die Arbeitsdatei unverändert.

Die Gestaltung ist in [docs/DESIGN.md](docs/DESIGN.md) dokumentiert. Ein separates dunkles Erscheinungsbild gehört derzeit nicht zum Umfang.

## Umfang von Version 0.5.0

### Anzeige und Navigation

- Einzelbildansicht, Transparenzraster, Zoom und Vollbild.
- Ordnernavigation mit Vorschaubildern und Suche nach Dateinamen.
- Diashow mit einstellbarem Intervall.
- Navigation zwischen Seiten beziehungsweise Animationsframes.
- Wiedergabe von mehrbildigen Quellen innerhalb der verfügbaren Decodergrenzen.

### Bearbeitung

- Rotation um 90° und freie Winkel, horizontales und vertikales Spiegeln.
- Rechteckiger Zuschnitt, präzise Auswahlvorgaben, Zwischenablage und automatische Randentfernung.
- Größenänderung in Pixeln, Prozent, cm und Zoll mit DPI und vier Interpolationsverfahren.
- Graustufen, Negativ und automatischer Kontrast.
- Helligkeit, Kontrast, Gamma, RGB-Balance, Sättigung, Schärfe, Rote Augen, Filter, Rahmen und Leinwandränder.
- Text im Auswahlrechteck mit Schriftfamilie, Stil, Punktgröße und Farbe; separate Zeichenwerkzeuge.
- Bildwasserzeichen mit begrenzter Größe und derzeit fester Deckkraft von 50 %.

### Speichern und Ausgabe

- Einzelbildexport in die dokumentierten Ausgabeformate.
- Formatabhängige Einstellungen und persistente Exportprofile.
- Selektive Übernahme unterstützter Metadaten.
- Atomare Veröffentlichung vollständig geschriebener Dateien.
- Kombinierter Mehrseitenexport der bearbeiteten Seite mit übrigen Originalseiten.
- GTK-Druckanbindung; praktische Druckausgabe noch offen.

### Distribution und Bedienoberfläche

- Installation im Benutzerkonto mit Menüeintrag und eigenem Eisvogel-Symbol.
- Registrierung unterstützter Dateitypen für „Öffnen mit“.
- Start aus dem Projektverzeichnis und als installierte Anwendung.
- Archiv mit Installer, Dokumentation, Symbol und Prüfsummen.
- Deutsche Oberfläche; keine vollständig lokalisierte Mehrsprachenversion.

## Produktgrenzen

Der aktuelle Bildzustand wird intern als 8-Bit-RGBA verarbeitet. Ebenen, Vektoren und HDR-Daten bleiben nicht als solche editierbar. PDF- und SVG-Inhalte werden für die Anzeige gerastert.

Das Dokumentmodell bearbeitet eine aktuelle Seite. Beim Mehrseitenexport werden die übrigen Seiten erneut aus der Quelle geladen. Unabhängige Bearbeitungsstände für viele Seiten gleichzeitig sind nicht vorgesehen.

Metadatenübernahme ist selektiv und formatabhängig. IPTC, Vorschaubilder und Spezialmetadaten werden nicht vollständig erhalten. Eine professionelle Farbmanagement- oder Drucktreue ist bislang nicht validiert.

HEIC/HEIF, komplexe AVIF-Alpha-Varianten und einzelne Spezialformate können nicht verarbeitet werden. Für Kamera-RAW, DICOM, XCF und WPG fehlen repräsentative Tests über die relevanten Varianten hinweg.

Bildschirmaufnahme, frei belegbare Tastenkürzel, Kontaktbögen, OCR und vollständige Metadatenbearbeitung sind noch nicht implementiert. Scanner und Medien benötigen optionale Systemmodule; ihre Hardware-/Codec-Abnahme steht aus.

## Architektur und Zustandsmodell

Die GTK-Oberfläche koordiniert Aktionen und zeigt Ergebnisse. Das Bildmodell enthält den aktuellen Zustand, die Historie und den Speicherstatus. Export, Größenberechnung und Stapelplanung sind soweit praktikabel von der grafischen Darstellung getrennt und direkt testbar.

Laden, Bearbeiten und Speichern laufen über Hintergrundaufträge. Ergebnisse werden über die GLib-Hauptschleife an die Oberfläche zurückgegeben. Während eines Bildauftrags werden widersprechende Bildänderungen gesperrt.

Native Zusatzdecoder werden nur für zugelassene Formate aufgerufen. Die Ausführung unterliegt Zeit-, Speicher- und Ausgabebegrenzungen. Die ImageMagick-Konfiguration unterbindet Netzwerk- und Delegatenzugriffe für diese Aufrufe.

Benutzerdaten umfassen ausdrücklich gespeicherte Bilder, Exportprofile, Ansichtsoptionen und die letzten zehn Bildordner. Das Installationspaket enthält keine persönlichen Bildsammlungen oder Profilkonfigurationen.

## Gestaltung und Sprache

Die Oberfläche nutzt native GTK-Bedienelemente in einem hellen, monochromen Erscheinungsbild: weiche Grautöne, abgerundete Karten, dünne Regler und schwarze Hauptaktionen. Das Hauptfenster startet mit 720 × 640 Pixeln. Menüleiste, kompakte Symbolleiste, bildfüllender Arbeitsbereich und schmale Statuszeile bilden die feste Struktur. Zoom und Navigation stehen in der Symbolleiste. Bildanpassungen, Export, Größenänderung und Vorschaubilder haben eigene Dialoge beziehungsweise Fenster. Funktionsbezeichnungen beschreiben die Aktion: „Größe ändern“, „Speichern unter“ oder „Alle Seiten exportieren“. Technische Begriffe werden dort verwendet, wo sie eine Exportentscheidung unterstützen, etwa bei Interpolation oder Farbunterabtastung.

Der Eisvogel in Nachtblau und Orange ist das zentrale Erkennungszeichen. Das Motiv soll Aufmerksamkeit und genaues Hinsehen vermitteln. Das Symbol wird als transparentes Rasterasset geliefert und für das Desktop-Thema in eine eigenständig skalierbare SVG-Datei eingebettet.

Tastaturbedienung ist Teil des Bedienkonzepts. Ein systematischer Accessibility-Test mit Screenreader, hoher Skalierung und alternativen Kontrastthemen steht noch aus.

## Qualität und Abnahme

Der aktuelle automatische Prüfstand umfasst 110 erfolgreiche Tests auf dem Referenzsystem. Sie prüfen unter anderem echte Kodierergebnisse, Pixelzustände, Undo/Redo, Namenskollisionen, Profilpersistenz und native Decoder.

Der grafische Integrationstest läuft erfolgreich in einer Fedora-44-Sitzung mit Xvfb und Openbox in GitHub Actions. Er deckt Navigation, Bildoperationen, Menüs, Strg+R, Speicherdialog, Vorschau, Übernahme und verkleinerten Export ab. Screenshots prüfen die Anordnung und ein kompaktes Fenster. Lokal bleibt der Display-Zugriff eingeschränkt; Status 77 bedeutet dort „nicht ausgeführt“.

Für eine belastbare Desktop-Freigabe sind folgende manuelle Prüfungen noch erforderlich:

| Prüfung | Abnahmekriterium |
| --- | --- |
| Start aus dem Anwendungsmenü | Sichtbares Fenster, korrektes Symbol, verständliche Fehlermeldungen |
| Öffnen mit und Dateinamen | Leerzeichen und Unicode funktionieren; richtige Datei wird angezeigt |
| Größenänderung | Dialog über Menü und `Strg+R`; Pixel-/Prozentwerte und Seitenverhältnis nachvollziehbar |
| Speichern | Formatwechsel, Zielwahl, Überschreibabfrage und Fehlerfälle im echten Desktop bestätigt |
| Darstellung | Lesbare Dialoge bei kleinen Displays und hoher Skalierung |
| Druck | Vorschau und mindestens eine tatsächliche Ausgabe bestätigt |
| Zugänglichkeit | Fokusführung und grundlegende Screenreader-Bedienung geprüft |

## Nächste Entwicklungsschritte

### Priorität 1: Desktop-Abläufe absichern

Manuelle Prüfungen auf einer normalen Desktop-Sitzung durchführen, gefundene Layout- und Fokusprobleme beheben und reproduzierbare GUI-Prüfungen etablieren. Fehlerbehandlung und Verständlichkeit der Dialoge haben Vorrang vor einer größeren Formatliste.

### Priorität 2: Häufige Alltagsaufgaben ergänzen

Zwischenablage, präzise Auswahl, Zeichnen, Rahmen, DPI und dauerhafte Ansichtsoptionen sind umgesetzt. Nächste Kandidaten sind genauer einstellbare Wasserzeichen, mehr Druckseitenoptionen und Bildlisten für Diashows. Eine Erweiterung erfolgt anhand konkreter Arbeitsabläufe und mit passenden Tests.

### Priorität 3: Format- und Metadatenqualität verbessern

Repräsentative Testdateien für vorhandene Zusatzdecoder sammeln, AVIF-Varianten genauer behandeln und gezielte Metadatenfunktionen ergänzen. Verlustfreie JPEG-Operationen sind ein möglicher eigener Arbeitsbereich.

### Priorität 4: Verteilung vereinfachen

Zusätzliche Linux-Distributionen validieren und paketierte Laufzeiten oder distributionsspezifische Pakete evaluieren. Ein universelles Installationsformat ist derzeit noch kein zugesagter Bestandteil.

Die Reihenfolge ist eine Planung, keine verbindliche Terminangabe.

## Erfolgskriterien

Das Produkt ist für seine Kernaufgaben erfolgreich, wenn Anwender ohne Kontoeinrichtung ein Bild öffnen, den Ausschnitt oder die Größe ändern und eine passende Datei exportieren können. Wiederkehrende Exporte sollen mit Profilen oder CLI-Befehlen reproduzierbar sein.

Messbare Qualitätsziele sind nachvollziehbare Fehlerberichte, keine unbestätigten Überschreibvorgänge, bestandene Dateiexport-Prüfungen und dokumentierte manuelle Desktop-Abnahmen. Nutzungsmetriken werden nicht durch einen eingebauten Telemetrie-Dienst erhoben.

## Lizenz

Bildblick wird unter der [MIT-Lizenz](LICENSE) bereitgestellt. Installation und Bedienung sind in [README.md](README.md) beschrieben.

## Neue Arbeitsabläufe in 0.5.0

- Auswahl in die Zwischenablage kopieren, in einem neuen Fenster einfügen und unabhängig speichern.
- Frei drehen, Rote Augen korrigieren, Gamma und RGB-Kanäle einstellen; zehn Effekte und reduzierte Farbpaletten anwenden.
- Schriftfamilie, Stil und Punktgröße wählen; im Auswahlrechteck umbrechen. Stift und Formen in einem eigenen Zeichendialog nutzen.
- Leinwandseiten getrennt vergrößern oder kürzen, mehrteilige Rahmen ergänzen und Bilder horizontal/vertikal zusammensetzen.
- Gespeicherte Dateien umbenennen, kopieren, verschieben, extern öffnen oder nach Bestätigung in den Papierkorb legen.
- Druckgröße und Position festlegen; optional mit SANE scannen oder lokale Medien über GTK/GStreamer wiedergeben.

Alle Ergänzungen bleiben in separaten Dialogen. Das Hauptfenster behält 720 × 640 Pixel als Startgröße. **Strg+Y** schneidet jetzt zu; **Strg+Umschalt+Z** wiederholt. **Strg+S** und **S** öffnen den Speicherdialog; die Menüaktion „Speichern“ speichert die aktuelle Datei mit Ersetzungsabfrage.

Die aktuelle, funktionsweise Menüübersicht steht in [docs/FEATURES.md](docs/FEATURES.md). Hardwareabhängige Integrationen sind implementiert, aber noch keine Zusage für jeden Scanner, Drucker oder Mediencodec. Eine vollständige Umsetzung sämtlicher denkbarer Spezialformate und Zusatzmodule wird nicht behauptet.

## Effekte mit direkter Vorschau

Der separate Effekte-Dialog bietet zehn direkt anklickbare Effekte, eine große Bildvorschau und einen Originalvergleich. Jeder Effekt besitzt einen Intensitätsregler von 0 bis 100 Prozent. Zusätzliche Regler werden passend zum ausgewählten Effekt angezeigt; Einstellungen bleiben beim Wechsel erhalten. Zurücksetzen betrifft den ausgewählten Effekt. Abbrechen ändert weder Bild noch Historie; Anwenden verarbeitet die Originalauflösung und erzeugt einen rückgängig machbaren Bearbeitungsschritt. Die Vorschau nutzt höchstens 1200 × 1200 Pixel und kennzeichnet ihre verkleinerte Darstellung.

## Einheitliche Werkzeugdialoge in 0.6.0

Die Bearbeitungswerkzeuge teilen ein gemeinsames Bedienkonzept: Bildvorschau links, Einstellungen rechts, Originalvergleich, Zurücksetzen und ausdrückliches Anwenden oder Abbrechen. Das gilt für Helligkeit/Kontrast/Farbe, Schärfen/Weichzeichnen, freie Drehung, Rahmen, Rote Augen, Palette, Farbkanaltausch, automatischen Zuschnitt, Leinwand und Text. Neue Werkzeugvorschauen verarbeiten die Originalpixel in einem Hintergrundauftrag, bevor das Ergebnis für die Anzeige verkleinert wird. Ein Auftrag läuft pro Dialog; veraltete oder nach dem Schließen eintreffende Ergebnisse werden verworfen.

Visuelle Parameter erhalten Slider. Exakte Maße, Positionen, DPI und Dateinamen behalten passende Eingabefelder. Rahmenstile, Kanalanordnungen, Zeichenwerkzeuge, Einheiten, Interpolation, Größenvorgaben, Auswahlverhältnisse, Druckmodi und Exportformate sind direkt anklickbar. Bei Rahmen- und Strichbreiten steht zusätzlich eine genaue Zahleneingabe bereit. Fehler in einer Vorschau ändern die Arbeitsdatei nicht; nach Korrektur der Eingabe kann weitergearbeitet werden.


## Bildübersicht und Zeichenwerkzeuge in 0.7.0

Das Hauptfenster wächst beim manuellen Vergrößern mit dem Bild. Sobald die verfügbare Bildschirmfläche erreicht ist, wird es maximiert; weiteres Zoomen bleibt möglich und verschiebt den sichtbaren Ausschnitt über Scrollleisten. Die Startgröße bleibt 720 × 640 Pixel. Verkleinern reduziert die Fenstergröße nicht automatisch.

Die Taste **I** öffnet eine vollständige Datei- und Bildübersicht mit ursprünglichen und aktuellen Abmessungen/Farbtiefen, getrennten X-/Y-DPI, physischen Druckmaßen, abschaltbarer RGB-Farbzählung im Hintergrund, Dateigröße, aktuellem Pixel-Speicher, Ordnerposition, Datum und Ladezeit. EXIF, IPTC und Kommentare erscheinen in eigenen Leseansichten. DPI lassen sich ohne Neuberechnung der Pixel ändern und rückgängig machen. Unbekannte Quelldaten werden ausdrücklich gekennzeichnet.

Der Zeichendialog stellt Stift, weichen Pinsel, Linie, Pfeil, Rechteck und Ellipse als sechs direkt auswählbare, beschriftete Symbole dar. Breite, Farbe und Rücknahme bleiben direkt erreichbar. Der Pinsel trägt weich auslaufende Striche auf; Anwenden übernimmt die gesamte Zeichnung als einen Undo-Schritt.


## Tastatur und Designreferenz in 0.8.0

Die zentrale Tastaturbelegung steuert Dateiwechsel, kontextabhängiges Scrollen, 1–9-Dateisprünge, Markierungen, Fensterleisten und sechs Vollbildmodi. F1 öffnet eine durchsuchbare Hilfe aus derselben Liste. Einfache Tasten werden nicht als Bearbeitungsbefehle ausgewertet, während Textfelder oder Werkzeugdialoge bedient werden. Enter schaltet Vollbild, Strg+Y schneidet zu, F5 aktualisiert die Ansicht und F9 steuert die Diashow. Strg+R bleibt Größenänderung. Strg+S öffnet den Speicherdialog.

Die lokale Designreferenz enthält alle benutzerseitigen Elementfamilien und verbindliche Muster. Ihre index.html bettet CSS, JavaScript und Symbole ein; zum Betrachten ist kein Server erforderlich. Neue Designmuster werden zuerst dort beschrieben und anschließend in der GTK-App umgesetzt.

## Einheitliche Dialoggrößen in 0.9.0

Dialoge erhalten eine aus der Bedienelementzahl abgeleitete Breite und eine Höhe nach ihrem natürlichen Inhalt. Die Bildschirmfläche begrenzt beide Maße. Vertikales Scrollen kommt nur zum Einsatz, wenn der Inhalt nicht in den verfügbaren Bildschirm passt. Formel: `docs/DIALOG-SIZING.md`; Tokens: `design-system/tokens.json`.

Bearbeitungsdialoge ordnen Vorschau und Optionen untereinander an. Bildinformationen, Metadaten, Zeichnen, Größenänderung, Export, Tastaturhilfe, Meldungen, Vorschaubilder, Histogramm und Medienmodul verwenden denselben Rahmen. Die sechs Menüs gruppieren ihre 88 Aktionen und zeigen verfügbare Kürzel rechts. Systemoberflächen für Datei-, Farb-, Schrift- und Druckerauswahl behalten ihre Linux-Gestaltung.

Der [UI-Abgleich](docs/UI-AUDIT.md) dokumentiert alle betroffenen Module und die Prüfverfahren.

Kurze Meldungen und Sicherheitsabfragen sind ab 0.9.2 inhaltshoch. Ungespeicherte Änderungen bieten Speichern, Verwerfen und Abbrechen; eine nachfolgende Aktion wartet auf erfolgreiches Speichern in voller Auflösung.


## Klarere Bedienung in 0.10.0

Auswahlzustände unterscheiden sich von Abschlussaktionen. Gemeinsame GTK-Rollenfarben, Schriftgrößen und Radien stammen aus der Designreferenz. Dateiname und Zielordner stehen im Export offen vor den Formateinstellungen. Bildinformationen gliedern sich in Datei, Abmessungen/Druck, Farben sowie Speicher/Anzeige. Regler bilden klar getrennte Gruppen; leere Suchergebnisse bieten einen Weg zurück. Der weitere Plan ist in `redesign.md` dokumentiert.
