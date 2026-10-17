# Dialoggrößen in Bildblick

Version 1.0 · 17. Oktober 2026

## Ziel

Ein Dialog soll alle seine Bedienelemente und die Abschlussaktionen gleichzeitig zeigen. Eine gemeinsame feste Breite und Höhe verhindert das bei Formularen und Variantenlisten. Deshalb leitet Bildblick die Größe aus der Komplexität des jeweiligen Dialogs und der natürlichen GTK-Messung seines Inhalts ab.

## Größenregel

1. Gezählt werden Bedienelemente und Informationselemente: Buttons und Auswahlbuttons, Kontrollkästchen, Eingaben, Regler, Auswahllisten, Schalter, Textfelder, Beschriftungen und Vorschaubilder. Inhalte geschlossener Expander werden mitgezählt, damit die Breite auch bei geöffneten Zusatzoptionen ausreicht. GTK-interne Kindwidgets zählen nicht.
2. Die empfohlene Breite beträgt `480 + max(0, Anzahl − 4) × 24` logische Pixel. Sie ist auf 960 px begrenzt. So bleiben kleine Aufgaben kompakt und Varianten-/Formulardialoge erhalten mit wachsender Zahl von Bedienelementen mehr Platz.
3. Die natürliche Mindestbreite des GTK-Inhalts darf die Empfehlung übersteigen, wenn der Bildschirm Platz bietet. Lange Namen und Pfade werden dafür umbrochen; sie dürfen die Breite nicht aufblasen.
4. Die Höhe wird nach dem Umbruch an der tatsächlichen natürlichen Höhe des Inhalts gemessen. Titel, Ränder und Aktionsleiste werden hinzugerechnet. Sie erhält keinen pauschalen Mindestwert.
5. Verfügbare Bildschirmgröße abzüglich 32 px begrenzt Breite und Höhe. Fenster bleiben größenveränderbar. Wenn der natürliche Inhalt höher ist als die verfügbare Bildschirmfläche, scrollt nur der Inhalt; die Aktionsleiste bleibt stehen. Kurze Meldungen messen sich weiter am Text.

Diese Formel ist eine reproduzierbare Startgröße, keine Behauptung, dass jede Bedienelementart gleich viel Platz benötigt. Die GTK-Naturmaße und die Sichtprüfung entscheiden bei jedem realen Dialog. Für alle Dialoge wird dieselbe Vorgehensweise verwendet: öffnen, alle aufklappbaren Bereiche öffnen, Bedienelemente zählen, erste Größe messen, Umbruch/Überlappung und Scrollbedarf ansehen, danach bei Bedarf Inhalte gruppieren und erneut messen.

## Bestandsaufnahme

`tests/ui_dialog_audit.py` öffnet die vollständigen App-Dialoge, Nebenfenster, Menüs, erweiterten Zustände und Exportformate. Der Bericht notiert pro Fenster die Bedienelementzahl, empfohlene/finale Maße und ob der Inhalt noch scrollen muss. Screenshots der zentralen und dichten Dialoge dienen zur Sichtprüfung. Systemdialoge (Datei, Farbe, Schrift, Druck) folgen der Desktopumgebung.

Bei Inhaltsüberhang ist die Reihenfolge der Korrektur: unwichtige Wiederholungen entfernen oder gruppieren, gleichartige Felder in eine zweispaltige Zeile setzen, unnötige Außenabstände reduzieren und nur dann scrollen, wenn das Fenster die verfügbare Bildschirmhöhe erreicht. Abschlussaktionen bleiben stets sichtbar.
