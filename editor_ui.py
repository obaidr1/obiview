"""Photo inspector with asynchronous previews and explicit reversible apply."""
from PIL import Image
from gi.repository import Gtk, GLib, GdkPixbuf
from dialog_layout import StandardDialog
from adjustments import adjusted, CONTROLS
from ui_theme import card, label, accessible, icon_button, selection_content, preview_surface


def preview_pixbuf(image):
    image = image.convert('RGBA')
    return GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(image.tobytes()),
        GdkPixbuf.Colorspace.RGB, True, 8, image.width, image.height, image.width*4)


class EditorUI:
    def setup_editor(self):
        self.preview_generation = 0
        self.preview_timer = 0
        self.preview_running = False
        self.preview_pixbuf = None
        self.preview_syncing = False
        self.preview_identity = None
        self.look = 'Original'
        self.adjust_sliders = {}
        self.histogram_values = None
        self.inspector = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, width_request=430)
        self.inspector.add_css_class('inspector')
        looks = card('Looks')
        row = Gtk.Box(spacing=2, homogeneous=True)
        self.look_buttons = {}
        group = None
        for name in ('Original','Film','Fade','Warm'):
            button = Gtk.ToggleButton()
            selection_content(button, name)
            if group:
                button.set_group(group)
            else:
                group = button
            button.set_active(name == 'Original')
            button.connect('toggled', self.look_changed, name)
            self.look_buttons[name] = button
            row.append(button)
        looks.append(row)
        self.inspector.append(looks)
        for title, keys in [('Licht',('brightness','contrast','gamma','highlights','shadows')),
                            ('Farbe',('temperature','saturation','vibrance','red','green','blue')),
                            ('Effekte',('grain','vignette','sharpness'))]:
            section = card(title)
            section.set_spacing(16)
            grid = Gtk.Grid(column_spacing=16,row_spacing=8,hexpand=True)
            if title == 'Licht':
                self.histogram = Gtk.DrawingArea(content_height=36)
                accessible(self.histogram,'RGB-Histogramm des Bildes')
                self.histogram.set_draw_func(self.draw_histogram)
                grid.attach(self.histogram,0,0,2,1)
            for index,key in enumerate(keys):
                field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                line = Gtk.Box()
                line.append(label(CONTROLS[key], hexpand=True))
                value = label('0', 'numeric-value')
                line.append(value)
                field.append(line)
                slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0 if key in ('grain','vignette') else -100, 100, 1)
                slider.set_draw_value(False)
                slider.set_value(0)
                accessible(slider, CONTROLS[key])
                slider.connect('value-changed',self.adjustment_changed,value)
                field.append(slider)
                grid.attach(field,index%2,(index//2)+(1 if title=='Licht' else 0),1,1)
                self.adjust_sliders[key] = slider
            section.append(grid)
            self.inspector.append(section)
        self.preview_note = label('Anpassungen als Vorschau', 'small muted', wrap=True)

        self.reset_adjustments = Gtk.Button(label='Zurücksetzen')
        self.reset_adjustments.connect('clicked',lambda *_:self.reset_preview())
        self.inspector_scroll = Gtk.ScrolledWindow(vexpand=True)
        self.inspector_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        self.inspector_scroll.set_hexpand(False)
        self.inspector_scroll.set_child(self.inspector)
        self.inspector_scroll.set_size_request(430,-1)
        self.inspector_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
        self.inspector_panel.append(self.inspector_scroll)
        self.inspector_panel.append(self.preview_note)
        self.editor_dialog = None
        self.adjust_picture = None

    def adjust_dialog(self):
        if self.busy or self.model.image is None:
            return
        self.stop_slideshow()
        if self.editor_dialog:
            self.editor_dialog.present()
            return
        dialog = StandardDialog(title='Bildanpassungen',transient_for=self,modal=True)
        dialog.set_titlebar(Gtk.Box())
        dialog.add_button('Abbrechen',Gtk.ResponseType.CANCEL)
        self.editor_accept = dialog.add_button('Anwenden',Gtk.ResponseType.ACCEPT)
        self.editor_accept.add_css_class('primary')
        actions = self.editor_accept.get_parent()
        actions.set_margin_start(20)
        actions.set_margin_end(20)
        actions.set_margin_top(12)
        actions.set_margin_bottom(20)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,
                       margin_start=20,margin_end=20,margin_top=16)
        body.append(label('Bildanpassungen','dialog-title'))
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=20,vexpand=True)
        preview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,hexpand=True)
        preview.set_size_request(240,-1)
        self.adjust_picture = Gtk.Picture(hexpand=True,vexpand=True,can_shrink=True)
        self.adjust_picture.set_size_request(-1,160); self.adjust_picture.set_vexpand(False)
        accessible(self.adjust_picture,'Vorschau der Bildanpassungen')
        preview.append(preview_surface(self.adjust_picture))
        preview.append(self.reset_adjustments)
        content.append(preview)
        content.append(self.inspector_panel)
        body.append(content)
        dialog.get_content_area().append(body)
        self.editor_dialog = dialog
        self.dialogs.append(dialog)
        self.set_scrim(True)
        def response(_dialog,answer):
            if self.busy:
                return
            content.remove(self.inspector_panel)
            preview.remove(self.reset_adjustments)
            self.editor_dialog = None
            self.adjust_picture = None
            self.dialogs.remove(dialog)
            self.set_scrim(False)
            dialog.destroy()
            if answer == Gtk.ResponseType.ACCEPT and self.has_preview():
                self.edit(lambda _m:None)
            else:
                self.reset_preview()
        dialog.connect('response',response)
        dialog.connect('close-request',lambda *_:(response(dialog,Gtk.ResponseType.CANCEL),True)[1])
        self.update_editor()
        dialog.present()

    def recipe(self):
        return {key:round(slider.get_value()) for key,slider in self.adjust_sliders.items()}, self.look

    def has_preview(self):
        return hasattr(self,'adjust_sliders') and (self.look != 'Original' or any(s.get_value() for s in self.adjust_sliders.values()))

    def look_changed(self, button, name):
        if button.get_active():
            self.look = name
            self.queue_preview()

    def adjustment_changed(self, slider, value):
        amount = round(slider.get_value())
        value.set_text(f'{amount:+d}' if amount else '0')
        self.queue_preview()

    def queue_preview(self):
        if self.preview_syncing or self.model.image is None:
            return
        self.stop_slideshow()
        self.preview_generation += 1
        if self.preview_timer:
            GLib.source_remove(self.preview_timer)
        self.preview_timer = GLib.timeout_add(120,self.render_preview)
        self.update_editor()

    def render_preview(self):
        self.preview_timer = 0
        if self.closed or self.busy:
            return False
        if self.preview_running:
            self.preview_timer = GLib.timeout_add(120,self.render_preview)
            return False
        if not self.has_preview():
            self.preview_pixbuf = None
            self.canvas.queue_draw()
            return False
        generation = self.preview_generation
        source = self.model.image
        values, look = self.recipe()
        self.preview_running = True
        def work():
            image = source.copy()
            image.thumbnail((1200,1200),Image.Resampling.LANCZOS)
            return adjusted(image,values,look)
        def done(image):
            self.preview_running = False
            if generation == self.preview_generation:
                self.preview_pixbuf = preview_pixbuf(image)
                if self.adjust_picture:
                    self.adjust_picture.set_pixbuf(self.preview_pixbuf)
                self.histogram_values = image.convert('RGB').histogram()
                self.histogram.queue_draw()
                self.canvas.queue_draw()
        def failed(error):
            self.preview_running = False
            if generation == self.preview_generation:
                self.preview_note.add_css_class('error')
                self.preview_note.set_text(f'Vorschau fehlgeschlagen: {error}')
        self.submit(work,done,failed)
        return False

    def reset_preview(self):
        if not hasattr(self,'adjust_sliders'):
            return
        self.preview_generation += 1
        if self.preview_timer:
            GLib.source_remove(self.preview_timer)
            self.preview_timer = 0
        self.preview_syncing = True
        for slider in self.adjust_sliders.values():
            slider.set_value(0)
        self.look_buttons['Original'].set_active(True)
        self.look = 'Original'
        self.preview_syncing = False
        self.preview_pixbuf = None
        self.preview_identity = None
        self.update_editor()
        self.canvas.queue_draw()

    def update_editor(self):
        if not hasattr(self,'inspector'):
            return
        loaded = self.model.image is not None
        self.inspector_panel.set_sensitive(loaded and not self.busy)
        pending = self.has_preview()
        if pending and not self.busy:
            self.undo_button.set_sensitive(True)
            self.lookup_action('undo').set_enabled(True)
        self.reset_adjustments.set_sensitive(pending)
        if self.editor_dialog:
            self.editor_accept.set_sensitive(pending and not self.busy)
            self.adjust_picture.set_pixbuf(self.preview_pixbuf or self.pixbuf)
        self.preview_note.remove_css_class('error')
        self.preview_note.set_text('Vorschau · noch nicht angewendet' if pending else 'Alle Anpassungen sind übernommen.')
        identity = (id(self.model.image),self.model.revision)
        if identity != self.preview_identity and loaded:
            self.preview_identity = identity
            source = self.model.image
            factor = min(256/source.width,256/source.height,1)
            thumb = source.resize((max(1,round(source.width*factor)),max(1,round(source.height*factor))))
            self.histogram_values = thumb.convert('RGB').histogram()
            self.histogram.queue_draw()
        self.empty_state.set_visible(not loaded)
        self.zoom_label.set_label(f'{self.scale*100:.0f} %')

    def draw_histogram(self, _area, cr, width, height):
        if not self.histogram_values:
            return
        colors = [(0.65,.32,.28),(.32,.52,.37),(.34,.43,.64)]
        peak = max(1,max(self.histogram_values))
        for channel,color in enumerate(colors):
            cr.set_source_rgba(*color,.45)
            cr.move_to(0,height)
            for x,value in enumerate(self.histogram_values[channel*256:(channel+1)*256]):
                cr.line_to(x*width/255,height - (value/peak)**.5*(height-3))
            cr.line_to(width,height)
            cr.close_path()
            cr.fill()
