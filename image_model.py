"""Independent image operations for a native Linux viewer."""
import math
import os
from pathlib import Path
import tempfile
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ExifTags, UnidentifiedImageError
from save_options import SaveSettings
from image_export import write_image
import io
import re


FORMATS = {'.png': 'PNG', '.jpg': 'JPEG', '.jpeg': 'JPEG',
           '.webp': 'WEBP', '.bmp': 'BMP', '.tif': 'TIFF', '.tiff': 'TIFF',
           '.gif': 'GIF', '.ico': 'ICO', '.pdf': 'PDF', '.jp2': 'JPEG2000', '.ppm': 'PPM'}


def image_files(folder):
    Image.init()
    extensions = {ext for ext, fmt in Image.registered_extensions().items() if fmt in Image.OPEN}
    try:
        from native_codecs import extra_extensions
        extensions.update(extra_extensions())
    except ImportError:
        pass
    def natural(path):
        return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                     for part in re.split(r'(\d+)', path.name))
    return sorted((p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in extensions), key=natural)


def atomic_write(path, writer, overwrite=False):
    """Publish a complete output in the destination filesystem."""
    path = Path(path).absolute()
    fd, temporary = tempfile.mkstemp(prefix='.bildblick-', suffix=path.suffix, dir=path.parent)
    os.close(fd)
    try:
        writer(temporary)
        with open(temporary, 'rb') as stream:
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
            os.unlink(temporary)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def crop_box(start, end, size):
    """Normalize a drag in image coordinates, clamping to the image."""
    x1, x2 = sorted((start[0], end[0]))
    y1, y2 = sorted((start[1], end[1]))
    box = (max(0, min(size[0], math.floor(x1))),
           max(0, min(size[1], math.floor(y1))),
           max(0, min(size[0], math.ceil(x2))),
           max(0, min(size[1], math.ceil(y2))))
    return box if box[2] > box[0] and box[3] > box[1] else None


class ImageModel:
    def __init__(self):
        self.image = None
        self.path = None
        self.history = []
        self.future = []
        self.revision = self.saved_revision = 0
        self.next_revision = 1
        self.icc = None
        self.multiframe = False
        self.source_path = None
        self.frame_index = 0
        self.frame_count = 1
        self.duration = 100
        self.exif = b''
        self.metadata = {}
        self.xmp = b''
        self.comment = b''

    @property
    def dpi(self):
        try:
            values = self.image.info.get('dpi',(96,96)) if self.image else (96,96)
            value = values[0] if isinstance(values,(tuple,list)) else 96
            return float(value) if math.isfinite(float(value)) and 1 <= float(value) <= 9600 else 96
        except (TypeError,ValueError):
            return 96

    @property
    def dirty(self):
        return self.revision != self.saved_revision

    def load(self, path, frame=0):
        path = Path(path).absolute()
        exif_bytes = b''
        xmp = comment = b''
        try:
            with Image.open(path) as source:
                count = getattr(source, 'n_frames', 1)
                if not 0 <= frame < count:
                    raise ValueError('Seite außerhalb des Dokuments')
                source.seek(frame)
                if source.width*source.height > 80_000_000 or count > 10_000:
                    raise ValueError('Datei überschreitet die Grenze von 80 Megapixeln oder 10.000 Einzelbildern.')
                icc = source.info.get('icc_profile') if source.mode in ('RGB', 'RGBA') else None
                duration = max(20, int(source.info.get('duration', 100) or 100))
                oriented = ImageOps.exif_transpose(source)
                xmp = oriented.info.get('xmp', b'')
                comment = source.info.get('comment', b'')
                if isinstance(xmp, str):
                    xmp = xmp.encode('utf-8')
                if isinstance(comment, str):
                    comment = comment.encode('utf-8')
                metadata = {str(ExifTags.TAGS.get(k, k)): str(v)[:1000] for k,v in oriented.getexif().items()}
                metadata.update({'Format': source.format, 'Modus': source.mode, 'Dateigröße': str(path.stat().st_size)})
                exif = oriented.getexif()
                # Geometry and embedded thumbnail pointers are stale after editing.
                for tag in (274, 256, 257, 40962, 40963, 513, 514):
                    if tag in exif:
                        del exif[tag]
                exif_bytes = exif.tobytes() if exif else b''
                image = oriented.convert('RGBA')
                image.load()
        except UnidentifiedImageError:
            from native_codecs import decode
            image, count, metadata = decode(path, frame=frame)
            duration, icc = 100, None
        self.image, self.path, self.source_path = image, path, path
        self.frame_count, self.frame_index = count, frame
        self.multiframe, self.icc = count > 1, icc
        self.exif, self.metadata, self.duration = exif_bytes, metadata, duration
        self.xmp, self.comment = xmp, comment
        self.history.clear()
        self.future.clear()
        self.revision = self.saved_revision = 0
        self.next_revision = 1

    def replace(self, image):
        if 'dpi' not in image.info:
            image.info['dpi'] = (self.dpi,self.dpi)
        self.history.append((self.image, self.revision))
        self.history = self.history[-20:]
        while len(self.history) > 1 and sum(i.width*i.height*4 for i,_ in self.history) > 128*1024*1024:
            self.history.pop(0)
        self.future.clear()
        self.image = image
        self.revision = self.next_revision
        self.next_revision += 1

    def rotate(self, clockwise=True):
        op = Image.Transpose.ROTATE_270 if clockwise else Image.Transpose.ROTATE_90
        self.replace(self.image.transpose(op))

    def crop(self, box):
        if box is None or crop_box(box[:2], box[2:], self.image.size) != box:
            raise ValueError('Ungültiger Bildausschnitt')
        self.replace(self.image.crop(box))

    def undo(self):
        if self.history:
            self.future.append((self.image, self.revision))
            self.image, self.revision = self.history.pop()

    def redo(self):
        if self.future:
            self.history.append((self.image, self.revision))
            self.image, self.revision = self.future.pop()

    def resize(self, width, height, method='lanczos', dpi=None):
        width, height = int(width), int(height)
        if min(width, height) < 1 or width * height > 80_000_000:
            raise ValueError('Größe muss positiv sein und darf 80 Megapixel nicht überschreiten.')
        filters = {'lanczos':Image.Resampling.LANCZOS,'bicubic':Image.Resampling.BICUBIC,
                   'bilinear':Image.Resampling.BILINEAR,'nearest':Image.Resampling.NEAREST}
        if method not in filters:
            raise ValueError('Unbekannte Interpolation')
        result = self.image.resize((width, height), filters[method])
        if dpi is not None:
            if not math.isfinite(dpi) or not 1 <= dpi <= 9600:
                raise ValueError('DPI muss zwischen 1 und 9600 liegen.')
            result.info['dpi'] = (dpi,dpi)
        self.replace(result)

    def effect(self, name, amount=1.0):
        alpha = self.image.getchannel('A')
        rgb = self.image.convert('RGB')
        if name == 'mirror':
            result = ImageOps.mirror(self.image)
        elif name == 'flip':
            result = ImageOps.flip(self.image)
        elif name == 'grayscale':
            result = ImageOps.grayscale(rgb).convert('RGBA')
        elif name == 'invert':
            result = ImageOps.invert(rgb).convert('RGBA')
        elif name == 'autocontrast':
            result = ImageOps.autocontrast(rgb).convert('RGBA')
        elif name == 'blur':
            result = rgb.filter(ImageFilter.GaussianBlur(float(amount))).convert('RGBA')
        elif name in ('brightness', 'contrast', 'color', 'sharpness'):
            enhancer = {'brightness':ImageEnhance.Brightness, 'contrast':ImageEnhance.Contrast,
                        'color':ImageEnhance.Color, 'sharpness':ImageEnhance.Sharpness}[name]
            result = enhancer(rgb).enhance(float(amount)).convert('RGBA')
        else:
            raise ValueError('Unbekannter Effekt')
        if name not in ('mirror','flip'):
            result.putalpha(alpha)
        self.replace(result)

    def add_text(self, text, x=20, y=20, size=32, color='#ffffff'):
        if not text:
            raise ValueError('Bitte Text eingeben.')
        result = self.image.copy()
        font = ImageFont.load_default(size=int(size))
        ImageDraw.Draw(result).text((int(x),int(y)), text, fill=color, font=font, stroke_width=1)
        self.replace(result)

    def watermark(self, path, opacity=.5):
        with Image.open(path) as overlay:
            overlay = ImageOps.exif_transpose(overlay).convert('RGBA')
        overlay.thumbnail((max(1,self.image.width//3), max(1,self.image.height//3)))
        overlay.putalpha(overlay.getchannel('A').point(lambda a:round(a*max(0,min(1,opacity)))))
        result = self.image.copy()
        result.alpha_composite(overlay, (max(0,result.width-overlay.width-12), max(0,result.height-overlay.height-12)))
        self.replace(result)

    def export_document(self, path, overwrite=False):
        """Export source pages plus the current edited page; source stays untouched."""
        path = Path(path).absolute()
        fmt = FORMATS.get(path.suffix.lower())
        if fmt not in ('TIFF','GIF','PDF','WEBP'):
            raise ValueError('Mehrseiten-Export: TIFF, GIF, WebP oder PDF wählen.')
        if self.source_path and path.resolve() == self.source_path.resolve():
            raise ValueError('Für den Mehrseiten-Export einen neuen Dateinamen wählen.')
        frames, durations, pixels = [], [], 0
        for index in range(self.frame_count):
            if index == self.frame_index:
                image, duration = self.image, self.duration
            else:
                model = ImageModel()
                model.load(self.source_path,frame=index)
                image, duration = model.image, model.duration
            pixels += image.width*image.height
            if pixels > 64_000_000:
                raise ValueError('Mehrseiten-Export benötigt zu viel Speicher (max. 64 Millionen Pixel insgesamt).')
            if fmt == 'PDF':
                background = Image.new('RGB',image.size,'white')
                background.paste(image,mask=image.getchannel('A'))
                image = background
            frames.append(image)
            durations.append(duration)
        if fmt in ('GIF','WEBP') and len({frame.size for frame in frames})>1:
            raise ValueError('Für unterschiedliche Seitengrößen bitte TIFF oder PDF wählen.')
        options = {'save_all':True,'append_images':frames[1:]}
        if fmt in ('GIF','WEBP'):
            options.update(duration=durations,loop=0)
        if fmt == 'GIF':
            options['disposal'] = 2
        atomic_write(path,lambda tmp:frames[0].save(tmp,format=fmt,**options),overwrite)

    def save(self, path, overwrite=False, quality=95, metadata=True, settings=None):
        path = Path(path).absolute()
        fmt = FORMATS.get(path.suffix.lower())
        if not fmt:
            raise ValueError('Unterstützte Endungen: ' + ', '.join(FORMATS))
        settings = settings if settings is not None else SaveSettings.legacy(quality, metadata)
        atomic_write(path, lambda tmp:write_image(self, tmp, fmt, settings), overwrite)
        self.path = path
        self.saved_revision = self.revision
