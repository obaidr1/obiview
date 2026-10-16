"""Check readable text and identifiable control boundaries in the shared palette."""
import json
from pathlib import Path
import unittest

TOKENS=json.loads((Path(__file__).resolve().parents[1]/'design-system/tokens.json').read_text())
def luminance(hex_color):
    values=[int(hex_color[i:i+2],16)/255 for i in (1,3,5)]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(v*w for v,w in zip(linear,(.2126,.7152,.0722)))
def contrast(a,b):
    light,dark=sorted((luminance(TOKENS[a]),luminance(TOKENS[b])),reverse=True)
    return (light+.05)/(dark+.05)

class DesignContrast(unittest.TestCase):
    def test_text_roles_on_all_content_surfaces(self):
        for text in ('color-ink','color-muted','color-error'):
            for background in ('color-surface','color-card','color-white','color-selected'):
                with self.subTest(text=text,background=background):
                    self.assertGreaterEqual(contrast(text,background),4.5)
        self.assertGreaterEqual(contrast('color-white','color-ink'),4.5)

    def test_input_and_selected_boundaries(self):
        for edge in ('color-control-border','color-selected-border'):
            for background in ('color-surface','color-card','color-white','color-selected'):
                with self.subTest(edge=edge,background=background):
                    self.assertGreaterEqual(contrast(edge,background),3)
