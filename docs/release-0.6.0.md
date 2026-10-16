# Bildblick 0.6.0 – Einheitliche Bearbeitungsdialoge

- Große Live-Vorschau, Originalvergleich und Zurücksetzen für Helligkeit/Kontrast/Farbe, Schärfen/Weichzeichnen, freie Drehung, Rahmen, Rote Augen, Farbreduktion, Farbkanaltausch, automatischen Zuschnitt, Leinwand und Text.
- Breite Slider für visuelle Parameter wie Kontrast, Sättigung, Schärfe, Winkel, Toleranz und Farbanzahl.
- Direkt anklickbare Rahmenstile, Farbkanal-Reihenfolgen und Zeichenwerkzeuge sowie Einheiten, Interpolation, Größenvorgaben, Auswahlverhältnisse, Druckmodi und Exportformate.
- Regler für Strichbreite, PNG-Kompression, Exportqualität und weitere einfache Einstellungen. Präzise Bildmaße, Positionen und Dateinamen bleiben Eingabefelder.
- Abbrechen verwirft offene Vorschauen. Anwenden erzeugt einen rückgängig machbaren Schritt und wartet nötigenfalls auf eine gültige Vorschau. Veraltete Ergebnisse verändern das Bild nicht.

86 Funktionstests und der erweiterte native GTK-Integrationstest prüfen Pixelresultate, direkte Auswahl, Slider, Vorschau, Zurücksetzen, Abbrechen, Anwenden, Undo und Fehlerkorrektur. Die neue Werkzeugvorschau verarbeitet Originalpixel im Hintergrund; große Bilder können mehr Rechenzeit benötigen.

Archiv entpacken und `install.sh` ausführen. Eine laufende Bildblick-Instanz danach schließen und neu öffnen.
