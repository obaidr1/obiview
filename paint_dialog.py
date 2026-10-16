"""Drawing in a separate dialog; all strokes become one undoable edit."""
import math
from PIL import Image, ImageDraw, ImageFilter
from gi.repository import Gtk, Gdk
from dialog_layout import StandardDialog
from advanced_ui import pixbuf
from ui_theme import label, accessible
from edit_controls import ChoiceButtons, SliderField


def paint_strokes(image,strokes):
    result=image.copy(); draw=ImageDraw.Draw(result)
    for kind,points,color,width in strokes:
        width=max(1,round(width)); start,end=points[0],points[-1]
        if kind=='brush':
            margin=width*2
            x0=max(0,math.floor(min(x for x,y in points)-margin))
            y0=max(0,math.floor(min(y for x,y in points)-margin))
            x1=min(image.width,math.ceil(max(x for x,y in points)+margin+1))
            y1=min(image.height,math.ceil(max(y for x,y in points)+margin+1))
            if x1<=x0 or y1<=y0: continue
            local=[(x-x0,y-y0) for x,y in points]
            mask=Image.new('L',(x1-x0,y1-y0)); brush=ImageDraw.Draw(mask)
            core=max(1,round(width*.6)); radius=core/2
            brush.line(local,fill=255,width=core,joint='curve')
            for x,y in (local[0],local[-1]): brush.ellipse((x-radius,y-radius,x+radius,y+radius),fill=255)
            mask=mask.filter(ImageFilter.GaussianBlur(max(.5,width*.16)))
            if len(color)>3 and color[3]!=255: mask=mask.point(lambda v:round(v*color[3]/255))
            layer=Image.new('RGBA',mask.size,color); layer.putalpha(mask)
            result.alpha_composite(layer,(x0,y0)); draw=ImageDraw.Draw(result)
        elif kind=='pen':
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


def tool_symbol(area,cr,width,height,kind,button):
    """Resolution-independent, theme-aware line icons for the actual tools."""
    cr.scale(width/24,height/24)
    cr.set_source_rgb(*((1,1,1) if button.get_active() else (.14,.14,.14)))
    cr.set_line_width(1.7); cr.set_line_cap(1); cr.set_line_join(1)
    if kind=='pen':
        cr.move_to(5,15); cr.line_to(16,4); cr.line_to(20,8); cr.line_to(9,19)
        cr.line_to(4,20); cr.close_path(); cr.stroke()
        cr.move_to(14,6); cr.line_to(18,10); cr.move_to(5,15); cr.line_to(9,19); cr.stroke()
    elif kind=='brush':
        cr.move_to(10,13); cr.line_to(18,3); cr.curve_to(20,1,23,4,21,6)
        cr.line_to(13,16); cr.close_path(); cr.stroke()
        cr.move_to(10,13); cr.curve_to(4,11,7,20,2,20)
        cr.curve_to(12,23,17,19,13,16); cr.stroke()
    elif kind in ('line','arrow'):
        cr.move_to(4,20); cr.line_to(20,4)
        if kind=='arrow': cr.move_to(11,4); cr.line_to(20,4); cr.line_to(20,13)
        cr.stroke()
    elif kind=='rectangle': cr.rectangle(3,5,18,14); cr.stroke()
    else:
        cr.translate(12,12); cr.scale(1,.75); cr.arc(0,0,9,0,2*math.pi); cr.stroke()


class PaintDialog(StandardDialog):
    def __init__(self,parent):
        super().__init__(title='Zeichnen',transient_for=parent,modal=True,default_width=780,default_height=620)
        self.set_titlebar(Gtk.Box()); self.parent=parent
        self.source=parent.model.image.copy(); self.strokes=[]; self.points=[]
        self.add_button('Abbrechen',Gtk.ResponseType.CANCEL)
        self.add_button('Anwenden',Gtk.ResponseType.ACCEPT).add_css_class('primary')
        root=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin_top=16,margin_bottom=20,margin_start=20,margin_end=20)
        root.append(label('Zeichnen','dialog-title'))
        controls=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
        self.tool=ChoiceButtons(columns=3)
        self.tool_icons={}
        for ident,title in [('pen','Stift'),('brush','Pinsel'),('line','Linie'),('arrow','Pfeil'),('rectangle','Rechteck'),('ellipse','Ellipse')]:
            self.tool.append(ident,title)
            button=self.tool.buttons[ident]
            content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4,
                            halign=Gtk.Align.CENTER,margin_top=4,margin_bottom=4)
            symbol=Gtk.DrawingArea(content_width=24,content_height=24,halign=Gtk.Align.CENTER)
            symbol.set_draw_func(lambda area,cr,w,h,k=ident,b=button:tool_symbol(area,cr,w,h,k,b))
            button.connect('toggled',lambda _b,icon=symbol:icon.queue_draw())
            accessible(symbol,title+'-Symbol'); self.tool_icons[ident]=symbol
            content.append(symbol); content.append(label(title)); button.set_child(content)
            button.set_tooltip_text('Pinsel mit weicher Kante' if ident=='brush' else title)
        self.tool.set_active_id('pen'); accessible(self.tool,'Zeichenwerkzeug'); root.append(self.tool)
        controls.append(label('Strichbreite'))
        self.width=SliderField(1,500,1,4,'Strichbreite',exact=True); accessible(self.width,'Strichbreite in Bildpixeln'); controls.append(self.width)
        controls.append(label('Farbe'))
        rgba=Gdk.RGBA(); rgba.parse('#e43b2c'); self.color=Gtk.ColorButton(rgba=rgba); accessible(self.color,'Zeichenfarbe'); controls.append(self.color)
        undo=Gtk.Button(tooltip_text='Letzter Strich zurück'); undo_content=Gtk.Box(spacing=6)
        undo_content.append(Gtk.Image(icon_name='edit-undo-symbolic')); undo_content.append(label('Zurück'))
        undo.set_child(undo_content); accessible(undo,'Letzter Strich zurück')
        undo.connect('clicked',lambda *_:self.undo_stroke()); controls.append(undo)
        root.append(controls)
        self.area=Gtk.DrawingArea(hexpand=True,vexpand=True,content_height=220)
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
        if self.tool.get_active_id() in ('pen','brush'): self.points.append(point)
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
