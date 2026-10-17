# Designwissen für Bildblick

Stand: 16. Oktober 2026. Grundlage: *Refactoring UI* von Adam Wathan und Steve Schoger, bereitgestellte PDF mit 252 Seiten. Der gesamte extrahierbare Buchtext wurde gelesen; Titel und ausgewählte Vorher-/Nachher-Beispiele wurden zusätzlich als gerenderte Seiten geprüft. Die folgenden Notizen sind eigene Zusammenfassungen und Entscheidungen für Bildblick, keine Abschrift des Buchs. Seitenangaben beziehen sich auf die PDF-Seiten, die hier mit der gedruckten Seitennummer übereinstimmen.

## 1. Von einer Aufgabe ausgehen

**Buch, S. 8–19:** Eine Oberfläche wird verständlicher, wenn sie um eine konkrete Handlung gebaut wird. Kurze Zyklen aus Entwurf, Implementierung und Prüfung decken Probleme auf, die ein statisches Idealbild verdeckt.

**Für Bildblick:** Jede Ansicht beantwortet: Was bearbeite ich? Was verändert sich? Wie übernehme oder verwerfe ich es? Der Exportdialog ist ein Ablauf aus Ziel, Format, Größe und Speichern. Effekte sind ein Ablauf aus Auswahl, Vorschau, Stärke und Anwenden. Die komplette Menüstruktur muss diese Aufgaben zugänglich machen; sie muss nicht durch eine neue Navigation ersetzt werden.

## 2. Eine erkennbare Persönlichkeit und wenige Entscheidungen

**Buch, S. 20–32:** Schrift, Form, Farbe und Sprache prägen gemeinsam den Charakter. Begrenzte Skalen ersparen willkürliche Einzelentscheidungen.

**Für Bildblick:** Die gewünschte ruhige, helle Oberfläche bleibt erhalten: warme neutrale Flächen, dunkle Hauptaktion, klare Sans-Serif, gerundete Bedienelemente. Keine neue Akzentfarbe nur um der Veränderung willen. Farben, Abstände, Größen und Zustände kommen aus der Designreferenz. Native GTK- und HTML-Werte sollen dieselbe Quelle nutzen, statt nur zufällig gleich auszusehen.

## 3. Hierarchie entsteht durch Unterschiede

**Buch, S. 36–47, 54–59:** Nicht jedes Element verdient dieselbe Aufmerksamkeit. Gewicht, Kontrast und Zurücknahme der Umgebung sind oft wirksamer als größere Schrift. Überschriften müssen nicht automatisch riesig sein; schwere Symbole können Text übertönen.

**Für Bildblick:** Das Bild ist der wichtigste Inhalt. Danach folgen aktueller Werkzeugname, veränderbare Werte und Hauptaktion. Hinweise bleiben gut lesbar, aber ruhiger. Gruppenüberschriften ordnen; sie werden nicht zu Werbeüberschriften. Auswahlbuttons sind Zustände, keine konkurrierenden schwarzen Hauptaktionen. Symbole bleiben in ihrer vorgesehenen kleinen Größe.

## 4. Daten und Formulare unterschiedlich behandeln

**Buch, S. 48–52:** Daten können häufig aus Format und Kontext verstanden werden; überflüssige Beschriftungen erschweren die Hierarchie. Für Formulare gilt dieser Verzicht ausdrücklich nicht. Bei technischen Daten helfen stabile Labels beim Suchen.

**Für Bildblick:** Dateiname, Maße und Format dürfen eine kompakte Zusammenfassung bilden. Breite, Höhe, DPI und Metadaten brauchen klare Beschriftungen. Lange Dateipfade müssen auswählbar und vollständig erreichbar bleiben. Kein Entfernen technischer Bildinformationen zugunsten einer hübscheren Karte.

## 5. Aktionen nach Wichtigkeit gestalten

**Buch, S. 60–62:** Haupt-, Neben- und seltene Aktionen benötigen unterschiedliche visuelle Gewichte. Eine destruktive Aktion muss nicht überall die lauteste sein.

**Für Bildblick:** Pro Dialog eine dunkle Hauptaktion. Abbrechen, Zurücksetzen, Originalvergleich und Ordnerauswahl bleiben sichtbar, aber nachgeordnet. In der Speicherabfrage bleibt Speichern die Hauptaktion; Verwerfen und Abbrechen bleiben getrennt. Tastaturfokus auf Abbrechen ist eine bewusste Schutzentscheidung. Fehler dürfen den erfolgreichen Abschluss niemals vortäuschen.

## 6. Abstand vermittelt Zugehörigkeit

**Buch, S. 66–75, 96–99:** Abstand ist ein Strukturmittel. Innerhalb einer Gruppe müssen Elemente enger beieinander liegen als zwischen verschiedenen Gruppen. Dichte ist eine bewusste Entscheidung, kein Zufall.

**Für Bildblick:** Feldname und Eingabe bilden eine Einheit, mehrere Felder eine Sektion. Zielwerte: 4–8 px innerhalb eines Felds, 16 px zwischen Feldern, 24 px zwischen größeren Abschnitten. Menü und Symbolleiste bleiben bewusst kompakt. Eine eigene Karte um jeden Regler würde das Gegenteil bewirken.

## 7. Verfügbaren Platz nicht zwanghaft füllen

**Buch, S. 76–99:** Maximalbreiten und inhaltliche Größen sind oft sinnvoller als prozentuale Raster. Große Elemente und kleine Bedienelemente skalieren nicht identisch.

**Aktualisierte Produktregel (17. Oktober 2026):** Die frühere gemeinsame Maximalbreite von 520 px und der feste 760-px-Rahmen sind aufgehoben. Die Breite wächst mit der Anzahl der Bedienelemente, die Höhe folgt der gemessenen natürlichen Inhaltshöhe, beides begrenzt durch den Bildschirm. Siehe `docs/DIALOG-SIZING.md`. Freier Platz in einem Werkzeug ist weniger schädlich als künstlich gestreckte Buttons; unnötiges Scrollen wird durch passende Gruppierung und Anordnung vermieden.

## 8. Lesbarkeit systematisch sichern

**Buch, S. 102–134:** Wenige Schriftgrößen und Gewichte ergeben Konsistenz. Längere Texte brauchen geeignete Zeilenlänge, linksbündige Ausrichtung und ausreichenden Zeilenabstand. Vergleichbare Zahlen sollten gleich ausgerichtet werden.

**Für Bildblick:** 12 px für knappe Zusatzdaten, 14 px für Bedienung, 22 px für Dialogtitel; normal und semibold reichen. Hilfetexte nicht durch immer kleinere Schrift retten. Kurze, lokale Hinweise ersetzen lange Einleitungen. Exakte Zahlenfelder rechtsbündig ausrichten. Einheiten ausdrücklich benennen. Keine fremden Fonts nachladen.

## 9. Farben als Rollen definieren

**Buch, S. 138–168:** Eine brauchbare Palette umfasst abgestufte Neutraltöne und Zustände. HSL erleichtert gestalterische Entscheidungen, ersetzt aber keine visuelle Prüfung. Wahrgenommene Helligkeit ist nicht identisch mit dem HSL-Lichtwert. Farbe darf nicht das einzige Signal sein.

**Für Bildblick:** Rollen wie Text, Sekundärtext, Fläche, Eingabegrenze, Auswahl, Sliderbahn und Fehler explizit festlegen. Eine dezente Kartenlinie reicht nicht automatisch als Erkennung einer Eingabe. Aktive Auswahl erhält neben der Fläche ein sichtbares Auswahlzeichen. Fehler enthalten eine verständliche Nachricht. Kontraste rechnerisch prüfen, danach im Kontext ansehen; keine pauschale Behauptung vollständiger Barrierefreiheit aus einer Farbprüfung ableiten.

## 10. Tiefe zeigt Ebenen

**Buch, S. 172–196:** Schatten und unterschiedliche Flächen können erklären, was über etwas anderem liegt. Wiederverwendbare Höhenstufen sind besser als individuelle Dekoration. Auch flache Gestaltung kann Ebenen zeigen.

**Für Bildblick:** Bildfläche, Werkzeug und darüberliegende Bestätigung müssen unterscheidbar sein. Der modale Hintergrund und ein zurückhaltender Fensterschatten reichen. Karten brauchen nicht gleichzeitig helle Fläche, auffällige Kontur und eigenen Schatten. Fokusrahmen sind Bedienfeedback und dürfen beim Vereinfachen nicht entfernt werden.

## 11. Bilder zuverlässig einbetten

**Buch, S. 200–217:** Bildinhalt verändert Kontrast und Layout. Symbole sind für bestimmte Größen gezeichnet. Beliebige Nutzerbilder brauchen einen stabilen Rahmen.

**Für Bildblick:** Vorschauen müssen auch bei weißen, schwarzen, transparenten, sehr schmalen oder sehr hohen Bildern funktionieren. Ein neutraler Vorschaugrund und korrektes Einpassen verhindern optisches Verschwinden. Die im Buch für Bildkarten vorgeschlagene automatische Beschneidung ist für unsere Bearbeitungsvorschau ungeeignet: Das komplette Bild muss sichtbar bleiben. Ebenfalls ungeeignet wäre es, Nutzerbilder zur Verbesserung der UI-Lesbarkeit abzudunkeln oder farblich zu verändern. Beschriftungen gehören außerhalb des Bilds; Vollbildtexte erhalten ihre eigene Fläche.

## 12. Leere, wartende und fehlerhafte Zustände entwerfen

**Buch, S. 234–236; ergänzend S. 16–19:** Eine Oberfläche ohne Beispieldaten ist kein Sonderfall, sondern oft der erste Kontakt. Sie braucht eine klare nächste Handlung.

**Für Bildblick:** Ein leeres Fenster bietet einen direkt nutzbaren „Bild öffnen“-Button sowie kurze Hinweise auf Drag-and-drop und Zwischenablage. Vorschauarbeit wird als Arbeit angezeigt; ein Fehler bleibt als Fehler sichtbar. Nicht verfügbare Aktionen dürfen keine erfolgreiche Bedienung suggerieren. Kein simuliertes Bild oder fiktiver Fortschritt.

## 13. Weniger Rahmen, bessere Gruppen

**Buch, S. 220–246:** Bestehende Komponenten können durch bessere Zustände und Anordnung gewinnen. Trennung kann über Abstand und Flächen statt über immer mehr Linien erfolgen. Auswahlkarten können verständlicher sein als versteckte Listen.

**Für Bildblick:** Direkt sichtbare Optionen bleiben erhalten. Ausgewählte Optionen erhalten einen eindeutigen Marker, aber weniger optisches Gewicht als „Anwenden“. Metadaten werden nach Datei, Bild und technischen Details gegliedert. Keine riesigen Menüs mit Illustrationen: Die häufigen Tastatur- und Desktopabläufe bestimmen die Dichte.

## 14. Nachweis statt Bauchgefühl

**Buch, S. 250–252:** Gute Entwürfe werden durch genaues Hinsehen, Nachbauen und Vergleichen verstanden.

**Für Bildblick:** Änderungen in der HTML-Referenz und in GTK gegen denselben Vertrag prüfen. Zusätzlich zu Screenshots: lange Namen, kleinere Bildschirme, Fokus, Tastatur, deaktivierte Zustände, erfolgreiche und fehlgeschlagene Aktionen testen. Bestehende Funktionen und Shortcuts sind Teil der Qualität. Eine reine CSS-Änderung beweist noch keine gelungene Bedienung.

## Verbindliche Leitfrage für neue Elemente

Was ist hier die Hauptaufgabe, woran erkennt man den aktuellen Zustand, welche Information braucht man dafür, und was kann leiser oder erst auf Nachfrage erscheinen?

Die konkrete Bestandsaufnahme, Priorisierung und Umsetzung stehen in [redesign.md](redesign.md). Die verbindliche Komponentenreferenz bleibt [design-system/DESIGN.md](design-system/DESIGN.md).
