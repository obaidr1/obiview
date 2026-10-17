"""Compact native dialogs for selection, effects, text, preferences and printing."""
import io
import json
import os
import re
from pathlib import Path
from PIL import Image, ImageColor
from gi.repository import Gtk, Gdk, Gio, Pango, GObject, GLib
from dialog_layout import StandardDialog
from image_model import ImageModel
from image_tools import (fine_rotate, red_eye, frame, text_image,
                         to_pixels, checked_size, print_layout, panorama, add_canvas)
from ui_theme import label, card, accessible, preview_surface, ratio_link_state
from edit_controls import ChoiceButtons, SliderField
from editor_ui import preview_pixbuf


def _unit_from_title(title):
    text = title.casefold()
    if '%' in title or 'prozent' in text: return '%'
    if 'pixel' in text or re.search(r'\bpx\b', text): return 'px'
    if re.search(r'\bcm\b|zentimeter', text): return 'cm'
    if 'zoll' in text or re.search(r'\binch\b', text): return 'in'
    if 'grad' in text or 'winkel' in text: return '°'
    if 'dpi' in text: return 'DPI'
    if 'sekunde' in text: return 's'
    return ''


def image_clipboard_provider(image):
    from advanced_ui import pixbuf
    texture=Gdk.Texture.new_for_pixbuf(pixbuf(image))
    value=GObject.Value(); value.init(Gdk.Texture); value.set_object(texture)
    return Gdk.ContentProvider.new_for_value(value)


class ToolDialog(StandardDialog):
    def __init__(self,parent,title,fields,apply,note='',preview=None,sliders=(),linked_pair=None):
        super().__init__(title=title, transient_for=parent, modal=True)
        self.set_titlebar(Gtk.Box())
        self.widgets, self.kinds = {}, {}
        self.fields = fields
        self.apply, self.preview_operation = apply, preview
        self.alive, self.syncing = True, False
        self.preview_timer = 0
        self.preview_running = False
        self.preview_generation = 0
        self.preview_ready = False
        self.pending_accept = False
        self.preview_buffer = None
        self.add_button('Abbrechen',Gtk.ResponseType.CANCEL)
        self.accept = self.add_button('Anwenden',Gtk.ResponseType.ACCEPT)
        self.accept.add_css_class('primary')
        actions = self.accept.get_parent()
        for side in ('start','end','bottom'): getattr(actions,'set_margin_'+side)(20)
        actions.set_margin_top(12)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,
                       margin_top=20,margin_start=20,margin_end=20)
        body.append(label(title,'dialog-title'))
        if note: body.append(label(note,'muted',wrap=True,max_width_chars=40))
        content = Gtk.Box(orientation=(Gtk.Orientation.HORIZONTAL if preview else Gtk.Orientation.VERTICAL),
                          spacing=20,vexpand=True)
        if preview:
            self.source = parent.model.image.copy()
            thumb = self.source.copy(); thumb.thumbnail((1200,1200))
            self.original_buffer = preview_pixbuf(thumb)
            left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,hexpand=True)
            left.set_size_request(240,-1)
            self.picture = Gtk.Picture(hexpand=True,vexpand=True,can_shrink=True)
            self.picture.set_size_request(-1,160); self.picture.set_vexpand(False)
            accessible(self.picture,'Live-Vorschau: '+title)
            left.append(preview_surface(self.picture))
            self.compare = Gtk.ToggleButton(label='Original vergleichen')
            self.compare.connect('toggled',self.show_preview)
            left.append(self.compare)
            self.preview_note = label('','small muted',wrap=True)
            left.append(self.preview_note)
            content.append(left)
        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        section = card('Einstellungen')
        section.set_spacing(16)
        controls.append(section)
        field_grid = Gtk.Grid(column_spacing=16,row_spacing=10,hexpand=True)
        section.append(field_grid)
        columns = 1 if preview else 2
        rendered_fields = {}
        pair_keys = set(linked_pair or ())
        for key,title,value,kind in fields:
            visual_widget = None
            if linked_pair and key == linked_pair[2]:
                widget = Gtk.ToggleButton(child=Gtk.Image.new_from_icon_name('insert-link-symbolic'),active=value)
                widget.add_css_class('ratio-link')
                ratio_link_state(widget)
                widget.connect('toggled',ratio_link_state)
            elif isinstance(kind,list):
                widget = ChoiceButtons()
                for ident,text in kind: widget.append(str(ident),text)
                widget.set_active_id(str(value))
            elif isinstance(kind,tuple):
                if key in sliders:
                    widget = SliderField(*kind,value=value,title=title,exact=key in ('width','inner_width'),
                                         unit=_unit_from_title(title))
                else:
                    widget = Gtk.SpinButton.new_with_range(*kind)
                    widget.set_digits(2 if kind[2] < 1 else 0)
                    widget.set_update_policy(Gtk.SpinButtonUpdatePolicy.ALWAYS)
                    widget.set_value(value); widget.set_numeric(True)
                    unit = _unit_from_title(title)
                    widget.set_increments(kind[2],kind[2]*10)
                    shown_step=f'{kind[2]:g}' + (f' {unit}' if unit else '')
                    page_step=f'{kind[2]*10:g}' + (f' {unit}' if unit else '')
                    widget.set_tooltip_text(f'Pfeiltasten: {shown_step}; Bild auf/ab: {page_step}.')
                    if unit:
                        value_box = Gtk.Box(spacing=4, hexpand=True)
                        value_box.append(widget)
                        value_box.append(label(unit,'small muted unit-suffix'))
                        visual_widget = value_box
            elif kind == 'bool': widget = Gtk.CheckButton(active=value)
            elif kind == 'color':
                rgba = Gdk.RGBA(); rgba.parse(value)
                widget = Gtk.ColorButton(rgba=rgba)
                widget.set_use_alpha(False); widget.set_title(title)
            elif kind == 'font': widget = Gtk.FontButton(font=value,use_font=True)
            elif kind == 'text':
                widget = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR,height_request=100)
                widget.get_buffer().set_text(value)
            else: widget = Gtk.Entry(text=str(value))
            widget.set_hexpand(True); accessible(widget,title)
            if linked_pair and key == linked_pair[2]:
                accessible(widget,'Seitenverhältnis beibehalten')
                field = None
            else:
                field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
                if kind == 'bool': widget.set_label(title)
                else: field.append(label(title))
                field.append(visual_widget or widget)
            rendered_fields[key] = field
            self.widgets[key], self.kinds[key] = widget,kind

        layout_items=[]
        for key,_title,_value,_kind in fields:
            if linked_pair and key==linked_pair[0]:
                layout_items.append(('linked',linked_pair))
            elif linked_pair and key in pair_keys:
                continue
            else:
                layout_items.append(('field',key))
        row=column=0
        for item,key in layout_items:
            if item=='linked':
                if column: row+=1; column=0
                left,right,lock=key
                group=Gtk.Box(spacing=8,hexpand=True)
                group.append(rendered_fields[left])
                group.append(self.widgets[lock])
                group.append(rendered_fields[right])
                field_grid.attach(group,0,row,columns,1)
                row+=1; column=0
                continue
            field=rendered_fields[key]
            kind=self.kinds[key]
            span=columns if kind=='text' and columns>1 else 1
            if span==columns and column:
                row+=1; column=0
            field_grid.attach(field,column,row,span,1)
            column+=span
            if column>=columns:
                row+=1; column=0
        self.error = label('','error',wrap=True); controls.append(self.error)
        if preview:
            reset = Gtk.Button(label='Zurücksetzen')
            reset.connect('clicked',self.reset)
            controls.append(reset)
        self.controls_scroll = Gtk.ScrolledWindow(vexpand=True,hexpand=not bool(preview))
        self.controls_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        if preview: self.controls_scroll.set_size_request(320,-1)
        self.controls_scroll.set_child(controls); content.append(self.controls_scroll)
        body.append(content); self.get_content_area().append(body)
        self.connect('response',self.respond)
        self.connect('close-request',lambda *_:(self.respond(self,Gtk.ResponseType.CANCEL),True)[1])
        parent.set_scrim(True); parent.dialogs.append(self)
        if preview:
            for key,widget in self.widgets.items():
                kind = self.kinds[key]
                signal = ('value-changed' if isinstance(kind,tuple) else 'changed' if isinstance(kind,list)
                          else 'toggled' if kind=='bool' else 'notify::rgba' if kind=='color'
                          else 'notify::font' if kind=='font' else 'changed')
                (widget.get_buffer() if kind=='text' else widget).connect(signal,self.queue_preview)
            self.show_preview(); self.queue_preview()
        self.present()

    def values(self):
        result = {}
        for key,w in self.widgets.items():
            kind = self.kinds[key]
            if isinstance(kind,tuple): value = w.get_value()
            elif isinstance(kind,list): value = w.get_active_id()
            elif kind == 'bool': value = w.get_active()
            elif kind == 'color':
                rgba = w.get_rgba()
                value = '#'+''.join(f'{round(channel*255):02x}' for channel in (rgba.red,rgba.green,rgba.blue))
            elif kind == 'font': value = w.get_font()
            elif kind == 'text':
                buffer = w.get_buffer(); value = buffer.get_text(*buffer.get_bounds(),False)
            else: value = w.get_text()
            result[key] = value
        return result

    def reset(self,*_):
        self.syncing = True
        for key,_title,value,kind in self.fields:
            widget = self.widgets[key]
            if isinstance(kind,tuple): widget.set_value(value)
            elif isinstance(kind,list): widget.set_active_id(str(value))
            elif kind=='bool': widget.set_active(value)
            elif kind=='color':
                rgba=Gdk.RGBA(); rgba.parse(value); widget.set_rgba(rgba)
            elif kind=='font': widget.set_font(value)
            elif kind=='text': widget.get_buffer().set_text(value)
            else: widget.set_text(str(value))
        self.syncing = False
        self.compare.set_active(False)
        self.queue_preview()

    def show_preview(self,*_):
        if self.alive:
            self.picture.set_pixbuf(self.original_buffer if self.compare.get_active()
                                    else self.preview_buffer or self.original_buffer)

    def queue_preview(self,*_):
        if not self.alive or self.syncing: return
        self.preview_generation += 1
        self.preview_ready = False
        self.error.set_text('')
        self.accept.set_sensitive(not self.pending_accept)
        self.preview_note.set_text('Vorschau wird berechnet …')
        if self.preview_timer: GLib.source_remove(self.preview_timer)
        self.preview_timer = GLib.timeout_add(120,self.render_preview)

    def render_preview(self):
        self.preview_timer = 0
        if not self.alive: return False
        if self.preview_running:
            self.preview_timer=GLib.timeout_add(120,self.render_preview); return False
        values = self.values()
        generation = self.preview_generation
        self.preview_running = True
        operation, source = self.preview_operation, self.source
        def work():
            image = operation(source.copy(),values)
            size = image.size
            image.thumbnail((1200,1200),Image.Resampling.LANCZOS)
            return image,size
        def done(result):
            self.preview_running = False
            if not self.alive or generation!=self.preview_generation: return
            image,size = result
            self.preview_buffer = preview_pixbuf(image)
            self.preview_ready = True
            self.preview_note.set_text(f'{size[0]} × {size[1]} px · Vorschau, noch nicht angewendet')
            self.show_preview()
            if self.pending_accept: self.respond(self,Gtk.ResponseType.ACCEPT)
        def failed(error):
            self.preview_running = False
            if not self.alive or generation!=self.preview_generation: return
            self.pending_accept = False
            self.controls_scroll.set_sensitive(True)
            self.error.set_text(f'Vorschau fehlgeschlagen: {error}'); self.preview_note.set_text('Einstellungen prüfen und erneut versuchen.')
            self.accept.set_sensitive(False)
        self.get_transient_for().submit(work,done,failed)
        return False

    def respond(self,_dialog,response):
        if not self.alive: return
        if response == Gtk.ResponseType.ACCEPT:
            values = self.values()
            if self.preview_operation and not self.preview_ready:
                self.pending_accept=True
                self.accept.set_sensitive(False)
                self.controls_scroll.set_sensitive(False)
                return
            try: self.apply(values)
            except Exception as error:
                self.error.set_text(str(error)); self.pending_accept=False
                self.controls_scroll.set_sensitive(True); self.accept.set_sensitive(True); return
        self.alive = False
        self.pending_accept = False
        self.preview_generation += 1
        if self.preview_timer: GLib.source_remove(self.preview_timer); self.preview_timer=0
        parent = self.get_transient_for()
        parent.set_scrim(False); parent.dialogs.remove(self); self.destroy()


class ImageToolsUI:
    def setup_tools(self):
        config = Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'bildblick'/'viewer.json'
        self.viewer_config = config
        self.background = '#f5f5f3'
        self.fit_upscale = False
        try:
            values = json.loads(config.read_text())
            ImageColor.getrgb(values['background'])
            self.background = values['background']
            self.fit_upscale = bool(values.get('fit_upscale',False))
        except (OSError,ValueError,KeyError,TypeError): pass

    def preview_tool(self,title,fields,operation,note='',sliders=()):
        if self.busy or self.model.image is None: return
        if self.has_preview():
            self.edit(lambda _m:None,after=lambda:self.preview_tool(title,fields,operation,note,sliders)); return
        self.stop_slideshow()
        return ToolDialog(self,title,fields,
            lambda values:self.edit(lambda model:model.replace(operation(model.image,values))),
            note,preview=operation,sliders=sliders)

    def preferences_dialog(self):
        def apply(v):
            self.viewer_config.parent.mkdir(parents=True,exist_ok=True)
            temporary = self.viewer_config.with_suffix('.tmp')
            temporary.write_text(json.dumps(v))
            temporary.replace(self.viewer_config)
            self.background, self.fit_upscale = v['background'],v['fit_upscale']
            self.canvas.queue_draw()
        return ToolDialog(self,'Ansicht einstellen',[
            ('background','Hintergrund',self.background,'color'),
            ('fit_upscale','Kleine Bilder beim Einpassen vergrößern',self.fit_upscale,'bool')],apply,
            'Diese Einstellungen werden für den nächsten Start gespeichert.')

    def fine_rotation_dialog(self):
        return self.preview_tool('Frei drehen',[
            ('angle','Winkel (Grad)',0,(-360,360,.1)),('expand','Bildfläche erweitern',True,'bool'),
            ('color','Randfarbe','#ffffff','color')],
            lambda image,v:fine_rotate(image,**v),
            'Positive Winkel drehen nach rechts, negative nach links. Den Rand danach bei Bedarf zuschneiden.',sliders=('angle',))

    def effects_dialog(self):
        from effects_dialog import EffectsDialog
        if self.busy or self.model.image is None:
            return
        if self.has_preview():
            self.edit(lambda _m: None, after=self.effects_dialog)
            return
        for dialog in self.dialogs:
            if isinstance(dialog, EffectsDialog):
                dialog.present()
                return dialog
        self.stop_slideshow()
        return EffectsDialog(self)

    def border_dialog(self):
        dialog = self.preview_tool('Rahmen hinzufügen',[
            ('style','Stil','plain',[('plain','Einfach'),('double','Doppelrahmen'),('bevel','Reliefrahmen')]),
            ('width','Breite außen (Pixel)',20,(0,10000,1)),('color','Außenfarbe','#ffffff','color'),
            ('inner_width','Breite innen, Doppelrahmen',2,(0,10000,1)),
            ('inner_color','Innenfarbe','#242424','color')],
            lambda image,v:frame(image,**v),sliders=('width','inner_width'))
        if dialog:
            def changed(*_):
                double=dialog.widgets['style'].get_active_id()=='double'
                for key in ('inner_width','inner_color'): dialog.widgets[key].set_sensitive(double)
            dialog.widgets['style'].connect('changed',changed); changed()
        return dialog

    def canvas_dialog(self):
        return self.preview_tool('Leinwand erweitern',[
            ('left','Links (Pixel)',20,(-10000,10000,1)),('right','Rechts (Pixel)',20,(-10000,10000,1)),
            ('top','Oben (Pixel)',20,(-10000,10000,1)),('bottom','Unten (Pixel)',20,(-10000,10000,1)),
            ('color','Farbe','#ffffff','color')],
            lambda image,v:add_canvas(image,**v),
            'Jede Bildseite unabhängig ändern: positive Werte ergänzen Rand, negative schneiden ihn ab. Vorhandene Pixel werden nicht skaliert.')

    def red_eye_dialog(self):
        box = self.selection
        if not box:
            self.message('Augenbereich auswählen','Mit der Maus zuerst einen engen Rahmen um den roten Augenbereich aufziehen.')
            return
        return self.preview_tool('Rote Augen korrigieren', [('strength','Stärke (%)',100,(1,100,1))],
            lambda image,v:red_eye(image,box,**v),
            'Nur rot dominierte Pixel innerhalb der Auswahl werden korrigiert.',sliders=('strength',))

    def selection_dialog(self):
        image = self.model.image
        box = self.selection or (0,0,image.width,image.height)
        units = [('px','Pixel'),('cm','Zentimeter'),('inch','Zoll')]
        def apply(v):
            w,h = to_pixels(v['width'],v['unit'],v['dpi']),to_pixels(v['height'],v['unit'],v['dpi'])
            ratio = image.width/image.height if v['ratio']=='image' else float(v['ratio']) if v['ratio']!='free' else None
            if ratio: h = max(1,round(w/ratio))
            x,y = int(v['x']),int(v['y'])
            checked_size(w,h)
            if x+w>image.width or y+h>image.height:
                raise ValueError('Die Auswahl passt nicht ins Bild. Breite, Höhe oder Position verkleinern.')
            self.crop_toggle.set_active(True)
            self.selection = (x,y,x+w,y+h)
            self.refresh()
        dialog = ToolDialog(self,'Eigene Auswahl',[
            ('ratio','Seitenverhältnis','free',[('free','Frei'),('image','Wie das Bild'),('1','1:1'),('2','2:1'),
                                               ('0.5','1:2'),(str(4/3),'4:3'),(str(3/2),'3:2'),(str(16/9),'16:9')]),
            ('unit','Einheit','px',units),('dpi','DPI',self.model.dpi,(1,9600,1)),
            ('width','Breite',box[2]-box[0],(.01,80000000,.1)),
            ('height','Höhe',box[3]-box[1],(.01,80000000,.1)),
            ('x','Position X (Pixel)',box[0],(0,image.width-1,1)),
            ('y','Position Y (Pixel)',box[1],(0,image.height-1,1))],apply,
            'Bei festem Verhältnis bestimmt die Breite die Höhe. Auswahlkanten ziehen; mit rechter Maustaste verschieben.')
        self.link_units(dialog)
        def ratio_changed(widget):
            ident = widget.get_active_id()
            dialog.widgets['height'].set_sensitive(ident=='free')
            if ident!='free':
                ratio = image.width/image.height if ident=='image' else float(ident)
                dialog.widgets['height'].set_value(dialog.widgets['width'].get_value()/ratio)
        dialog.widgets['ratio'].connect('changed',ratio_changed)
        dialog.widgets['width'].connect('value-changed',lambda *_:ratio_changed(dialog.widgets['ratio']))
        return dialog

    @staticmethod
    def link_units(dialog):
        state = ['px']
        def changed(widget):
            new = widget.get_active_id(); old = state[0]; dpi = dialog.widgets['dpi'].get_value()
            factors = {'px':1,'cm':dpi/2.54,'inch':dpi}
            state[0] = new
            values = {name:dialog.widgets[name].get_value()*factors[old]/factors[new] for name in ('width','height')}
            for name,value in values.items():
                dialog.widgets[name].set_value(value)
        dialog.widgets['unit'].connect('changed',changed)

    def text_dialog(self):
        box = self.selection or (20 if self.model.image.width>20 else 0,20 if self.model.image.height>20 else 0,
                                 self.model.image.width,self.model.image.height)
        def operation(image,v):
            if not v['text'].strip(): raise ValueError('Bitte Text eingeben.')
            desc = Pango.FontDescription.from_string(v['font'])
            pixels = desc.get_size()/Pango.SCALE
            if not desc.get_size_is_absolute(): pixels *= self.model.dpi/72
            checked_size(max(1,pixels),1)
            return text_image(image,v['text'],box,desc.get_family(),pixels,v['color'],
                            desc.get_weight()>=Pango.Weight.BOLD,desc.get_style()!=Pango.Style.NORMAL)
        return self.preview_tool('Text einfügen',[
            ('text','Text','','text'),('font','Schrift / Stil / Größe','Sans 48','font'),
            ('color','Textfarbe','#ffffff','color')],operation,
            'Text wird im ausgewählten Rechteck umgebrochen und begrenzt. Ohne Auswahl beginnt er oben links mit 20 Pixel Abstand. Schriftgröße in Punkt, umgerechnet mit der Bild-DPI.')

    def new_document(self,image,name='Unbenannt.png'):
        model = ImageModel()
        model.image = image.convert('RGBA')
        model.path = Path.home()/name
        model.revision = 1; model.next_revision = 2
        self.adopt_model(model)

    def new_window(self):
        window = type(self)(self.get_application())
        window.present()
        return window

    def clear_image(self):
        def clear():
            self.reset_preview()
            self.model = ImageModel(); self.pixbuf = None; self.selection = None
            self.crop_toggle.set_active(False)
            self.status.set_text('Bild öffnen · O oder Strg+V')
            self.refresh()
        self.guard(clear)

    def paste_image(self):
        def read():
            self.set_busy(True)
            def ready(clipboard,result):
                try:
                    texture = clipboard.read_texture_finish(result)
                    if texture is None: raise ValueError('Die Zwischenablage enthält kein Bild.')
                    checked_size(texture.get_width(),texture.get_height())
                    with Image.open(io.BytesIO(texture.save_to_png_bytes().get_data())) as source:
                        image = source.convert('RGBA')
                    if not self.closed: self.new_document(image)
                except Exception as error:
                    if not self.closed: self.message('Einfügen fehlgeschlagen',str(error))
                finally:
                    if not self.closed: self.set_busy(False)
            self.get_clipboard().read_texture_async(None,ready)
        self.guard(read)

    def copy_image(self):
        if self.has_preview():
            box=self.selection
            def copied():
                self.selection=box; self.copy_image()
            self.edit(lambda _m:None,after=copied); return
        image = self.model.image.crop(self.selection) if self.selection else self.model.image
        self.get_clipboard().set_content(image_clipboard_provider(image))

    def panorama_dialog(self):
        def chosen(paths):
            if len(paths)<2:
                self.message('Bilder nebeneinander','Mindestens zwei Dateien wählen.'); return
            def apply(v):
                def start():
                    self.set_busy(True)
                    def work():
                        images=[]; total=0
                        for path in paths:
                            model=ImageModel(); model.load(path)
                            total+=model.image.width*model.image.height
                            if total>80_000_000: raise ValueError('Zusammen höchstens 80 Megapixel verwenden.')
                            images.append(model.image)
                        return panorama(images,**v)
                    def done(image):
                        self.new_document(image,'Panorama.png'); self.set_busy(False)
                    self.submit(work,done,lambda e:(self.set_busy(False),self.message('Zusammenfügen fehlgeschlagen',str(e))))
                self.guard(start)
            ToolDialog(self,'Bilder zusammenfügen',[
                ('vertical','Untereinander statt nebeneinander',False,'bool'),
                ('gap','Abstand (Pixel)',0,(0,1000,1)),('color','Hintergrund','#ffffff','color')],apply,
                'Reihenfolge: '+', '.join(p.name for p in paths)+'. Die Bilder werden aneinandergesetzt, nicht nahtlos verschmolzen.')
        self.choose('Bilder zusammenfügen',chosen,multiple=True)

    def print_image(self):
        if self.has_preview():
            self.edit(lambda _m:None,after=self.print_image); return
        dialog = ToolDialog(self,'Bild drucken',[
            ('orientation','Ausrichtung','portrait',[('portrait','Hochformat'),('landscape','Querformat')]),
            ('mode','Bildgröße','fit',[('fit','Bestmöglich einpassen'),('custom','Eigene Größe (cm)'),('scale','Skalierung (%)')]),
            ('width_cm','Breite (cm)',10,(.01,200,.1)),('height_cm','Höhe (cm)',10*self.model.image.height/self.model.image.width,(.01,200,.1)),
            ('locked','Seitenverhältnis (eigene Größe)',True,'bool'),
            ('scale_x','Breite (%)',100,(.1,1000,.1)),('scale_y','Höhe (%)',100,(.1,1000,.1)),
            ('centered','Auf Seite zentrieren',True,'bool'),('x_cm','Abstand links (cm)',0,(0,200,.1)),
            ('y_cm','Abstand oben (cm)',0,(0,200,.1))],self.run_print,
            'Danach folgen Druckerauswahl, Papier und Druckereigenschaften. Prozentwerte beziehen sich auf die Bild-DPI. Übergröße wird an den druckbaren Seitenrändern abgeschnitten.',
            linked_pair=('width_cm','height_cm','locked'))

        syncing = [False]
        def dimensions_changed(widget,axis):
            if syncing[0] or not dialog.widgets['locked'].get_active(): return
            syncing[0] = True
            ratio = self.model.image.width/self.model.image.height
            other = 'height_cm' if axis=='width_cm' else 'width_cm'
            dialog.widgets[other].set_value(widget.get_value()/ratio if axis=='width_cm' else widget.get_value()*ratio)
            syncing[0] = False
        for axis in ('width_cm','height_cm'):
            dialog.widgets[axis].connect('value-changed',dimensions_changed,axis)
        dialog.widgets['locked'].connect('toggled',lambda *_:dimensions_changed(dialog.widgets['width_cm'],'width_cm'))
        def mode_changed(*_):
            mode = dialog.widgets['mode'].get_active_id()
            for key in ('width_cm','height_cm','locked'): dialog.widgets[key].set_sensitive(mode=='custom')
            for key in ('scale_x','scale_y'): dialog.widgets[key].set_sensitive(mode=='scale')
            for key in ('x_cm','y_cm'): dialog.widgets[key].set_sensitive(not dialog.widgets['centered'].get_active())
        dialog.widgets['mode'].connect('changed',mode_changed)
        dialog.widgets['centered'].connect('toggled',mode_changed)
        mode_changed()
        return dialog

    def run_print(self,values,export_path=None,direct=False):
        self.stop_slideshow()
        self.last_print_values=dict(values)
        values = dict(values)
        orientation = values.pop('orientation')
        operation = Gtk.PrintOperation()
        operation.set_n_pages(1); operation.set_unit(Gtk.Unit.POINTS)
        if getattr(self,'last_print_settings',None): operation.set_print_settings(self.last_print_settings)
        setup = Gtk.PageSetup()
        setup.set_orientation(Gtk.PageOrientation.LANDSCAPE if orientation=='landscape' else Gtk.PageOrientation.PORTRAIT)
        operation.set_default_page_setup(setup)
        buffer = self.pixbuf
        size,dpi = self.model.image.size,self.model.dpi_pair
        def draw_page(_op,context,_page):
            cr = context.get_cairo_context()
            x,y,w,h = print_layout(size,(context.get_width(),context.get_height()),dpi=dpi,**values)
            cr.set_source_rgb(1,1,1); cr.paint()
            cr.translate(x,y); cr.scale(w/size[0],h/size[1])
            Gdk.cairo_set_source_pixbuf(cr,buffer,0,0); cr.paint()
        operation.connect('draw-page',draw_page)
        if export_path: operation.set_export_filename(str(export_path))
        mode=Gtk.PrintOperationAction.EXPORT if export_path else Gtk.PrintOperationAction.PRINT if direct else Gtk.PrintOperationAction.PRINT_DIALOG
        result=operation.run(mode,self)
        if result==Gtk.PrintOperationResult.APPLY and not export_path: self.last_print_settings=operation.get_print_settings()
        return operation
