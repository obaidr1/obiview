"""Deterministic, alpha-preserving photo adjustments shared by preview and apply."""
from PIL import Image, ImageEnhance, ImageChops, ImageOps

CONTROLS = {
    'gamma':'Gamma', 'red':'Rot', 'green':'Grün', 'blue':'Blau',
    'brightness': 'Helligkeit', 'contrast': 'Kontrast', 'highlights': 'Lichter',
    'shadows': 'Schatten', 'temperature': 'Temperatur', 'saturation': 'Sättigung',
    'vibrance': 'Dynamik', 'grain': 'Körnung', 'vignette': 'Vignette', 'sharpness': 'Schärfe',
}


def adjusted(image, values, look='Original'):
    alpha = image.getchannel('A')
    rgb = image.convert('RGB')
    if look == 'Film':
        rgb = ImageEnhance.Color(rgb).enhance(.75)
        rgb = ImageEnhance.Contrast(rgb).enhance(1.1)
    elif look == 'Fade':
        rgb = rgb.point(lambda x: round(22 + x * .86))
    elif look == 'Warm':
        rgb = Image.merge('RGB', (rgb.getchannel('R').point(lambda x:min(255,x+9)),
                                  rgb.getchannel('G'), rgb.getchannel('B').point(lambda x:max(0,x-9))))
    for key, enhancer in [('brightness', ImageEnhance.Brightness), ('contrast', ImageEnhance.Contrast),
                          ('saturation', ImageEnhance.Color), ('sharpness', ImageEnhance.Sharpness)]:
        amount = values.get(key, 0)
        if amount:
            rgb = enhancer(rgb).enhance(1 + amount / 100)
    gamma = 2 ** (values.get('gamma',0)/50)
    if gamma != 1:
        rgb = rgb.point(lambda x:round(255*(x/255)**(1/gamma)))
    if any(values.get(k,0) for k in ('red','green','blue')):
        rgb = Image.merge('RGB',tuple(channel.point(lambda x,a=values.get(key,0):round(max(0,min(255,x+a*2.55))))
                                      for channel,key in zip(rgb.split(),('red','green','blue'))))
    lights, shadows = values.get('highlights', 0), values.get('shadows', 0)
    if lights or shadows:
        rgb = rgb.point(lambda x: max(0,min(255,round(x + lights*.65*(x/255)**3 + shadows*.65*(1-x/255)**3))))
    temperature = values.get('temperature', 0) * .45
    if temperature:
        red, green, blue = rgb.split()
        rgb = Image.merge('RGB', (red.point(lambda x:round(max(0,min(255,x+temperature)))), green,
                                 blue.point(lambda x:round(max(0,min(255,x-temperature))))))
    vibrance = values.get('vibrance', 0)
    if vibrance:
        mask = ImageOps.invert(rgb.convert('HSV').getchannel('S'))
        rgb = Image.composite(ImageEnhance.Color(rgb).enhance(1+vibrance/100), rgb, mask)
    grain = values.get('grain', 0)
    if grain:
        # Fixed noise tile: preview and saved image do not change randomly.
        tile = Image.new('L',(64,64))
        tile.putdata([100 + ((i*1103515245 + 12345) >> 16) % 57 for i in range(4096)])
        noise = Image.new('L',rgb.size)
        for y in range(0,rgb.height,64):
            for x in range(0,rgb.width,64):
                noise.paste(tile,(x,y))
        rgb = Image.blend(rgb, ImageChops.add(rgb,noise.convert('RGB'),offset=-128),grain/100)
    vignette = values.get('vignette',0)
    if vignette:
        mask = Image.new('L',(128,128))
        mask.putdata([round(255*(1-vignette/100*.75*min(1,((x-63.5)/90)**2+((y-63.5)/90)**2)))
                      for y in range(128) for x in range(128)])
        rgb = ImageChops.multiply(rgb,mask.resize(rgb.size,Image.Resampling.BILINEAR).convert('RGB'))
    rgb.putalpha(alpha)
    return rgb
