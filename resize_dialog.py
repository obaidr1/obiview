"""Pixel/percentage resize dialog with two-way aspect-ratio locking."""
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk
from resize_settings import ResizeSettings
from ui_theme import card, label, accessible


class ResizeDialog(Gtk.Dialog):
    def __init__(self,parent,on_apply):
        super().__init__(title='Größe ändern',transient_for=parent,modal=True,default_width=500,default_height=620)
        parent.set_scrim(True)
        self.settings = ResizeSettings(*parent.model.image.size)
        self.on_apply = on_apply
        self.syncing = False
        self.percent = False
        self.add_button('Abbrechen',Gtk.ResponseType.CANCEL)
        self.apply_button = self.add_button('Größe ändern',Gtk.ResponseType.ACCEPT)
        self.apply_button.add_css_class('suggested-action')
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16,
                       margin_top=8,margin_bottom=16,margin_start=24,margin_end=24)
        body.append(label('Größe ändern','dialog-title'))
        body.append(label('Mehr Platz für Details. Oder weniger Dateigröße.','muted',wrap=True))
        section = card('Abmessungen')
        grid = Gtk.Grid(column_spacing=16,row_spacing=14)
        section.append(grid)
        body.append(section)
        grid.attach(Gtk.Label(label=f'Original: {self.settings.width} × {self.settings.height} Pixel',xalign=0),0,0,2,1)
        self.units = Gtk.ComboBoxText()
        self.units.append('pixels','Pixel')
        self.units.append('percent','Prozent')
        self.units.set_active_id('pixels')
        grid.attach(Gtk.Label(label='Einheit',xalign=0),0,1,1,1)
        grid.attach(self.units,1,1,1,1)
        self.width = Gtk.SpinButton.new_with_range(1,80_000_000,1)
        self.height = Gtk.SpinButton.new_with_range(1,80_000_000,1)
        for row,(title,widget,axis) in enumerate((('Breite',self.width,'width'),('Höhe',self.height,'height')),2):
            accessible(widget,title+' des Bildes')
            widget.set_hexpand(True)
            widget.set_numeric(True)
            widget.set_activates_default(True)
            widget.connect('value-changed',self.dimension_changed,axis)
            grid.attach(Gtk.Label(label=title,xalign=0),0,row,1,1)
            grid.attach(widget,1,row,1,1)
        self.lock = Gtk.CheckButton(label='Seitenverhältnis beibehalten',active=True)
        self.lock.connect('toggled',self.lock_changed)
        grid.attach(self.lock,0,4,2,1)
        presets = Gtk.Box(spacing=8,homogeneous=True)
        for amount in (25,50,100,200):
            button = Gtk.Button(label=f'{amount} %')
            button.connect('clicked',lambda _button,p=amount:self.use_preset(p))
            presets.append(button)
        grid.attach(presets,0,5,2,1)
        self.method = Gtk.ComboBoxText()
        for ident,title in [('lanczos','Lanczos – hohe Qualität'),('bicubic','Bikubisch'),
                            ('bilinear','Bilinear'),('nearest','Nächster Nachbar – Pixelgrafik')]:
            self.method.append(ident,title)
        self.method.set_active_id('lanczos')
        grid.attach(Gtk.Label(label='Interpolation',xalign=0),0,6,1,1)
        grid.attach(self.method,1,6,1,1)
        self.summary = Gtk.Label(xalign=0,wrap=True)
        grid.attach(self.summary,0,7,2,1)
        note = Gtk.Label(label='Ändert die Bildpixel. Die Originaldatei bleibt bis zum Speichern unverändert.',
                         xalign=0,wrap=True,max_width_chars=55)
        note.add_css_class('dim-label')
        grid.attach(note,0,8,2,1)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(body)
        self.get_content_area().append(scroll)
        self.units.connect('changed',self.unit_changed)
        self.connect('response',self.on_response)
        self.connect('close-request',lambda *_:(self.on_response(self,Gtk.ResponseType.CANCEL),True)[1])
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
        parent.set_scrim(False)
        if self in parent.dialogs:
            parent.dialogs.remove(self)
        self.destroy()
