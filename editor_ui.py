"""Photo inspector with asynchronous previews and explicit reversible apply."""
from PIL import Image
from gi.repository import Gtk, GLib, GdkPixbuf
from adjustments import adjusted, CONTROLS
from ui_theme import card, label, accessible, icon_button


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
        self.inspector = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, width_request=272)
        self.inspector.add_css_class('inspector')
        looks = card('Looks')
        row = Gtk.Box(spacing=2, homogeneous=True)
        self.look_buttons = {}
        group = None
        for name in ('Original','Film','Fade','Warm'):
            button = Gtk.ToggleButton(label=name)
            button.add_css_class('small')
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
        for title, keys in [('Licht',('brightness','contrast','highlights','shadows')),
                            ('Farbe',('temperature','saturation','vibrance')),
                            ('Effekte',('grain','vignette','sharpness'))]:
            section = card(title)
            section.set_spacing(3)
            if title == 'Licht':
                self.histogram = Gtk.DrawingArea(content_height=36)
                accessible(self.histogram,'RGB-Histogramm des Bildes')
                self.histogram.set_draw_func(self.draw_histogram)
                section.append(self.histogram)
            for key in keys:
                line = Gtk.Box()
                line.append(label(CONTROLS[key], hexpand=True))
                value = label('0', 'small muted')
                line.append(value)
                section.append(line)
                slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0 if key in ('grain','vignette') else -100, 100, 1)
                slider.set_draw_value(False)
                slider.set_value(0)
                accessible(slider, CONTROLS[key])
                slider.connect('value-changed',self.adjustment_changed,value)
                section.append(slider)
                self.adjust_sliders[key] = slider
            self.inspector.append(section)
        self.preview_note = label('Anpassungen als Vorschau', 'small muted', wrap=True)

        row = Gtk.Box(spacing=8, homogeneous=True)
        self.reset_adjustments = Gtk.Button(label='Zurücksetzen')
        self.reset_adjustments.connect('clicked',lambda *_:self.reset_preview())
        self.apply_adjustments = Gtk.Button(label='Anwenden')
        self.apply_adjustments.connect('clicked',lambda *_:self.edit(lambda _m:None))
        row.append(self.reset_adjustments)
        row.append(self.apply_adjustments)
        footer_row = row
        self.inspector_scroll = Gtk.ScrolledWindow(vexpand=True)
        self.inspector_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        self.inspector_scroll.set_hexpand(False)
        self.inspector_scroll.set_child(self.inspector)
        self.inspector_scroll.set_size_request(304,-1)
        workspace = Gtk.Box(spacing=8, vexpand=True)
        self.pane.set_hexpand(True)
        parent = self.pane.get_parent()
        previous = self.pane.get_prev_sibling()
        parent.remove(self.pane)
        workspace.append(self.pane)
        self.inspector_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
        self.inspector_panel.set_hexpand(False)
        self.inspector_panel.append(self.inspector_scroll)
        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8,
                         margin_start=12,margin_end=20,margin_bottom=12)
        footer.append(self.preview_note)
        footer.append(footer_row)
        self.inspector_panel.append(footer)
        workspace.append(self.inspector_panel)
        parent.insert_child_after(workspace,previous)
        self.workspace = workspace

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
                self.histogram_values = image.convert('RGB').histogram()
                self.histogram.queue_draw()
                self.canvas.queue_draw()
        def failed(error):
            self.preview_running = False
            if generation == self.preview_generation:
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
        self.apply_adjustments.set_sensitive(pending)
        if pending and not self.busy:
            self.undo_button.set_sensitive(True)
            self.lookup_action('undo').set_enabled(True)
        self.reset_adjustments.set_sensitive(pending)
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
