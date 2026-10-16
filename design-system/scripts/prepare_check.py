"""Generate an ignored self-testing browser page; never part of the catalogue."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text().replace('</head>','<script src="scripts/browser-check.js" defer></script></head>')
(root/'.browser-check.html').write_text(html)
print(root/'.browser-check.html')
