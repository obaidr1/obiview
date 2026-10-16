"""Source facts and bounded-memory information calculations without GTK."""
import math
import struct
from datetime import datetime
from pathlib import Path
from PIL import ExifTags, IptcImagePlugin


def dpi_pair(image):
    raw = image.info.get('dpi', (96,96))
    try:
        values = tuple(float(v) for v in raw)
        if len(values)==2 and all(math.isfinite(v) and 1<=v<=9600 for v in values): return values
    except (ValueError,TypeError): pass
    return 96.,96.


def metadata_text(value):
    if isinstance(value,bytes):
        if value.startswith(b'ASCII\0\0\0'): value=value[8:]
        try: value=value.decode('utf-8')
        except UnicodeDecodeError: value=value.decode('latin-1')
    elif isinstance(value,(list,tuple)):
        value='; '.join(metadata_text(v) for v in value)
    else: value=str(value)
    return value if len(value)<=8192 else value[:8192]+' … [Anzeige gekürzt]'


def source_details(source,path):
    mode=source.mode
    bits={'1':1,'L':8,'P':8,'LA':16,'RGB':24,'RGBA':32,'CMYK':32,
          'I':32,'F':32,'I;16':16,'I;16B':16,'I;16L':16}.get(mode)
    try:
        with Path(path).open('rb') as stream: header=stream.read(32)
        if header.startswith(b'\x89PNG\r\n\x1a\n') and len(header)>=26:
            bits=header[24]*{0:1,2:3,3:1,4:2,6:4}[header[25]]
        elif header.startswith(b'BM') and len(header)>=30: bits=int.from_bytes(header[28:30],'little')
        elif source.format=='TIFF':
            samples=source.tag_v2.get(258)
            if samples: bits=sum(samples) if isinstance(samples,tuple) else int(samples)
    except (OSError,KeyError,TypeError,ValueError): pass
    exif_values={}
    try:
        exif=source.getexif()
        for key,value in exif.items():
            exif_values[str(ExifTags.TAGS.get(key,key))]=metadata_text(value)
        for number,prefix,tags in ((34665,'Exif',ExifTags.TAGS),(34853,'GPS',ExifTags.GPSTAGS),(40965,'Interop',ExifTags.TAGS)):
            try:
                for key,value in exif.get_ifd(number).items():
                    exif_values[f'{prefix}.{tags.get(key,key)}']=metadata_text(value)
            except (KeyError,TypeError,ValueError,OSError): pass
    except (ValueError,OSError,SyntaxError): pass
    try: iptc=IptcImagePlugin.getiptcinfo(source) or {}
    except (ValueError,OSError,SyntaxError,TypeError): iptc={}
    return {'size':source.size,'mode':mode,'bits':bits,'format':source.format,
            'exif':exif_values,'iptc':iptc,'rasterized':False}


def dimensions(size):
    w,h=size; divisor=math.gcd(w,h)
    return f'{w} × {h} Pixel · {w*h/1_000_000:.2f} MP · {w//divisor}:{h//divisor}'


def bytes_text(count):
    return f'{count/1024/1024:.2f} MiB ({count:,} Bytes)'.replace(',',' ')


def color_description(mode,bits):
    if not mode or not bits: return 'Nicht verfügbar'
    if mode=='P': text=f'Bis zu {2**bits:,} Palettenfarben'
    elif mode in ('1','L','LA') or mode.startswith('I;16'): text=f'{2**(bits//2 if mode=="LA" else bits):,} Graustufen'
    elif mode in ('RGB','RGBA'):
        channels=4 if mode=='RGBA' else 3
        color_bits=bits*3//channels
        if mode=='RGB' and bits==32: color_bits=24  # RGBX storage padding
        text=f'{2**color_bits:,} mögliche RGB-Farben'
        if mode=='RGBA': text+=' + Alpha'
    else: text=mode
    return f'{text.replace(","," ")} · {bits} Bit/Pixel ({mode})'


def info_values(model,folder_files=()):
    image=model.image; original=model.source_info
    path=model.path; exists=bool(path and path.is_file())
    xdpi,ydpi=dpi_pair(image)
    cm=image.width/xdpi*2.54,image.height/ydpi*2.54
    values={
        'filename':path.name if path else 'Unbenannt',
        'directory':str(path.parent) if path else 'Noch nicht gespeichert',
        'path':str(path) if path else 'Noch nicht gespeichert',
        'format':original.get('format') or 'Arbeitsbild (RGBA)',
        'original_size':dimensions(original['size']) if original.get('size') else 'Keine Quelldatei',
        'current_size':dimensions(image.size),
        'print_size':f'{cm[0]:.2f} × {cm[1]:.2f} cm · {image.width/xdpi:.2f} × {image.height/ydpi:.2f} Zoll',
        'original_colors':color_description(original.get('mode'),original.get('bits')),
        'current_colors':color_description('RGBA',32),
        'disk':'Noch nicht gespeichert',
        'memory':bytes_text(image.width*image.height*len(image.getbands()))+' · aktuelle Bildpixel',
        'index':f'{folder_files.index(model.source_path)+1} / {len(folder_files)}' if model.source_path in folder_files else 'Nicht in einer Ordnerliste',
        'modified':'Nicht verfügbar',
        'load_time':f'{model.load_ms:.1f} Millisekunden' if model.load_ms is not None else 'Nicht aus Datei geladen',
        'page':f'{model.frame_index+1} / {model.frame_count}',
    }
    if original.get('rasterized'): values['original_size']+=' (gerastert)'
    if exists:
        try:
            stat=path.stat(); values['disk']=bytes_text(stat.st_size)
            values['modified']=datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y · %H:%M:%S')
            if path!=model.source_path:
                from save_options import ALIASES
                values['format']=ALIASES.get(path.suffix.lower(),values['format'])
        except OSError: values['disk']='Datei nicht mehr verfügbar'
    return values


def count_rgb_colors(image,cancel=None):
    """Exact RGB colors (alpha excluded), using a 2 MiB bitset and small tiles."""
    seen=bytearray(1<<21); count=0
    for y in range(0,image.height,32):
        if cancel and cancel.is_set(): return None
        data=image.crop((0,y,image.width,min(y+32,image.height))).convert('RGB').tobytes()
        for r,g,b in struct.iter_unpack('BBB',data):
            value=(r<<16)|(g<<8)|b; index=value>>3; bit=1<<(value&7)
            if not seen[index]&bit:
                seen[index]|=bit; count+=1
    return count
