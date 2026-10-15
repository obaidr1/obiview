"""Validated export preferences, file naming and persistent named profiles."""
from dataclasses import asdict, dataclass, fields
import json
import os
from pathlib import Path
import tempfile


FORMAT_CHOICES = {
    'JPEG': ('.jpg', 'JPEG – JPG/JPEG'),
    'PNG': ('.png', 'PNG'),
    'GIF': ('.gif', 'GIF'),
    'WEBP': ('.webp', 'WebP'),
    'TIFF': ('.tif', 'TIFF'),
    'BMP': ('.bmp', 'BMP'),
    'ICO': ('.ico', 'Windows-Icon (ICO)'),
    'PDF': ('.pdf', 'PDF – aktuelle Seite'),
    'JPEG2000': ('.jp2', 'JPEG 2000'),
    'PPM': ('.ppm', 'PPM'),
}
ALIASES = {ext: fmt for fmt, (ext, _) in FORMAT_CHOICES.items()}
ALIASES.update({'.jpeg': 'JPEG', '.tiff': 'TIFF'})


@dataclass(frozen=True)
class SaveSettings:
    quality: int = 95
    progressive: bool = False
    grayscale: bool = False
    chroma444: bool = False
    keep_exif: bool = True
    keep_icc: bool = True
    keep_comment: bool = True
    keep_xmp: bool = True
    gif_interlace: bool = False
    gif_transparency: bool = True
    png_compression: int = 6
    webp_lossless: bool = False
    target_kib: int = 0

    def __post_init__(self):
        limits = {'quality': (1, 100), 'png_compression': (0, 9), 'target_kib': (0, 1_000_000)}
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name in limits:
                low, high = limits[field.name]
                if type(value) is not int or not low <= value <= high:
                    raise ValueError(f'Ungültiger Wert für {field.name}: {value}')
            elif type(value) is not bool:
                raise ValueError(f'Ungültiger Schalter: {field.name}')

    @classmethod
    def legacy(cls, quality=95, metadata=True):
        return cls(quality=max(1, min(100, int(quality))), keep_exif=metadata,
                   keep_icc=metadata, keep_comment=metadata, keep_xmp=metadata)


def filename_for_format(name, fmt):
    """The selected format wins; do not silently encode JPEG under a PNG name."""
    name = name.strip()
    if not name or name in ('.', '..') or '/' in name or '\x00' in name:
        raise ValueError('Bitte einen Dateinamen ohne Ordnerpfad eingeben.')
    if fmt not in FORMAT_CHOICES:
        raise ValueError('Unbekanntes Ausgabeformat.')
    path = Path(name)
    if ALIASES.get(path.suffix.lower()) == fmt:
        return name
    return str(path.with_suffix(FORMAT_CHOICES[fmt][0]))


class SaveProfiles:
    def __init__(self, path=None):
        self.path = Path(path) if path else Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')/'bildblick'/'save-profiles.json'
        self.profiles = {}
        self.error = None
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding='utf-8'))
                if raw.get('version') != 1 or not isinstance(raw.get('profiles'), dict):
                    raise ValueError('Unbekanntes Profilformat')
                for name, value in raw['profiles'].items():
                    self.validate_name(name)
                    if value['format'] not in FORMAT_CHOICES:
                        raise ValueError('Unbekanntes Bildformat im Profil')
                    SaveSettings(**value['settings'])
                self.profiles = raw['profiles']
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
            self.error = f'Profile konnten nicht gelesen werden: {error}'

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str) or not name.strip() or len(name) > 80:
            raise ValueError('Bitte einen Profilnamen mit 1–80 Zeichen eingeben.')

    def load(self, name):
        value = self.profiles[name]
        return value['format'], SaveSettings(**value['settings'])

    def save(self, name, fmt, settings):
        name = name.strip()
        self.validate_name(name)
        if fmt not in FORMAT_CHOICES:
            raise ValueError('Unbekanntes Bildformat')
        updated = dict(self.profiles)
        updated[name] = {'format': fmt, 'settings': asdict(settings)}
        self.write(updated)

    def delete(self, name):
        updated = dict(self.profiles)
        del updated[name]
        self.write(updated)

    def write(self, updated):
        if self.error:
            raise ValueError(self.error)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='.save-profiles-', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump({'version': 1, 'profiles': updated}, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            self.profiles = updated
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
