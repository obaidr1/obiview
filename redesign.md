# Redesign von Bildblick

Stand: 16. Oktober 2026. Ausgangspunkt: Version 0.9.2. Grundlage: [knowlede.md](knowlede.md), das gelesene Buch und der tatsächliche GTK-/HTML-Bestand. Dies ist ein Arbeitsplan mit überprüfbaren Ergebnissen, keine Behauptung einer bereits vollständig erneuerten App.

## Rahmen und Vorgehen

Der vorhandene helle Stil, die kompakte Desktopstruktur, alle Funktionen und Tastenkürzel bleiben erhalten. Werkzeugdialoge: maximal 520 × 760 logische Pixel, begrenzt durch den Bildschirm. Meldungen und die Speicherabfrage: inhaltshoch, drei getrennte Speicherentscheidungen. Kein automatisches Beschneiden oder Verfärben von Nutzerbildern für die Gestaltung.

Geprüft wurden die sechs Menümodelle, die gemeinsamen Komponenten und alle eigenen Dialog-/Modulfamilien anhand ihres Quellcodes. Ergänzend wurden vorhandene native Prüfbilder von Export, Bildinformationen und Bildanpassungen mit der HTML-Referenz verglichen. Das ersetzt keine Geräteprüfung von Scanner, Drucker oder Desktop-Portalen. Nach Änderungen folgen neue native Tests und Screenshots.

## Bestandsaufnahme

| Bereich | Befund im Bestand | Vorgeschlagene Änderung / Entscheidung |
| --- | --- | --- |
| Hauptfenster, Menüleiste, Symbolleiste, Status | Die gewünschte kompakte Struktur und die Startgröße sind vorhanden. Sechs Menüs sind gruppiert; Kürzel stehen rechts. | Struktur beibehalten. Kein zusätzliches Navigationssystem. Den vorhandenen Leerzustand sachlicher formulieren und Zwischenablage nennen. |
| Gemeinsames Theme | HTML-Tokens und GTK-CSS enthalten teilweise dieselben Werte als unabhängige Literale. | Gemeinsame Rollenfarben, Schriftgrößen und Radien in GTK aus `tokens.json` einsetzen. Eingabegrenzen von bloßen Trennlinien unterscheiden. |
| Auswahl, Effekte, Looks, Zeichenwerkzeuge | Aktive Togglebuttons sind ebenso dunkel wie die Hauptaktion; mehrere schwarze Flächen konkurrieren. | Helle ausgewählte Fläche, erkennbare Kontur und zusätzlicher Auswahlmarker. Eine dunkle abschließende Aktion behalten. Werkzeug-Symbole und sichtbare Namen erhalten. |
| Generische Werkzeuge | `ToolDialog` gruppiert alle Felder in einer Karte; Abstand zwischen Feldern ist ähnlich dem Abstand innerhalb eines Feldes. Längere Erläuterungen stehen vor der Vorschau. | Feldgruppen deutlicher trennen, Label und Feld enger zusammenhalten. Gemeinsame Zahlen-/Auswahlkomponenten korrigieren. Ausführliche kontextspezifische Hilfe später gezielt überarbeiten. |
| Bildanpassungen | Viele Regler stehen eng hintereinander; Werte sind klein und zurückgenommen. | Jeder Name mit seinem Wert und Slider als eigene Gruppe. Werte gut lesbar und ausgerichtet; Sektionen Licht/Farbe/Effekte erhalten. |
| Export / Speichern unter | Dateiname und Zielordner sind unter einem eingeklappten Speicherort verborgen, während weniger wichtige Optionen vorher erscheinen. | Speicherziel direkt nach der Dateizusammenfassung immer offen zeigen. Format, Qualität, Ausgabegröße folgen. Erweiterte Optionen und Profile bleiben aufklappbar. Langer Pfad bleibt erreichbar. |
| Größe ändern | Eine lange Karte mit gleichartigen Abständen erschwert die Zuordnung. Ein werblicher Satz erklärt die Aufgabe nicht präzise. | Gliedern in Abmessungen, Berechnung und Größenvorgaben; Beschriftung direkt am Feld. Neue Pixelgröße klar hervorheben; Fehler erkennbar markieren. |
| Bildinformationen | Alle Daten stehen gleichgewichtig in einer langen Liste. Horizontale/vertikale DPI sind nur über Accessibility/Tooltip unterschieden. | Datei, Abmessungen/Druck, Farben, Speicher/Anzeige getrennt gruppieren; X/Y sichtbar benennen. Alle bisherigen Werte und EXIF/IPTC/Kommentar behalten. |
| Vorschauen: Effekte, Anpassungen, generische Werkzeuge | `Gtk.Picture` hat keine gemeinsame Vorschaufläche. Sehr helle oder transparente Bilder können optisch verschwinden. | Neutralen gemeinsamen Vorschaugrund verwenden, vollständiges Bild einpassen. Fehlermeldungen klar von normalen Vorschauhinweisen unterscheiden. |
| Zeichnen | Werkzeuge haben bereits eigene Symbole und Namen. Rückgängig sieht auch ohne Strich bedienbar aus. | Auswahlgestaltung angleichen; Rückgängig erst nach einem Strich freigeben. Keine Änderung der Zeichenfunktionen. |
| Vorschaubilder / Dateisuche | Bei null Treffern bleibt eine leere Liste. Dekodierfehler werden ohne sichtbaren Hinweis übersprungen. | Eigenen Leerzustand mit „Ordner öffnen“ und „Filter zurücksetzen“ anbieten; fehlgeschlagene Vorschau beschriften. |
| Informationen, Metadaten, Tastaturhilfe | Lesefenster und Suchfunktion vorhanden; Metadaten bleiben vollständig zugänglich. | Gemeinsame Typografie/Feldgestaltung übernehmen. Suche ohne Treffer in einem späteren Durchgang um Rückmeldung ergänzen. |
| Rotation, Rahmen, Leinwand, Auswahl, Text, Palette, Kanaltausch, Filter, Wasserzeichen | Verwenden den gemeinsamen `ToolDialog`; direkte Auswahl und Slider existieren. | Erste Verbesserungen automatisch über den gemeinsamen Rahmen und die Komponenten. Danach einzelne Reihenfolgen und Hilfehinweise gezielt prüfen. |
| Neues Bild, Umbenennen, externe Programme, letzte Ordner, Scanner | Gemeinsames Formular; dynamische Systemlisten können lang werden. | Gemeinsame Verbesserungen übernehmen. Suchbare Auswahl für lange Systemlisten als nächste Iteration planen; keine Effektauswahl in Dropdowns verwandeln. |
| Drucken, Panorama, Stapeloptionen | Funktionale Formulare, aber viele gleichzeitig sichtbare Bedingungen und lange Hilfetexte. | Gemeinsame Feldgruppen jetzt verbessern. Bedingte Optionen und aufgabenspezifische Beschriftungen später separat bearbeiten, mit Funktionstests. |
| Stapelfortschritt | Zähler und Dateiname sind vorhanden; keine Fortschrittsleiste. | Im nächsten Durchgang eine echte, aus erledigten Dateien berechnete Leiste ergänzen. Keine Zeitprognose erfinden. |
| Histogramm | RGB-Kurven unterscheiden sich überwiegend durch Farbe. | Im nächsten Durchgang benannte Kanalwahl/Legende, damit die Zuordnung nicht allein von Farbe abhängt. |
| Medien, native Datei-/Farb-/Schrift-/Druckdialoge | Teilweise vom System bzw. von Codecs bereitgestellt. | Eigenen Rahmen konsistent halten; Systemoberflächen respektieren. Hardware-/Desktopprüfung bleibt ausdrücklich getrennt. |
| Fehler, Bestätigungen, ungespeicherte Änderungen | Kompakter Rahmen und sicherer Ablauf sind seit 0.9.2 geprüft. | Erhalten. Keine erneute Mindesthöhe von 760 px. |

## Erste Umsetzung: klar abgegrenzter Durchgang

Statuslegende: offen → umgesetzt → geprüft. Ein Häkchen bedeutet implementiert und im beschriebenen Umfang geprüft.

- [ ] **R01 – Gemeinsame Gestaltung:** GTK nutzt zentrale Rollen-Tokens. Auswahlzustände sind hell und zusätzlich markiert; Texte/Fokus bleiben erkennbar. Keine reine Farbcodierung der Auswahl.
- [ ] **R02 – Feldgruppen und Regler:** `ToolDialog`, Anpassungen und Resize nutzen eindeutige Abstände. Zahlen sind rechtsbündig. Fehler bei Größenangaben erhalten eine erkennbare Meldung.
- [ ] **R03 – Speicherziel:** Dateiname und Ordner sind im Export ohne Aufklappen sichtbar. Bestehende Formate, Profile, Größenberechnung und sichere Speicherfortsetzung funktionieren weiter.
- [ ] **R04 – Bildinformationen:** Alle vorhandenen Werte bleiben vorhanden und sind sinnvoll gruppiert. Beide DPI-Achsen sind sichtbar beschriftet.
- [ ] **R05 – Vorschau:** Gemeinsamer neutraler Untergrund; vollständiges Bild bleibt sichtbar. Fehlerzustand wird auch sprachlich bezeichnet.
- [ ] **R06 – Leere Listen und Werkzeuge:** Such-/Ordner-Leerzustand hat passende Aktionen; fehlende Vorschaubilder haben einen Hinweis. Zeichnen-Rückgängig ist ohne Strich deaktiviert.
- [ ] **R07 – Referenz und Nachweis:** HTML/CSS/TypeScript-Muster zuerst anpassen; anschließend Browser, Kernfunktionen, native Dialoggeometrie und relevante Bedienabläufe prüfen. Ergebnis und Grenzen unten festhalten.

## Nächster Durchgang, bewusst noch nicht umgesetzt

Diese Punkte sind das Ergebnis der vollständigen Bestandsaufnahme; der Nutzer hat zunächst den Beginn der Umsetzung verlangt. Sie werden nicht als erledigt ausgegeben:

1. **R08:** Histogramm mit benannten Kanälen und auslesbaren Spitzenwerten; Farbunterscheidung ergänzen.
2. **R09:** Stapelfortschritt mit realer Fortschrittsleiste und dauerhaft zugänglichen Dateiergebnissen.
3. **R10:** Tastaturhilfe ohne Treffer, durchsuchbare dynamische Systemlisten und kontextbezogene Detailhilfe in langen Werkzeugformularen.
4. **R11:** Druck-/Rahmenoptionen abhängig von ihrer Auswahl stärker bündeln; Kernfelder sichtbar lassen und Ein-/Ausblenden mit Tastatur testen.

## Abnahme

- Referenz offline: keine externen Fonts/Skripte, keine waagerechten Überläufe; aktive Auswahl, Exportziel, Modalfooter, Fokus und kompakte Bestätigung prüfen.
- Native App: 520-px-Maximalbreite, reguläre Höhe und kleine Bildschirmbegrenzung, erreichbare Aktionen, lange Dateinamen/Pfade und alle bisherigen Menüaktionen prüfen.
- Arbeitsabläufe: Abbrechen verändert das Bild nicht; Übernehmen und Rückgängig bleiben intakt. Exportabbruch und Schreibfehler dürfen keine ausstehende Schließ-/Wechselaktion auslösen.
- Neue Designzustände: ausgewählte Optionen besitzen einen Marker; Formlabels und Werte gehören optisch zusammen; Informationsgruppen verlieren keine Daten; leere Suche hat eine nutzbare Rückkehr.
- Screenshots mit synthetischen Testbildern; Buchseiten und Nutzerdaten werden nicht in das Repository übernommen.

## Umsetzungsergebnis

Wird nach der tatsächlichen Implementierung und Prüfung ergänzt.
