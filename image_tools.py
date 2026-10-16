"""Pixel tools, selection geometry and physical print sizing without GTK."""
import math
import random
import subprocess
from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

EFFECTS = {'button':'3D-Schaltfläche', 'blur':'Weichzeichnen', 'emboss':'Relief',
           'oil':'Ölgemälde', 'edges':'Kantenerkennung', 'median':'Medianfilter',
           'explosion':'Explosion', 'pixelize':'Pixelieren', 'sepia':'Sepia', 'raindrops':'Regentropfen'}

# Only expose ranges that actually affect the corresponding pixel operation.
EFFECT_PARAMETERS = {
    'button': ('Randbreite', 1, 15, 'px'),
    'blur': ('Weichzeichnungsradius', 1, 100, 'px'),
    'oil': ('Pinselradius', 1, 5, 'px'),
    'median': ('Filterradius', 1, 5, 'px'),
    'explosion': ('Streuung', 4, 100, 'px'),
    'pixelize': ('Pixelgröße', 2, 100, 'px'),
    'raindrops': ('Tropfenpaare', 1, 100, ''),
}


def mixed_effect(image, name, amount=5, strength=100):
    """Blend an effect with its unchanged source, preserving alpha and dimensions."""
    if not math.isfinite(strength) or not 0 <= strength <= 100:
        raise ValueError('Die Intensität muss zwischen 0 und 100 Prozent liegen.')
    if name not in EFFECTS or not 1 <= amount <= 100:
        raise ValueError('Effekt oder Stärke ungültig (1–100).')
    if strength == 0:
        return image.copy()
    result = effect(image, name, amount)
    return result if strength == 100 else Image.blend(image, result, strength/100)


def checked_size(width, height):
    width, height = round(width), round(height)
    if min(width, height) < 1 or width * height > 80_000_000:
        raise ValueError('Die Größe muss positiv sein und darf 80 Megapixel nicht überschreiten.')
    return width, height


def to_pixels(value, unit='px', dpi=96):
    if not math.isfinite(float(value)) or not 1 <= dpi <= 9600:
        raise ValueError('Ungültige Abmessung oder DPI (1–9600).')
    factors = {'px':1, 'cm':dpi/2.54, 'inch':dpi}
    if unit not in factors:
        raise ValueError('Unbekannte Einheit')
    return max(1, round(float(value)*factors[unit])) if value > 0 else 0


def fine_rotate(image, angle, color='#ffffff', expand=True):
    if not math.isfinite(angle) or not -360 <= angle <= 360:
        raise ValueError('Winkel zwischen −360° und 360° eingeben.')
    # Positive UI angles turn clockwise.
    radians = math.radians(angle)
    if expand:
        checked_size(math.ceil(abs(image.width*math.cos(radians))+abs(image.height*math.sin(radians)))+2,
                     math.ceil(abs(image.height*math.cos(radians))+abs(image.width*math.sin(radians)))+2)
    return image.rotate(-angle, Image.Resampling.BICUBIC, expand=expand,
                        fillcolor=ImageColor.getcolor(color, 'RGBA'))


def red_eye(image, box, strength=100):
    if not box or not (0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height):
        raise ValueError('Zuerst den roten Augenbereich auswählen.')
    result = image.copy()
    region = image.crop(box)
    red, green, blue, alpha = region.split()
    neutral = ImageChops.add(green, blue, scale=2)
    # Only red-dominant, sufficiently bright pixels inside the explicit selection.
    threshold = ImageChops.lighter(green, blue).point(lambda v:min(255, int(v*1.5)+20))
    mask = ImageChops.subtract(red, threshold).point(lambda v:round(strength*2.55) if v else 0)
    region = Image.merge('RGBA',(Image.composite(neutral,red,mask),green,blue,alpha))
    result.paste(region,box[:2])
    return result


def frame(image, width=20, color='#ffffff', style='plain', inner_width=2, inner_color='#242424'):
    width, inner_width = int(width), int(inner_width)
    if width < 0 or inner_width < 0 or style not in ('plain','double','bevel'):
        raise ValueError('Ungültiger Rahmen.')
    total = width + (inner_width if style == 'double' else 0)
    checked_size(image.width+2*total,image.height+2*total)
    ImageColor.getcolor(color,'RGBA')
    ImageColor.getcolor(inner_color,'RGBA')
    result = ImageOps.expand(image,inner_width,inner_color) if style == 'double' else image.copy()
    result = ImageOps.expand(result,width,color)
    if style == 'bevel' and width:
        draw = ImageDraw.Draw(result)
        w,h = result.size
        rgb = ImageColor.getrgb(color)[:3]
        light = tuple(round(v+(255-v)*.5) for v in rgb)
        dark = tuple(round(v*.5) for v in rgb)
        draw.polygon([(0,0),(w,0),(w-width,width),(width,width),(width,h-width),(0,h)],fill=light)
        draw.polygon([(w,0),(w,h),(0,h),(width,h-width),(w-width,h-width),(w-width,width)],fill=dark)
        result.paste(image,(width,width))
    return result


def effect(image, name, amount=5):
    if name not in EFFECTS or not 1 <= amount <= 100:
        raise ValueError('Effekt oder Stärke ungültig (1–100).')
    rgb, alpha = image.convert('RGB'), image.getchannel('A')
    radius = min(15,max(1,round(amount)))
    if name == 'blur':
        result = rgb.filter(ImageFilter.GaussianBlur(amount))
    elif name == 'emboss':
        result = rgb.filter(ImageFilter.EMBOSS)
    elif name == 'edges':
        result = rgb.filter(ImageFilter.FIND_EDGES)
    elif name == 'median':
        result = rgb.filter(ImageFilter.MedianFilter(2*min(5,radius)+1))
    elif name == 'oil':
        result = ImageOps.posterize(rgb,4).filter(ImageFilter.ModeFilter(2*min(5,radius)+1))
    elif name == 'pixelize':
        block = max(2,round(amount))
        result = rgb.resize((max(1,image.width//block),max(1,image.height//block)),Image.Resampling.BOX).resize(image.size,Image.Resampling.NEAREST)
    elif name == 'sepia':
        result = ImageOps.colorize(ImageOps.grayscale(rgb),'#241709','#ffe3ad')
    elif name == 'button':
        result = rgb.copy()
        draw = ImageDraw.Draw(result)
        for i in range(min(radius,image.width//2,image.height//2)):
            draw.line([(i,image.height-i-1),(i,i),(image.width-i-1,i)], fill='#dddddd')
            draw.line([(i,image.height-i-1),(image.width-i-1,image.height-i-1),(image.width-i-1,i)],fill='#444444')
    elif name == 'explosion':
        rng = random.Random(17)
        block = max(4,round(amount),math.ceil(math.sqrt(image.width*image.height/100000)))
        mesh = []
        for y in range(0,image.height,block):
            for x in range(0,image.width,block):
                w,h = min(block,image.width-x),min(block,image.height-y)
                sx = max(0,min(image.width-w,x+rng.randint(-block,block)))
                sy = max(0,min(image.height-h,y+rng.randint(-block,block)))
                mesh.append(((x,y,x+w,y+h),(sx,sy,sx,sy+h,sx+w,sy+h,sx+w,sy)))
        result = rgb.transform(image.size,Image.Transform.MESH,mesh,Image.Resampling.BILINEAR)
    else:  # Deterministic magnifying droplets with highlights, retaining full canvas.
        result = rgb.copy()
        rng = random.Random(29)
        radius = max(3,round(min(image.size)*.035))
        for _ in range(round(amount)*2):
            x,y = rng.randrange(image.width),rng.randrange(image.height)
            box = (max(0,x-radius),max(0,y-radius),min(image.width,x+radius),min(image.height,y+radius))
            w,h = box[2]-box[0],box[3]-box[1]
            inset = (max(0,x-radius//2),max(0,y-radius//2),min(image.width,x+max(1,radius//2)),min(image.height,y+max(1,radius//2)))
            drop = rgb.crop(inset).resize((w,h),Image.Resampling.BICUBIC)
            mask = Image.new('L',(w,h)); ImageDraw.Draw(mask).ellipse((0,0,w-1,h-1),fill=220)
            result.paste(drop,box[:2],mask)
            ImageDraw.Draw(result).arc((box[0],box[1],box[2]-1,box[3]-1),195,270,fill='white',width=1)
    result.putalpha(alpha)
    return result


def text_image(image, text, box, font='Sans', size=48, color='#ffffff', bold=False, italic=False):
    if not text.strip():
        raise ValueError('Bitte Text eingeben.')
    ImageColor.getcolor(color,'RGBA')
    style = ('Bold ' if bold else '') + ('Italic' if italic else '')
    match = subprocess.run(['fc-match','-f','%{file}',f'{font}:style={style.strip() or "Regular"}'],
                           capture_output=True,text=True,check=True,timeout=5).stdout.strip()
    font_object = ImageFont.truetype(match,round(size))
    x1,y1,x2,y2 = box
    layer = Image.new('RGBA',(x2-x1,y2-y1))
    draw = ImageDraw.Draw(layer)
    lines = []
    for paragraph in text.splitlines():
        line = ''
        for char in paragraph:
            if line and draw.textlength(line+char,font=font_object) > layer.width:
                lines.append(line); line = ''
            line += char
        lines.append(line)
    draw.multiline_text((0,0),'\n'.join(lines),font=font_object,fill=color,spacing=4)
    result = image.copy()
    result.alpha_composite(layer,(x1,y1))
    return result


def selection_drag(box, start, end, size, mode='new'):
    from image_model import crop_box
    if mode == 'new' or box is None:
        return crop_box(start,end,size)
    dx,dy = round(end[0]-start[0]),round(end[1]-start[1])
    x1,y1,x2,y2 = box
    if mode == 'move':
        dx = max(-x1,min(size[0]-x2,dx)); dy = max(-y1,min(size[1]-y2,dy))
        return x1+dx,y1+dy,x2+dx,y2+dy
    if 'w' in mode: x1 += dx
    if 'e' in mode: x2 += dx
    if 'n' in mode: y1 += dy
    if 's' in mode: y2 += dy
    return crop_box((x1,y1),(x2,y2),size)


def print_layout(size, page, mode='fit', width_cm=10, height_cm=10, locked=True,
                 scale_x=100, scale_y=100, dpi=96, x_cm=0, y_cm=0, centered=True):
    pw,ph = page
    if mode == 'fit':
        factor = min(pw/size[0],ph/size[1]); w,h = size[0]*factor,size[1]*factor
    elif mode == 'custom':
        w,h = width_cm*72/2.54,height_cm*72/2.54
        if locked: h = w*size[1]/size[0]
    elif mode == 'scale':
        xdpi,ydpi = dpi if isinstance(dpi,(tuple,list)) else (dpi,dpi)
        if not all(math.isfinite(v) and v>0 for v in (xdpi,ydpi)):
            raise ValueError('Ungültige Druckauflösung')
        w,h = size[0]*72/xdpi*scale_x/100,size[1]*72/ydpi*scale_y/100
    else:
        raise ValueError('Unbekannter Druckmodus')
    if min(w,h) <= 0 or not all(math.isfinite(n) for n in (w,h,pw,ph,x_cm,y_cm)):
        raise ValueError('Ungültige Druckgröße')
    return ((pw-w)/2 if centered else x_cm*72/2.54,
            (ph-h)/2 if centered else y_cm*72/2.54,w,h)


def panorama(images, vertical=False, gap=0, color='#ffffff'):
    if len(images)<2:
        raise ValueError('Mindestens zwei Bilder auswählen.')
    gap = int(gap)
    if gap < 0: raise ValueError('Abstand muss positiv sein.')
    w = max(i.width for i in images) if vertical else sum(i.width for i in images)+gap*(len(images)-1)
    h = sum(i.height for i in images)+gap*(len(images)-1) if vertical else max(i.height for i in images)
    result = Image.new('RGBA',checked_size(w,h),color)
    pos = 0
    for image in images:
        result.alpha_composite(image,((w-image.width)//2,pos) if vertical else (pos,(h-image.height)//2))
        pos += (image.height if vertical else image.width)+gap
    return result


def add_canvas(image, left=0, top=0, right=0, bottom=0, color='#ffffff'):
    borders = tuple(int(v) for v in (left,top,right,bottom))
    target = checked_size(image.width+borders[0]+borders[2],image.height+borders[1]+borders[3])
    result = Image.new('RGBA',target,ImageColor.getcolor(color,'RGBA'))
    result.paste(image,(borders[0],borders[1]))
    return result


def erase_selection(image, box, outside=False, color='#ffffff'):
    if box is None:
        raise ValueError('Zuerst einen Bereich auswählen.')
    fill = ImageColor.getcolor(color,'RGBA')
    if outside:
        result = Image.new('RGBA',image.size,fill)
        result.paste(image.crop(box),box[:2])
    else:
        result = image.copy()
        result.paste(fill,box)
    return result


def auto_crop(image, tolerance=0):
    if not 0<=tolerance<=255: raise ValueError('Toleranz muss zwischen 0 und 255 liegen.')
    # Transparent edges or a uniform corner-colored surround.
    if image.getchannel('A').getextrema()[0]==0:
        box = image.getchannel('A').point(lambda p:255 if p>tolerance else 0).getbbox()
    else:
        rgb=image.convert('RGB')
        delta=ImageChops.difference(rgb,Image.new('RGB',image.size,rgb.getpixel((0,0))))
        channels=delta.split()
        mask=ImageChops.lighter(channels[0],ImageChops.lighter(channels[1],channels[2]))
        box=mask.point(lambda p:255 if p>tolerance else 0).getbbox()
    if not box: raise ValueError('Kein vom Rand unterscheidbarer Bildinhalt gefunden.')
    return image.crop(box)


def reduce_colors(image, colors=256, dither=True):
    if not 2<=colors<=256: raise ValueError('Zwischen 2 und 256 Farben wählen.')
    rgb=image.convert('RGB')
    palette=rgb.quantize(colors=int(colors),method=Image.Quantize.MEDIANCUT)
    result=rgb.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE).convert('RGBA')
    result.putalpha(image.getchannel('A'))
    return result


def swap_channels(image, order='BGR'):
    if order not in ('RGB','RBG','GRB','GBR','BRG','BGR'):
        raise ValueError('Ungültige Kanalreihenfolge.')
    return Image.merge('RGBA',tuple(image.getchannel(c) for c in order)+ (image.getchannel('A'),))
