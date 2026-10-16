# Bildblick 0.7.0

- Zeichnen: sechs direkt wählbare Werkzeuge mit eigenen Symbolen und Beschriftung – Stift, weicher Pinsel, Linie, Pfeil, Rechteck und Ellipse.
- Das Fenster wächst beim manuellen Zoom bis zur verfügbaren Bildschirmfläche. Danach bleiben weitere Vergrößerung und Scrollen möglich.
- I öffnet die erweiterten Bildinformationen mit Datei- und Ordnerdaten, ursprünglichen und aktuellen Abmessungen/Farbtiefen, physischen Druckmaßen, RGB-Farbzählung, Datei-/Pixel-Speicher, Datum und Ladezeit.
- X-/Y-DPI getrennt ändern, ohne Pixel neu zu berechnen; Rückgängig, Export und Druck berücksichtigen beide Achsen.
- Eigene Leseansichten für EXIF, IPTC und Kommentare.

92 Funktionstests und der native GTK-Integrationstest prüfen die Änderungen. Die grafische Prüfung läuft unter Fedora 44 mit X11/Xvfb/Openbox; Wayland, reale Drucker/Scanner und vollständige Barrierefreiheit benötigen weitere manuelle Prüfung.

## Installation

Archiv entpacken und im entpackten Ordner ./install.sh ausführen. Eine vorhandene Benutzerinstallation wird aktualisiert. Danach Bildblick neu starten.
