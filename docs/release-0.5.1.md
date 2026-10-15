# Bildblick 0.5.1 – Effekte mit Live-Vorschau

- Zehn direkt anklickbare Effekte statt eines Dropdowns.
- Große Bildvorschau und umschaltbarer Originalvergleich.
- Intensität von 0 bis 100 Prozent für jeden Effekt, einschließlich Sepia, Relief und Kantenerkennung.
- Passende zusätzliche Regler für Radius, Randbreite, Streuung, Pixelgröße oder Tropfenpaare.
- Einstellungen bleiben beim Wechsel zwischen Effekten erhalten; Zurücksetzen betrifft den gewählten Effekt.
- Anwenden übernimmt den Effekt in Originalauflösung als einen Undo-Schritt. Abbrechen verwirft sämtliche offenen Vorschauen.
- Asynchrone Vorschauen blockieren die Bedienung nicht; veraltete Ergebnisse werden verworfen.

Die kompakte Hauptansicht bleibt unverändert. Bei großen Bildern ist die Vorschau auf höchstens 1200 × 1200 Pixel verkleinert; pixelabhängige Effekte können deshalb beim Anwenden in Originalauflösung abweichen.

Geprüft mit 86 Funktionstests und dem nativen GTK-Integrationstest unter Fedora 44. Der GUI-Test prüft direkte Auswahl, passende Regler, Intensität, Originalvergleich, Einstellungswechsel, Zurücksetzen, Abbrechen, veraltete Ergebnisse und Anwenden mit Rückgängig.

Installation: Archiv entpacken und `install.sh` starten. Eine bereits laufende Bildblick-Instanz schließen und erneut öffnen, damit der neue Dialog geladen wird.
