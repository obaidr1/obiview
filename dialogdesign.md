# Dialogdesign

Dieser Dialog verletzt etliche grundlegende Prinzipien des modernen Interface- und Interaktionsdesigns (wie Material Design oder Human Interface Guidelines). Hier sind die gravierendsten UX/UI-Probleme im Detail:

### 1. Fatale UI-Affordance & inkonsistente Selection Controls

* **Falsche Komponentenauswahl für Single-Choice:** Bei „Einheit“, „Interpolation“ und „Größenvorgaben“ handelt es sich um exklusive Einzelauswahlen. Anstelle von etablierten UI-Elementen wie **Segmented Buttons**, **Radio Buttons** oder einem **Dropdown-Menü** wurden frei schwebende Textlabels verwendet, von denen nur das aktive Element eine Kontur hat.
* **Fehlende Interaktions-Hinweise (Affordance):** Die inaktiven Optionen („Prozent“, „Zoll“, „Bikubisch“ etc.) sehen aus wie statischer Text und nicht wie klickbare Buttons. Es fehlt an visueller Abgrenzung, Hover-States oder Container-Formen.
* **Das Häkchen-Icon:** Ein Häkchen (`✓`) innerhalb eines Buttons ist redundant, wenn der Status bereits durch die Kontur/Füllung visualisiert wird, und erinnert verwirrend an eine Checkbox.

---

### 2. Broken Inputs & Stepper-Logik

* **Völlig verkehrte Ausrichtung der Stepper:** In den Feldern für *Breite*, *Höhe* und *DPI* liegt der Zahlenwert ganz rechts, direkt gefolgt von den Plus-/Minus-Tasten. Links klafft ein riesiger Leerraum.
* Standard: Zahl linksbündig (oder sauber formatiert), Stepper (`-` / `+`) gebündelt ganz rechts oder jeweils an den Außenkanten.
* **Fehlende Einheiten-Angabe im Input:** In den Feldern für Breite und Höhe steht nur „1920“ statt „1920 px“. Der Nutzer muss den Blick nach oben zur Einheit abwenden, um sicherzugehen.
* **Stepper für hohe Pixelwerte:** Bei Werten wie 1920 Pixeln sind `+`/`-`-Schritte meist unbrauchbar, wenn die Schrittweite nicht klar definiert ist (z. B. 1px vs. 100px).

---

### 3. Informationsarchitektur & Redundanz

* **Widersprüchliche Presets:** Es gibt gleich zwei verschiedene Bereiche für Schnellwahlen: „Schnelle Größenänderung“ (Prozent-Buttons) und „Größenvorgaben“ (Pixel-Auflösungen). Das fragmentiert die geistige Landkarte des Nutzers völlig.
* **Veraltete Presets:** Auflösungen wie `640 × 480` oder `800 × 600` sind Relikte aus den 1990er-Jahren und für moderne Apps meist Ballast. Zudem fehlen moderne Kategorien (z. B. Social Media, 4K, Display).
* **Konflikt bei „Größenvorgaben“:** Was passiert, wenn man manuell eine Zahl ändert? Springt „Größenvorgaben“ automatisch wieder auf „Keine Vorgabe“? Die visuelle Koppelung ist hier komplett ungelöst.

---

### 4. Layout, Spacing & Clipping-Fehler

* **Abgeschnittene Inhalte (Clipping):** In der Karte „Größenvorgaben“ ist die untere Zeile (`1024 × 768`, `1280 × 720`, `1920 × 1080`) zur Hälfte durch den Kartenrand bzw. Dialogrand abgeschnitten. Das ist ein fataler Layout-Bug.
* **Layout-Verschiebung durch „DPI“:** Unter „Berechnung“ steht das DPI-Feld zusammenhanglos rechts oben, während links eine zweispaltige Liste mit Interpolations-Optionen liegt. Das erzeugt eine unruhige, asymmetrische Fluchtlinie.
* **Ungleichmäßiges Padding:** Die Abstände zwischen den logischen Blöcken und innerhalb der Karten wirken zufällig zusammengewürfelt statt auf einem konsistenten 8pt/4pt-Grid zu basieren.

---

### 5. Fehlende visuelle Metaphern

* **Seitenverhältnis als einfache Checkbox:** Der Standard in allen gängigen Tools (Photoshop, Figma, OS-Tools) ist ein **Kettenglied-Icon (Link/Unlink)** direkt vertikal zwischen den Eingabefeldern von *Breite* und *Höhe*. Eine Checkbox darunter reißt die zusammengehörenden Elemente visuell auseinander.

---

### Empfohlener Umbau (Best Practice):

1. **Header:** Bildvorschau mit Live-Größenänderung und kompakter Anzeige von Original- vs. Neugröße.
2. **Dimensionen:** Dropdown oder Segmented Control für Einheit (Pixel / % / cm). Breite und Höhe nebeneinander, verbunden durch ein Kettensymbol für das Seitenverhältnis.
3. **Presets:** Ein einziges sauberes Dropdown („Benutzerdefiniert“, „1080p Full HD“, „4K“, „Instagram Post“ etc.) statt abgeschnittener Button-Grids.
4. **Erweitert (Advanced Settings):** Interpolation und DPI hinter einem einklappbaren Bereich verstecken – 90 % der Nutzer benötigen nur Breite/Höhe und wollen nicht mit Algorithmen wie „Lanczos“ überfordert werden.

## Anwendung auf alle Dialoge

Dieses Muster ist der Prüfmaßstab für sämtliche Bildblick-Dialoge. Auswahlmöglichkeiten müssen sichtbar interaktiv sein und dürfen keine statischen Textlabels imitieren. Exklusive Auswahl bekommt eine passende Auswahlkomponente; kontinuierliche Werte erhalten Slider mit sichtbarem Zahlenwert; exakte Maße erhalten beschriftete Zahlenfelder mit Einheiten und verständlicher Schrittweite. Redundante Schnellwahlen werden zusammengeführt. Häufige Aufgaben bleiben sichtbar, seltene Optionen kommen in einen aussagekräftig benannten einklappbaren Bereich. Dialoge werden nach ihrem Inhalt bemessen; Fußzeilenaktionen bleiben sichtbar und Inhalte dürfen nicht abgeschnitten werden. Jedes Dialogmodul wird einzeln geprüft und an die gemeinsamen Abstände, Eingaben und Aktionshierarchie angepasst.

## Dialoginventar und Umsetzung

Gemeinsame Regeln werden in `dialog_layout.py`, `ui_theme.py`, `edit_controls.py` und `tool_dialogs.py` umgesetzt. So erhalten gleichartige Felder und Auswahlgruppen dasselbe Verhalten über alle Dialoge hinweg.

| Dialog oder Modul | Prüfung und passende Umsetzung |
| --- | --- |
| Größe ändern | Live-Vorschau, Original-/Neumaße, Einheitenwahl, verknüpfte Maße, ein Vorgabenfeld, explizite px/%/cm/in-Suffixe, Schrittweiten und einklappbare Interpolation/DPI. |
| Bild exportieren | Genau eine direkte Formatwahl für alle unterstützten Formate; Auflösungswahl mit proportional verknüpften Maßen; Qualität als Regler; seltene Codec- und Profiloptionen eingeklappt; sichtbare Dateiname- und Ordnerfelder. |
| Effekte | Jede Variante direkt auswählbar; Intensität und Effektparameter als Regler mit aktuellem Wert; Vorschau, Originalvergleich, Zurücksetzen. |
| Bildanpassungen | Looks als exklusive Auswahl; kontinuierliche Bildwerte als Regler mit Zahlenwert; Vorschau und Zurücksetzen. |
| Zeichnen | Alle sechs Werkzeuge mit Symbol und Text; Strichbreite als Regler plus genauer px-Eingabe; Farbe und zustandsabhängiges Rückgängigmachen. |
| Bildinformationen und Metadaten | Werte in aufgabenbezogenen Gruppen; DPI-Achsen beschriftet und mit Einheit; lange Werte auswählbar und umbrechend; Metadaten in separaten lesbaren Dialogen. |
| Drehen, Rahmen, Leinwand, Auswahl, Text, Rote Augen, Zuschneiden, Palette, Kanäle und Panorama | Gemeinsame `ToolDialog`-Form: direkte Auswahlbuttons, Slider für kontinuierliche Parameter, beschriftete Maße mit Einheiten, erklärte Stepper, Vorschau und sichtbare Fehlerzustände. |
| Drucken | Ausrichtung und Größenmodus direkt auswählbar; Breite/Höhe über ein Kettensymbol gekoppelt; cm-/%-Einheiten in den Eingaben; Position nur aktiv, wenn Zentrierung aus ist. Drucker und Papier bleiben im nativen GTK-Druckdialog. |
| Neues Bild, Scanner, Umbenennen, Öffnen mit, letzte Ordner | Dasselbe Feldraster und dieselben direkten Auswahlzustände; DPI und Bildmaße zeigen ihre Einheiten; native Datei- und Geräteauswahl folgt dem System. |
| Diashow, Exportoptionen, Stapelverarbeitung | Slider für Qualität/Zeit, Einheiten für Maximalmaße, unabhängige Optionen als Checkboxen und klare Zusammenfassungen vor destruktionsfreien Stapelaktionen. |
| Tastaturhilfe, Bestätigungen, Fortschritt und Meldungen | Gemeinsamer Dialograhmen mit dynamischen Abmessungen, sichtbarer Aktionsleiste, Escape/Abbrechen und kompakten textgerechten Höhen. |
| Histogramm, Miniaturen und Medien | Eigenständige Modulfenster mit gemeinsamer Fenstergeometrie; Medienwiedergabe zeigt echte Laufzeit- und Fehlerzustände. |
| Menüs, Datei-, Farb-, Schrift- und Systemdruckdialoge | Menüs behalten ihre native Popover-Bedienung. Betriebssystemdialoge bleiben systemeigen; app-eigene Beschriftungen, Schalter und Rückmeldungen folgen dem Bildblick-Vertrag. |

Finite Auswahlgruppen haben jetzt durchgehend eine sichtbare Kontur, Hover-Rückmeldung und helle aktive Fläche ohne redundantes Häkchen. Zahleneingaben stehen links; Stepper bleiben rechts. Jeder Stepper zeigt per Tooltip seine Schrittweite. Zahlenfelder, die eine Maßeinheit erwarten, zeigen die Einheit direkt am Eingabefeld.
