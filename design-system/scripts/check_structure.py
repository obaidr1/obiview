"""Check the offline catalogue's links, accessible labels and source coverage."""
from html.parser import HTMLParser
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
class Catalogue(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []; self.references = []; self.files = []; self.inputs = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
        for key in ('for', 'aria-labelledby', 'aria-describedby'):
            self.references.extend(attrs.get(key, '').split())
        for key in ('href', 'src'):
            value = attrs.get(key, '')
            if value.startswith('#'): self.references.append(value[1:])
            elif value and not value.startswith(('http:', 'https:', 'data:')): self.files.append(value)
            if tag in ('link', 'script') and value.startswith(('http:', 'https:')):
                raise AssertionError('External dependency: '+value)
        if tag in ('input', 'textarea', 'select'): self.inputs.append((tag, attrs))

html = (root/'index.html').read_text()
c = Catalogue(); c.feed(html)
assert len(c.ids) == len(set(c.ids)), 'Duplicate IDs'
assert not set(c.references)-set(c.ids), 'Broken ID references: '+str(set(c.references)-set(c.ids))
for file in c.files: assert (root/file).is_file(), file
for tag, attrs in c.inputs:
    if attrs.get('type') in ('checkbox','radio','file'): continue
    assert attrs.get('aria-label') or attrs.get('id') in c.references, ('Unlabelled field', attrs)
assert html.count('class="specimen"') == 17
assert len(re.findall(r'<symbol id="i-',html)) == 32
# Core themes + custom widget and dialog families must be represented in the mapping.
for name in ('ChoiceButtons','SliderField','ToolDialog','EffectsDialog','SaveDialog','ResizeDialog','ImageInfoDialog','ColorButton','FontButton','ComboBoxText','Expander','PopoverMenuBar','FlowBox','DrawingArea','Picture','Spinner','PrintOperation'):
    assert name in html, 'Missing native component mapping: '+name
print(f'PASS: 17 sections, 32 icons, {len(c.ids)} unique IDs, all references/files and labelled fields.')
