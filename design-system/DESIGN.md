# Bildblick · verbindlicher Designvertrag

Version 1.1 · 16. Oktober 2026

Diese Referenz gilt ab jetzt für neue und überarbeitete Benutzeroberflächen in Bildblick. Sie beschreibt die native GTK-App. Die HTML-Website ist ein lokal ausführbarer Komponenten- und Musterkatalog, keine zusätzliche Bildbearbeitung.

## Verbindliche Quellen

1. `tokens.json` definiert gemeinsame Farben, Abstände, Typografie und Radien. `tokens.css` wird daraus erzeugt.
2. `src/catalog.html` und `styles.css` definieren Komponenten, Zustände und zusammengesetzte Muster. Der Build erzeugt daraus die eigenständige `index.html`.
3. `src/app.ts` beschreibt die interaktiven Beispiele. `app.js` ist die erzeugte Offline-Ausgabe.
4. Dieser Vertrag beschreibt Verhalten, Einsatz und Grenzen.

Bei widersprüchlichen Beispielen zuerst den Widerspruch in der Referenz auflösen. Neue Varianten nicht stillschweigend nur in einem App-Dialog einführen. Explizite neue Produktentscheidungen des Nutzers können die Referenz ändern; anschließend Quellen und Beispiele gemeinsam aktualisieren.

## Grundaufbau

- Das Hauptfenster startet bei 720 × 640 logischen Pixeln. Menüleiste, kompakte Symbolleiste, Bildfläche und Statuszeile bilden seine Struktur.
- Beim manuellen Vergrößern wächst es bis zur verfügbaren Bildschirmfläche. Weitere Vergrößerung verwendet Scrollleisten. Verkleinern schrumpft das Fenster nicht automatisch.
- Werkzeuge öffnen eigene Dialoge. Keine permanente umfangreiche Bearbeitungsseitenleiste im Hauptfenster.
- Alle eigenen Dialoge und Nebenfenster verwenden 520 × 760 logische Pixel, einschließlich Export, Bearbeitung, Informationen und Hilfen. 520 px ist die gemeinsame Maximalbreite aus dem Exportmuster. Auf kleineren Bildschirmen werden beide Maße auf die verfügbare Fläche abzüglich 32 px begrenzt. Die Hauptansicht bleibt davon ausgenommen. Kurze Meldungen und Sicherheitsabfragen sind eine ausdrückliche Ausnahme: gleiche Maximalbreite, aber nur so hoch wie ihr Inhalt.
- Vorschauen stehen über Optionen und Reglern. Lange Inhalte scrollen vertikal; die Aktionsleiste bleibt außerhalb des Scrollbereichs sichtbar. Keine horizontale Verbreiterung durch Pfade, Listen oder Auswahlgruppen.
- Große Beispielüberschriften und die Navigationsseitenleiste dieser Dokumentationswebsite sind keine neuen Bestandteile der App.

## Farben und Form

| Zweck | Wert |
| --- | --- |
| Text / primäre Aktion | `#242424` |
| Sekundärtext | `#626262` |
| Fensterfläche | `#f5f5f3` |
| Karte | `#fafaf9` |
| Linien / Sliderbahn | `#dededb` |
| Eingabe / Slidergriff | `#ffffff` |
| Hover | `#e7e7e4` |
| Gedrückt | `#d9d9d5` |
| Fehler | `#a02020` |
| Modaler Hintergrund | Schwarz mit 35 % Deckkraft |

Farbe dient Inhalt und Bedeutung. Keine dekorativen bunten Akzentbuttons. Rot ist für Fehler und destruktive Aktionen reserviert; Bildinhalte und gewählte Zeichenfarben sind davon unabhängig. Status zusätzlich mit Text oder Symbol kennzeichnen.

Abstände: 4, 8, 12, 16, 20, 24, 32 px. Eingaben und Auswahlbuttons: 12 px Radius. Karten: 20 px. Dialoge: 24 px. Aktionsbuttons: Pillenform. Sichtbare Dialogränder betragen 20–24 px, Kartenpadding üblicherweise 16 px. Die Website bietet zusätzlich großzügigere Dokumentationskarten.

Schrift: Inter, Cantarell, System Sans. Dialogtitel 22 px / 600, Abschnittstitel 14 px / 600, Fließtext 14 px / 400, Hilfs- und Statustext 12 px / 400. Keine extern benötigten Webfonts.

## Komponentenregeln

| Element | Wann verwenden | Regeln |
| --- | --- | --- |
| Primärer Button | Abschließende Hauptaktion | Ein schwarzer Hauptbutton pro Dialog; rechts unten; präzises Verb wie „Anwenden“ oder „Bild speichern“ |
| Sekundärer / Textbutton | Abbrechen, Zurücksetzen, ergänzende Aktion | Leicht, ohne konkurrierende schwarze Fläche; Abbrechen links neben der Hauptaktion |
| Symbolbutton | Kompakte Toolbar | Vektor, zugänglicher Name, Tooltip einschließlich Kürzel; normal 40–44 px Ziel, in der App-Toolbar kompakt 30 px |
| Werkzeugauswahl | Stift, Pinsel, Linie, Pfeil, Rechteck, Ellipse | Eigene Symbole plus sichtbarer Text, aktive Auswahl hell mit sichtbarem Auswahlzeichen |
| Direkte Auswahl | Effekte, Varianten, Einheiten, Interpolation, Formate | Alle Optionen als Buttons oder Karten sichtbar; helle aktive Fläche mit Auswahlzeichen; kein Effekt-Dropdown |
| Formatkarte | Exportformat und Auflösung | Beschriftung plus Erklärung, dezente helle ausgewählte Karte und eindeutiger Auswahlpunkt |
| Slider | Stärke, Qualität, Kontrast, Winkel, Radius | Beschriftung, Einheit/Grenzen wo nötig, sichtbarer aktueller Wert; genaue Eingabe bei Bedarf gekoppelt |
| Zahlenfeld | Pixelmaße, Position, DPI | Plus/Minus, Eingabegrenzen, Einheit; keine unnötigen Slider für exakte Maße |
| Textfeld | Dateiname, Profil, Text | Sichtbare Beschriftung; Hilfstext statt ausschließlich Platzhalter; Fehler am Feld |
| Switch | Einstellung aktivieren/deaktivieren | Beschriftung links, Switch rechts; aktuelle Wirkung verständlich |
| Checkbox | Unabhängige Optionen | Mehrfachauswahl möglich; teilweise Auswahl bei Gruppen darstellen |
| Radiobutton | Einfache exklusive Wahl | Klare Gruppenbezeichnung; visuelle Varianten bevorzugt als direkte Auswahlbuttons |
| Auswahlliste / Suche | Unbegrenzte Systemdaten | Ausnahme für Profile, Schriftfamilien, Geräte, Ordner; keine versteckten Bearbeitungsvarianten |
| Details / Expander | Selten benötigte Zusatzoptionen | Aussagekräftiger Titel; wesentliche Standardfunktionen bleiben sichtbar |
| Information | Bilddaten, Metadaten, Ergebnislisten | Werte auswählbar, lange Pfade umbrechen; fehlende Daten ausdrücklich kennzeichnen |
| Menü / Popover | App-Aktionen | Text, sinnvolle Gruppierung, Kürzel rechts, deaktivierte Einträge erkennbar |
| Lade-/Leer-/Fehlerzustand | Asynchrone oder fehlende Inhalte | Verständliche Rückmeldung und nächster sinnvoller Schritt; keine erfundenen Ergebnisse |

Standardbuttons orientieren sich an 44 px sichtbarer Gesamthöhe. GTK-Mindesthöhen enthalten Padding und Rahmen je nach Widget unterschiedlich: visuelles Ergebnis gegen die Referenz prüfen, nicht nur CSS-Zahlen blind übertragen.

## Interaktion

- Live-Vorschau verändert das Arbeitsbild noch nicht. Originalvergleich, Zurücksetzen und Abbrechen funktionieren ohne unbeabsichtigte Übernahme.
- Anwenden erzeugt genau einen Undo-Schritt; Abbrechen verwirft nicht angewendete Änderungen.
- Slider und genaue Eingabe verwenden denselben begrenzten Wert. Ungültige Größen blockieren die Hauptaktion und nennen den Fehler.
- Dialoge dimmen das Elternfenster. Fokus bleibt im Dialog; Schließen stellt den Fokus am Auslöser wieder her. Escape entspricht Abbrechen, soweit dadurch keine bestätigungspflichtigen Änderungen verloren gehen.
- Ein 2-px-Fokusring mit 3 px Abstand muss sichtbar bleiben. Tastaturbedienung, zugängliche Namen und native Semantik sind Pflicht.
- Auswahlgruppen erlauben Pfeiltasten; Slider unterstützen Pfeiltasten sowie Home/End. Reduzierte Bewegung respektieren.
- Icon-only-Buttons benötigen Namen und Tooltips. Wesentliche Funktionen nicht ausschließlich per Hover erklären.
- Browserbeispiele kennzeichnen simulierte Ergebnisse. Berechnete Dateigrößen, Ladezeiten und Metadaten in der App dürfen nicht aus fiktiven Werten bestehen.

## Native Systemgrenze

Datei-, Farb-, Schrift-, Druck- und Portaloberflächen dürfen ihrer Linux-Umgebung folgen. Unsere Buttons, Beschriftungen und eigenen Dialoginhalte müssen zur Referenz passen. Der Web-Katalog demonstriert diese Auslöser, ersetzt aber nicht den jeweiligen Systemdialog. Scanner und Medienwiedergabe hängen von tatsächlichen Geräten und Codecs ab.

## Umsetzung in GTK

- `ui_theme.py`: gemeinsame GTK-Farben, Typografie, Radien, `card`, `label`, `icon_button`.
- `edit_controls.py`: `ChoiceButtons` und `SliderField` wiederverwenden.
- `tool_dialogs.py`: `ToolDialog` für Vorschau, Originalvergleich und Übernahme.
- `paint_dialog.py`: sechs Symbolwerkzeuge, Breite, Farbe, Strich zurück.
- `save_dialog.py`, `resize_dialog.py`, `info_dialog.py`: spezialisierte vollständige Muster.
- Die Tabelle „Inventar & Umsetzung“ in der Website ordnet alle benutzerseitigen Elementfamilien des aktuellen Quellenbestands zu. `Box`, `Grid`, `Stack` und `ScrolledWindow` erscheinen als Layoutmuster, nicht als sinnlose isolierte Container.

`dialog_layout.py` setzt die gemeinsamen Maße aus `tokens.json` für alle eigenen Dialoge und Nebenfenster um. Fachdialoge verwenden diesen Rahmen; neue Dialoge müssen ebenfalls `StandardDialog` oder `module_window` verwenden. Der Migrations- und Prüfbericht steht in `docs/UI-AUDIT.md`. Systemdialoge bleiben die oben beschriebene Ausnahme.

## Ablauf für neue UI-Arbeit

1. Dieses Dokument und das passende sichtbare Muster ansehen.
2. Vorhandene GTK-Komponenten einsetzen und Tokens einhalten.
3. Fehlendes Muster zuerst im Katalog ergänzen; neue Zustände und Interaktion dokumentieren.
4. In der App implementieren. Bestehende Systemdialoge nicht unnötig ersetzen.
5. Normal-, Fokus-, deaktivierten, Lade-, Fehler- und Leerzustand prüfen, soweit relevant.
6. Auf kompakter Fenstergröße und mit Tastatur kontrollieren. Sichtbare Abweichungen beheben.
7. Bei Designänderungen Tokens, Beispiele, GTK-Umsetzung und Dokumentation zusammen anpassen.


## Tastaturhilfe und Vollbild

F1 öffnet die durchsuchbare Tastaturhilfe als eigenen Dialog aus Titel, Suchfeld, scrollbarer zweispaltiger Liste und Schließen. Sie verwendet denselben Shortcut-Katalog wie die Eingabeverarbeitung. Die Website zeigt das Muster im Bereich Navigation.

Der optionale Bildtext im Vollbild liegt auf einer schwarzen Fläche mit 65 % Deckkraft, weißem 12-px-Text und 12-px-Radius. N blendet ihn aus. Markierungen müssen auch mit Text erkennbar sein. Im Vollbild verschwinden die App-Leisten; nach dem Verlassen gelten wieder ihre vorherigen Sichtbarkeiten.

## Ungespeicherte Änderungen

Die kompakte Abfrage bietet „Abbrechen“, „Verwerfen“ und „Speichern“. Abbrechen und Escape lassen das Bild offen; Verwerfen führt die angeforderte Aktion aus. Speichern öffnet den Exportdialog und führt die Aktion erst nach erfolgreichem Speichern in voller Auflösung aus. Abbruch, Fehler oder eine lediglich verkleinerte Exportkopie schließen das Arbeitsbild nicht. Speichern ist die schwarze Hauptaktion; Abbrechen erhält den Anfangsfokus.


## Hierarchie und aufgabenbezogene Gruppen (1.1)

Die Erkenntnisse in `../knowlede.md` und die Bestandsaufnahme in `../redesign.md` ergänzen diesen Vertrag. Das Bild und die Aufgabe haben Vorrang vor Dekoration.

- Auswahl ist keine Abschlussaktion: helle ausgewählte Fläche (`color-selected`), dunkle Kontur (`color-selected-border`) und ein sichtbares Häkchen bzw. Radiozeichen. Nur die Hauptaktion ist durchgehend dunkel. Zeichensymbole bleiben dunkel und 24 px groß.
- Karten trennen über Fläche und Abstand. Eingaben erhalten eine eigene erkennbare Begrenzung (`color-control-border`); dekorative Linien bleiben leiser. GTK liest dieselben Rollenfarben, Schriftgrößen und Radien wie die HTML-Referenz.
- Feldlabel und Eingabe: 4 px Abstand; voneinander unabhängige Felder: 16 px; größere Sektionen: 24 px. Reglername und Zahlenwert gehören zur jeweiligen Bahn. Zahlenfelder sind rechtsbündig.
- Export: Zusammenfassung, offen sichtbares Speicherziel (Dateiname und Ordner), Format, Qualität, Auflösung, Metadaten, weitere Optionen. Das Speicherziel darf nicht unter einem geschlossenen Expander versteckt werden.
- Bildinformationen: Datei, Abmessungen & Druck, Farben, Speicher & Anzeige. Vollständige bisherige Daten bleiben zugänglich. Horizontale und vertikale DPI haben sichtbare Beschriftungen.
- Bildvorschauen liegen auf einer neutralen Fläche (`color-preview`). Vollständiges Bild einpassen; niemals für das Layout zuschneiden oder verändern. Fehlermeldungen nennen ausdrücklich das Scheitern.
- Leere Vorschaulisten erklären, ob ein Ordner fehlt oder Filter keine Treffer liefern, und bieten Ordnerauswahl bzw. Filter zurücksetzen an. Zeichen-Rückgängig bleibt bis zum ersten Strich deaktiviert.
