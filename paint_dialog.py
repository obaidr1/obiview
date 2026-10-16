"""Drawing in a separate dialog; all strokes become one undoable edit."""
import math
from PIL import ImageDraw
from gi.repository import Gtk, Gdk
from advanced_ui import pixbuf
from ui_theme import label, accessible
from edit_controls import ChoiceButtons, SliderField


def paint_strokes(image,strokes):
    result=image.copy(); draw=ImageDraw.Draw(result)
    for kind,points,color,width in strokes:
        width=max(1,round(width)); start,end=points[0],points[-1]
        if kind=='pen':
            draw.line(points,fill=color,width=width,joint='curve')
            r=width/2
            for x,y in (start,end): draw.ellipse((x-r,y-r,x+r,y+r),fill=color)
        elif kind in ('line','arrow'):
            draw.line((start,end),fill=color,width=width)
            if kind=='arrow':
                angle=math.atan2(end[1]-start[1],end[0]-start[0]); length=max(10,width*4)
                vertices=[end]+[(end[0]-length*math.cos(angle+offset),end[1]-length*math.sin(angle+offset)) for offset in (-.45,.45)]
                draw.polygon(vertices,fill=color)
        else:
            box=(min(start[0],end[0]),min(start[1],end[1]),max(start[0],end[0]),max(start[1],end[1]))
            (draw.rectangle if kind=='rectangle' else draw.ellipse)(box,outline=color,width=width)
    return result


class PaintDialog(Gtk.Dialog):
    def __init__(self,parent):
        super().__init__(title='Zeichnen',transient_for=parent,modal=True,default_width=780,default_height=620)
        self.set_titlebar(Gtk.Box()); self.parent=parent
        self.source=parent.model.image.copy(); self.strokes=[]; self.points=[]
        self.add_button('Abbrechen',Gtk.ResponseType.CANCEL)
        self.add_button('Anwenden',Gtk.ResponseType.ACCEPT).add_css_class('primary')
        root=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin_top=16,margin_bottom=20,margin_start=20,margin_end=20)
        root.append(label('Zeichnen','dialog-title'))
        controls=Gtk.Box(spacing=10)
        self.tool=ChoiceButtons(columns=5)
        for ident,title in [('pen','Stift'),('line','Linie'),('arrow','Pfeil'),('rectangle','Rechteck'),('ellipse','Ellipse')]: self.tool.append(ident,title)
        self.tool.set_active_id('pen'); accessible(self.tool,'Zeichenwerkzeug'); root.append(self.tool)
        controls.append(label('Strichbreite'))
        self.width=SliderField(1,500,1,4,'Strichbreite'); accessible(self.width,'Strichbreite in Bildpixeln'); controls.append(self.width)
        rgba=Gdk.RGBA(); rgba.parse('#e43b2c'); self.color=Gtk.ColorButton(rgba=rgba); accessible(self.color,'Zeichenfarbe'); controls.append(self.color)
        undo=Gtk.Button(label='Letzter Strich zurück'); undo.connect('clicked',lambda *_:self.undo_stroke()); controls.append(undo)
        root.append(controls)
        self.area=Gtk.DrawingArea(hexpand=True,vexpand=True,content_height=360)
        accessible(self.area,'Zeichenfläche'); self.area.set_draw_func(self.draw); root.append(self.area)
        root.append(label('Mit der Maus zeichnen. Anwenden übernimmt die Zeichnung; Abbrechen verwirft sie.','muted',wrap=True))
        self.get_content_area().append(root)
        drag=Gtk.GestureDrag(button=1); drag.connect('drag-begin',self.begin); drag.connect('drag-update',self.update); drag.connect('drag-end',self.end); self.area.add_controller(drag)
        self.connect('response',self.response_done)
        self.connect('close-request',lambda *_:(self.response(Gtk.ResponseType.CANCEL),True)[1])
        parent.dialogs.append(self); parent.set_scrim(True); self.refresh_preview(); self.present()

    def refresh_preview(self):
        preview=self.source.copy(); preview.thumbnail((1200,1000)); factor=preview.width/self.source.width
        strokes=[(kind,[(x*factor,y*factor) for x,y in pts],color,width*factor) for kind,pts,color,width in self.strokes]
        self.buffer=pixbuf(paint_strokes(preview,strokes)); self.area.queue_draw()

    def draw(self,_area,cr,w,h):
        cr.set_source_rgb(.94,.94,.93); cr.paint()
        self.scale=min(w/self.source.width,h/self.source.height)
        self.origin=((w-self.source.width*self.scale)/2,(h-self.source.height*self.scale)/2)
        cr.save(); cr.translate(*self.origin); cr.scale(self.source.width*self.scale/self.buffer.get_width(),self.source.height*self.scale/self.buffer.get_height())
        Gdk.cairo_set_source_pixbuf(cr,self.buffer,0,0); cr.paint(); cr.restore()

    def point(self,x,y):
        return (max(0,min(self.source.width-1,(x-self.origin[0])/self.scale)),max(0,min(self.source.height-1,(y-self.origin[1])/self.scale)))

    def begin(self,_gesture,x,y):
        self.start=(x,y); self.points=[self.point(x,y)]
        rgba=self.color.get_rgba(); color=tuple(round(c*255) for c in (rgba.red,rgba.green,rgba.blue))+(255,)
        self.strokes.append((self.tool.get_active_id(),self.points,color,self.width.get_value()))

    def update(self,_gesture,dx,dy):
        if not self.points: return
        point=self.point(self.start[0]+dx,self.start[1]+dy)
        if self.tool.get_active_id()=='pen': self.points.append(point)
        else: self.points[:]=[self.points[0],point]
        self.refresh_preview()

    def end(self,gesture,dx,dy):
        self.update(gesture,dx,dy); self.points=[]

    def undo_stroke(self):
        if self.strokes: self.strokes.pop(); self.refresh_preview()

    def response_done(self,_dialog,response):
        parent=self.parent; parent.set_scrim(False); parent.dialogs.remove(self); self.destroy()
        if response==Gtk.ResponseType.ACCEPT and self.strokes:
            parent.edit(lambda m:m.replace(paint_strokes(m.image,self.strokes)))
