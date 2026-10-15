"""Optional native Linux decoders with resource-limited subprocesses.

extra_extensions() returns installed, allowlisted decoder extensions.
decode(path, frame=0) returns (detached RGBA Pillow image, page/frame count,
metadata). PDF pages and ImageMagick scenes use zero-based frame numbers.
This rasterizes vector/HDR/RAW input to 8-bit RGBA; original layered, HDR and
camera metadata are not preserved. Advertised coders are not a promise that
every variant of a format can be read. No network/delegate tools are enabled
for ImageMagick. PDF uses Poppler; AVIF uses FFmpeg with genuine frame counts.
AVIF alpha/auxiliary-image layouts are rejected rather than flattened.
"""
from functools import lru_cache
import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from PIL import Image

MAX_PIXELS = 40_000_000
MAX_INPUT = 512 * 1024 * 1024
MAX_OUTPUT = 192 * 1024 * 1024
MAX_FRAMES = 10_000
TIMEOUT = 30
# Explicit names prevent ImageMagick from interpreting extensions as commands.
_CODERS = {
    '.svg': 'RSVG', '.svgz': 'RSVG', '.jxl': 'JXL', '.exr': 'EXR',
    '.dpx': 'DPX', '.cin': 'CIN', '.dcm': 'DCM', '.dicom': 'DCM',
    '.mng': 'MNG', '.jng': 'JNG', '.xcf': 'XCF', '.wpg': 'WPG',
    '.wbmp': 'WBMP', '.sfw': 'SFW', '.rle': 'RLE', '.hdr': 'HDR',
    '.avif': 'AVIF', '.heic': 'HEIC', '.heif': 'HEIC',
    **{'.' + x.lower(): x for x in (
        'ARW', 'CR2', 'CR3', 'CRW', 'DCR', 'DNG', 'ERF', 'KDC', 'MRW',
        'NEF', 'NRW', 'ORF', 'PEF', 'RAF', 'RW2', 'RWL', 'SRF', 'SRW',
        'MOS', '3FR', 'IIQ', 'X3F')},
}
_POLICY = '''<policymap>
<policy domain="delegate" rights="none" pattern="*"/>
<policy domain="filter" rights="none" pattern="*"/>
<policy domain="coder" rights="none" pattern="{HTTP,HTTPS,URL,FTP,MVG,MSL,EPHEMERAL}"/>
<policy domain="path" rights="none" pattern="@*"/>
<policy domain="resource" name="memory" value="256MiB"/>
<policy domain="resource" name="map" value="512MiB"/>
<policy domain="resource" name="disk" value="512MiB"/>
<policy domain="resource" name="thread" value="2"/>
<policy domain="resource" name="time" value="25"/>
</policymap>'''


def _run(args, cwd=None, env=None):
    """Bound time, address space and output file size without preexec_fn."""
    limiter = shutil.which('prlimit')
    if not limiter:
        raise RuntimeError('Der sichere Decoder benötigt prlimit (util-linux).')
    command = [limiter, '--as=2147483648', f'--fsize={MAX_OUTPUT}',
               '--cpu=25', '--', *args]
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        try:
            result = subprocess.run(command, stdout=output, stderr=errors,
                                    stdin=subprocess.DEVNULL, timeout=TIMEOUT,
                                    cwd=cwd, env=env, check=False)
        except subprocess.TimeoutExpired as exc:
            raise ValueError('Bilddekodierung überschreitet das Zeitlimit.') from exc
        if result.returncode:
            errors.seek(0)
            detail = errors.read(2000).decode('utf-8', 'replace').strip()
            raise ValueError('Nativer Decoder konnte die Datei nicht lesen: ' + detail)
        size = output.tell()
        if size > MAX_OUTPUT:
            raise ValueError('Decoder-Ausgabe ist zu groß.')
        output.seek(0)
        return output.read()


@lru_cache(maxsize=1)
def _installed_coders():
    magick = shutil.which('magick')
    if not magick or not shutil.which('prlimit'):
        return frozenset()
    try:
        listing = _run([magick, '-list', 'format']).decode('utf-8', 'replace')
    except (OSError, ValueError, RuntimeError):
        return frozenset()
    return frozenset(m.group(1) for m in re.finditer(
        r'^\s*(\w+)\*?\s+\w+\s+r[-w][+-]\s', listing, re.MULTILINE))


@lru_cache(maxsize=1)
def _ffmpeg_avif_available():
    if not all(shutil.which(name) for name in ('ffmpeg', 'ffprobe', 'prlimit')):
        return False
    try:
        decoders = _run([shutil.which('ffmpeg'), '-hide_banner', '-decoders']).decode()
        demuxers = _run([shutil.which('ffprobe'), '-hide_banner', '-demuxers']).decode()
        return bool(re.search(r'^ V..... (?:libdav1d|libaom-av1|av1)\s', decoders, re.MULTILINE)
                    and re.search(r'^ D\s+mov,', demuxers, re.MULTILINE))
    except (OSError, ValueError, RuntimeError):
        return False


def _decode_avif(source, frame, folder, env):
    # AVIF requires an ISO BMFF ftyp brand, not merely a renamed video file.
    with source.open('rb') as stream:
        header = stream.read(4096)
    boxsize = int.from_bytes(header[:4], 'big')
    brands = [header[8:12]] + [header[i:i+4] for i in range(16, min(boxsize, len(header)), 4)]
    if header[4:8] != b'ftyp' or not 16 <= boxsize <= len(header) or not {b'avif', b'avis'}.intersection(brands):
        raise ValueError('Datei enthält keinen unterstützten AVIF-Dateikopf.')
    common = [shutil.which('ffprobe'), '-v', 'error', '-threads', '1',
              '-protocol_whitelist', 'file', '-f', 'mov']
    def probe(count=False):
        args = common + (['-count_frames'] if count else [])
        data = json.loads(_run(args + ['-show_streams', '-of', 'json', str(source)], folder, env))
        streams = [item for item in data.get('streams', []) if item.get('codec_type') == 'video']
        if not streams or any(item.get('codec_name') != 'av1' for item in streams):
            raise ValueError('AVIF enthält keinen unterstützten AV1-Bildstrom.')
        # Current FFmpeg lists an animation's primary still and timed sequence
        # with the same image ID. Distinct IDs/alpha auxiliaries require proper
        # compositing; refuse them instead of silently dropping transparency.
        ids = {item.get('id') for item in streams}
        if len(ids) != 1 or any(item.get('tags', {}).get('title', '').lower() == 'alpha' for item in streams):
            raise ValueError('AVIF mit Hilfsbildern/Alphakanal wird von diesem Decoder noch nicht unterstützt.')
        for item in streams:
            width, height = int(item.get('width', 0)), int(item.get('height', 0))
            if min(width, height) <= 0 or width * height > MAX_PIXELS:
                raise ValueError('AVIF überschreitet die Grenze von 40 Millionen Pixeln.')
        return streams
    probe()  # Bound dimensions before decoding every frame to obtain true counts.
    streams = probe(count=True)
    try:
        chosen = max(streams, key=lambda item: int(item['nb_read_frames']))
        count = int(chosen['nb_read_frames'])
    except (KeyError, ValueError) as error:
        raise ValueError('Die tatsächliche AVIF-Bildzahl konnte nicht ermittelt werden.') from error
    if not 0 <= frame < count <= MAX_FRAMES:
        raise ValueError('Bild außerhalb der AVIF-Datei oder zu viele Einzelbilder.')
    output = _run([shutil.which('ffmpeg'), '-v', 'error', '-nostdin',
                   '-threads', '1', '-filter_threads', '1', '-protocol_whitelist', 'file',
                   '-f', 'mov', '-i', str(source), '-map', '0:' + str(chosen['index']),
                   '-vf', f'select=eq(n\\,{frame})', '-frames:v', '1', '-an', '-sn',
                   '-c:v', 'png', '-threads', '1', '-pix_fmt', 'rgba',
                   '-f', 'image2pipe', 'pipe:1'], folder, env)
    return output, count


def extra_extensions():
    """Only extensions with an installed decoder; no install/network actions."""
    if not shutil.which('prlimit'):
        return set()
    found = {ext for ext, coder in _CODERS.items() if coder in _installed_coders()}
    if _ffmpeg_avif_available():
        found.add('.avif')
    if shutil.which('pdfinfo') and shutil.which('pdftoppm'):
        found.add('.pdf')
    return found


def decode(path, frame=0):
    """Read one page/scene, keeping the actual total count in the return value."""
    if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0:
        raise ValueError('Ungültige Seitennummer.')
    source = Path(path).expanduser().resolve(strict=True)
    ext = source.suffix.lower()
    if ext not in extra_extensions():
        raise ValueError('Kein installierter nativer Decoder für dieses Format.')
    if not source.is_file() or source.stat().st_size > MAX_INPUT:
        raise ValueError('Datei ist keine reguläre Datei oder überschreitet 512 MiB.')
    with tempfile.TemporaryDirectory(prefix='bildblick-codec-') as folder:
        # A fixed basename prevents scene syntax, pseudo-protocols and option
        # interpretation in filenames, and makes relative SVG assets unavailable.
        safe = Path(folder) / ('input' + ext)
        shutil.copyfile(source, safe)
        policy = Path(folder) / 'policy.xml'
        policy.write_text(_POLICY, encoding='utf-8')
        env = dict(os.environ, MAGICK_CONFIGURE_PATH=folder,
                   MAGICK_TEMPORARY_PATH=folder, LC_ALL='C')
        if ext == '.avif' and _ffmpeg_avif_available():
            output, count = _decode_avif(safe, frame, folder, env)
            codec = 'FFmpeg/AV1'
        elif ext == '.pdf':
            info = _run([shutil.which('pdfinfo'), str(safe)], folder, env).decode('utf-8', 'replace')
            count_match = re.search(r'^Pages:\s+(\d+)$', info, re.MULTILINE)
            if not count_match:
                raise ValueError('Die tatsächliche PDF-Seitenzahl konnte nicht ermittelt werden.')
            count = int(count_match.group(1))
            if not 0 <= frame < count <= MAX_FRAMES:
                raise ValueError('Seite außerhalb des Dokuments oder zu viele Seiten.')
            # Query the selected page because PDF pages can have different sizes.
            pageinfo = _run([shutil.which('pdfinfo'), '-f', str(frame + 1), '-l',
                             str(frame + 1), str(safe)], folder, env).decode('utf-8', 'replace')
            dims = re.search(r'(?:Page\s+\d+ size|Page size):\s+([\d.]+) x ([\d.]+) pts', pageinfo)
            if not dims or float(dims.group(1)) * float(dims.group(2)) * (150 / 72) ** 2 > MAX_PIXELS:
                raise ValueError('PDF-Seite ist zu groß oder ihre Abmessungen sind unbekannt.')
            output = _run([shutil.which('pdftoppm'), '-f', str(frame + 1), '-l',
                           str(frame + 1), '-singlefile', '-r', '150', '-png',
                           str(safe)], folder, env)
            codec = 'Poppler'
        else:
            magick = shutil.which('magick')
            coder = _CODERS[ext]
            input_arg = coder + ':' + str(safe)
            info = _run([magick, 'identify', '-ping', '-format', '%w %h\n', input_arg], folder, env)
            dimensions = [tuple(map(int, line.split())) for line in info.decode('ascii').splitlines()]
            count = len(dimensions)
            if not 0 <= frame < count <= MAX_FRAMES:
                raise ValueError('Bild außerhalb der Datei oder zu viele Einzelbilder.')
            if any(len(d) != 2 or d[0] <= 0 or d[1] <= 0 or d[0] * d[1] > MAX_PIXELS for d in dimensions):
                raise ValueError('Bild überschreitet die Grenze von 40 Millionen Pixeln.')
            output = _run([magick, input_arg + f'[{frame}]', '-auto-orient',
                           '-colorspace', 'sRGB', '-depth', '8', 'PNG32:-'], folder, env)
            codec = 'ImageMagick/' + coder
        import io
        with Image.open(io.BytesIO(output)) as image:
            if image.format != 'PNG' or image.width * image.height > MAX_PIXELS:
                raise ValueError('Ungültige oder zu große Ausgabe des Decoders.')
            rgba = image.convert('RGBA')
            rgba.load()
        return rgba, count, {'decoder': codec, 'source_format': ext[1:].upper(),
                             'rasterized': True, 'frame': frame}
