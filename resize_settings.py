"""Resize dimensions, independent of widgets and display servers."""
import math


class ResizeSettings:
    def __init__(self,width,height):
        if min(width,height)<1:
            raise ValueError('Bildgröße muss positiv sein.')
        self.original = (int(width),int(height))
        self.width,self.height = self.original
        self.locked = True
        self.last_axis = 'width'

    def set_dimension(self,axis,value,percent=False):
        if axis not in ('width','height') or not math.isfinite(value) or value<=0:
            raise ValueError('Bitte eine positive Größe eingeben.')
        index = 0 if axis=='width' else 1
        pixels = max(1,round(value*self.original[index]/100)) if percent else max(1,round(value))
        setattr(self,axis,pixels)
        self.last_axis = axis
        if self.locked:
            other = 'height' if axis=='width' else 'width'
            setattr(self,other,max(1,round(pixels*self.original[1-index]/self.original[index])))

    def set_locked(self,locked):
        self.locked = bool(locked)
        if self.locked:
            self.set_dimension(self.last_axis,getattr(self,self.last_axis))

    def preset(self,percent):
        if not math.isfinite(percent) or percent<=0:
            raise ValueError('Bitte einen positiven Prozentsatz eingeben.')
        self.width = max(1,round(self.original[0]*percent/100))
        self.height = max(1,round(self.original[1]*percent/100))

    def values(self,percent=False):
        if percent:
            return self.width*100/self.original[0],self.height*100/self.original[1]
        return self.width,self.height

    def dimensions(self):
        if min(self.width,self.height)<1 or self.width*self.height>80_000_000:
            raise ValueError('Die Zielgröße darf 80 Megapixel nicht überschreiten.')
        return self.width,self.height
