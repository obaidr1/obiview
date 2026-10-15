"""Encode single-frame exports without changing the editing canvas."""
import io
from pathlib import Path
from PIL import Image


def flattened(image):
    background = Image.new('RGB', image.size, 'white')
    background.paste(image, mask=image.getchannel('A'))
    return background


def write_image(model, filename, fmt, settings):
    image = model.image
    if settings.output_width:
        image = image.resize((settings.output_width,settings.output_height),Image.Resampling.LANCZOS)
    rgba = image
    opts = {}
    if fmt in ('JPEG','PNG','TIFF','BMP','PDF'):
        opts['dpi'] = (model.dpi,model.dpi)
    if fmt in ('JPEG', 'BMP', 'PDF', 'PPM'):
        image = flattened(image)
    else:
        image = image.copy()
    # Pillow sometimes inherits metadata from image.info, even without save kwargs.
    image.info.clear()
    if settings.keep_icc and model.icc and fmt in ('JPEG', 'PNG', 'WEBP', 'TIFF', 'PDF'):
        opts['icc_profile'] = model.icc
    if settings.keep_exif and model.exif and fmt in ('JPEG', 'PNG', 'WEBP'):
        exif = Image.Exif(); exif.load(model.exif)
        exif[282] = model.dpi; exif[283] = model.dpi; exif[296] = 2
        opts['exif'] = exif.tobytes()
    if settings.keep_xmp and model.xmp and fmt in ('JPEG', 'WEBP'):
        opts['xmp'] = model.xmp
    if settings.keep_comment and model.comment and fmt in ('JPEG', 'GIF'):
        opts['comment'] = model.comment
    if fmt in ('JPEG', 'WEBP'):
        opts['quality'] = settings.quality
    if fmt == 'JPEG':
        opts.update(progressive=settings.progressive, subsampling=0 if settings.chroma444 else 2)
        if settings.grayscale:
            image = image.convert('L')
            # The original profile describes RGB, not the new grayscale pixels.
            opts.pop('icc_profile', None)
    elif fmt == 'PNG':
        opts['compress_level'] = settings.png_compression
    elif fmt == 'WEBP':
        opts['lossless'] = settings.webp_lossless
    elif fmt == 'GIF':
        opts['interlace'] = settings.gif_interlace
        # Reserve palette index 255 for binary transparency; flatten partial alpha
        # over white because GIF cannot represent partially transparent pixels.
        alpha = rgba.getchannel('A')
        image = flattened(rgba).quantize(colors=255 if settings.gif_transparency else 256)
        if settings.gif_transparency and alpha.getextrema()[0] < 128:
            image.paste(255, mask=alpha.point(lambda a: 255 if a < 128 else 0))
            opts.update(transparency=255, optimize=False)
    if fmt == 'JPEG' and settings.target_kib:
        limit = settings.target_kib * 1024
        def encoded(quality):
            buffer = io.BytesIO()
            image.save(buffer, format=fmt, **dict(opts, quality=quality))
            return buffer.getvalue()
        data = encoded(settings.quality)
        if len(data) > limit:
            best = encoded(1)
            if len(best) > limit:
                raise ValueError('Die JPEG-Zielgröße ist selbst bei Qualität 1 nicht erreichbar. '
                                 'Größeres Limit wählen, Metadaten abwählen oder das Bild verkleinern.')
            low, high = 2, settings.quality - 1
            while low <= high:
                quality = (low + high) // 2
                candidate = encoded(quality)
                if len(candidate) <= limit:
                    best, low = candidate, quality + 1
                else:
                    high = quality - 1
            data = best
        Path(filename).write_bytes(data)
    else:
        image.save(filename, format=fmt, **opts)
