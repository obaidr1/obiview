"""Pixel/percentage resize dialog with two-way aspect-ratio locking."""
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk
from resize_settings import ResizeSettings


class ResizeDialog(Gtk.Dialog):
    def __init__(self,parent,on_apply):
        super().__init__(title='Größe ändern',transient_for=parent,modal=True,resizable=False)
        self.settings = ResizeSettings(*parent.model.image.size)
        self.on_apply = on_apply
        self.syncing = False
        self.percent = False
        self.add_button('Abbrechen',Gtk.ResponseType.CANCEL)
        self.apply_button = self.add_button('Größe ändern',Gtk.ResponseType.ACCEPT)
        self.apply_button.add_css_class('suggested-action')
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        grid = Gtk.Grid(column_spacing=16,row_spacing=12,margin_top=20,margin_bottom=20,margin_start=20,margin_end=20)
        grid.attach(Gtk.Label(label=f'Original: {self.settings.width} × {self.settings.height} Pixel',xalign=0),0,0,2,1)
        self.units = Gtk.ComboBoxText()
        self.units.append('pixels','Pixel')
        self.units.append('percent','Prozent')
        self.units.set_active_id('pixels')
        grid.attach(Gtk.Label(label='Einheit',xalign=0),0,1,1,1)
        grid.attach(self.units,1,1,1,1)
        self.width = Gtk.SpinButton.new_with_range(1,80_000_000,1)
        self.height = Gtk.SpinButton.new_with_range(1,80_000_000,1)
        for row,(label,widget,axis) in enumerate((('Breite',self.width,'width'),('Höhe',self.height,'height')),2):
            widget.set_numeric(True)
            widget.set_activates_default(True)
            widget.connect('value-changed',self.dimension_changed,axis)
            grid.attach(Gtk.Label(label=label,xalign=0),0,row,1,1)
            grid.attach(widget,1,row,1,1)
        self.lock = Gtk.CheckButton(label='Seitenverhältnis beibehalten',active=True)
        self.lock.connect('toggled',self.lock_changed)
        grid.attach(self.lock,0,4,2,1)
        presets = Gtk.Box(spacing=4)
        for amount in (25,50,75,100,150,200):
            button = Gtk.Button(label=f'{amount} %')
            button.connect('clicked',lambda _button,p=amount:self.use_preset(p))
            presets.append(button)
        grid.attach(presets,0,5,2,1)
        self.method = Gtk.ComboBoxText()
        for ident,label in [('lanczos','Lanczos – hohe Qualität'),('bicubic','Bikubisch'),
                            ('bilinear','Bilinear'),('nearest','Nächster Nachbar – Pixelgrafik')]:
            self.method.append(ident,label)
        self.method.set_active_id('lanczos')
        grid.attach(Gtk.Label(label='Interpolation',xalign=0),0,6,1,1)
        grid.attach(self.method,1,6,1,1)
        self.summary = Gtk.Label(xalign=0,wrap=True)
        grid.attach(self.summary,0,7,2,1)
        note = Gtk.Label(label='Ändert die Bildpixel. Die Originaldatei bleibt bis zum Speichern unverändert.',
                         xalign=0,wrap=True,max_width_chars=55)
        note.add_css_class('dim-label')
        grid.attach(note,0,8,2,1)
        self.get_content_area().append(grid)
        self.units.connect('changed',self.unit_changed)
        self.connect('response',self.on_response)
        self.sync_fields()

    def dimension_changed(self,widget,axis):
        if self.syncing:
            return
        self.settings.set_dimension(axis,widget.get_value(),self.percent)
        self.sync_fields()

    def sync_fields(self):
        self.syncing = True
        try:
            for widget,value in zip((self.width,self.height),self.settings.values(self.percent)):
                widget.set_digits(2 if self.percent else 0)
                widget.set_range(.01 if self.percent else 1,8_000_000_000 if self.percent else 80_000_000)
                widget.set_increments(1,10)
                widget.set_value(value)
        finally:
            self.syncing = False
        try:
            width,height = self.settings.dimensions()
            self.summary.set_text(f'Neue Größe: {width} × {height} Pixel  ·  {width*height/1_000_000:.2f} Megapixel')
            self.apply_button.set_sensitive(True)
        except ValueError as error:
            self.summary.set_text(str(error))
            self.apply_button.set_sensitive(False)

    def unit_changed(self,_widget):
        self.percent = self.units.get_active_id()=='percent'
        self.sync_fields()

    def lock_changed(self,widget):
        self.settings.set_locked(widget.get_active())
        self.sync_fields()

    def use_preset(self,amount):
        self.settings.preset(amount)
        self.sync_fields()

    def on_response(self,_dialog,answer):
        if answer==Gtk.ResponseType.ACCEPT:
            # Commit typed numeric text even when focus has not left the field.
            self.width.update()
            self.height.update()
            try:
                width,height = self.settings.dimensions()
            except ValueError as error:
                self.summary.set_text(str(error))
                return
            self.on_apply(width,height,self.method.get_active_id())
        parent = self.get_transient_for()
        if self in parent.dialogs:
            parent.dialogs.remove(self)
        self.destroy()
