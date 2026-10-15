"""Pixel/percentage resize dialog with two-way aspect-ratio locking."""
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk
from resize_settings import ResizeSettings
from image_tools import to_pixels
from ui_theme import card, label, accessible


class ResizeDialog(Gtk.Dialog):
    def __init__(self,parent,on_apply):
        super().__init__(title='Größe ändern',transient_for=parent,modal=True,default_width=500,default_height=760)
        self.set_titlebar(Gtk.Box())
        parent.set_scrim(True)
        self.settings = ResizeSettings(*parent.model.image.size)
        self.on_apply = on_apply
        self.syncing = False
        self.percent = False
        self.add_button('Abbrechen',Gtk.ResponseType.CANCEL)
        self.apply_button = self.add_button('Größe ändern',Gtk.ResponseType.ACCEPT)
        self.apply_button.add_css_class('suggested-action')
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        actions = self.apply_button.get_parent()
        actions.set_margin_start(24)
        actions.set_margin_end(24)
        actions.set_margin_top(12)
        actions.set_margin_bottom(20)
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
        self.units.append('cm','Zentimeter')
        self.units.append('inch','Zoll')
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
        self.dpi = Gtk.SpinButton.new_with_range(1,9600,1)
        self.dpi.set_value(parent.model.dpi)
        self.dpi.connect('value-changed',lambda *_:self.sync_fields())
        grid.attach(Gtk.Label(label='DPI (Druckauflösung)',xalign=0),0,8,1,1)
        grid.attach(self.dpi,1,8,1,1)
        self.resolution = Gtk.ComboBoxText()
        self.resolution.append('none','Auflösung wählen …')
        for w,h in ((640,480),(800,600),(1024,768),(1280,720),(1920,1080),(3840,2160)):
            self.resolution.append(f'{w}x{h}',f'{w} × {h}')
        self.resolution.append('screen','Bildschirmgröße')
        self.resolution.set_active_id('none')
        self.resolution.connect('changed',self.resolution_changed)
        grid.attach(Gtk.Label(label='Größenvorgabe',xalign=0),0,9,1,1)
        grid.attach(self.resolution,1,9,1,1)
        note = Gtk.Label(label='50 % = halb, 200 % = doppelt. Gesperrtes Verhältnis passt in die Größenvorgabe. DPI allein ändert keine Pixel und erzeugt keine zusätzlichen Details.',
                         xalign=0,wrap=True,max_width_chars=55)
        note.add_css_class('dim-label')
        grid.attach(note,0,10,2,1)
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
        unit = self.units.get_active_id()
        value = widget.get_value()
        if unit in ('cm','inch'):
            value = to_pixels(value,unit,self.dpi.get_value())
        pixels = max(1,round(value*self.settings.original[0 if axis=='width' else 1]/100)) if self.percent else max(1,round(value))
        if pixels == getattr(self.settings,axis):
            return
        self.settings.set_dimension(axis,value,self.percent)
        self.sync_fields()

    def sync_fields(self):
        self.syncing = True
        try:
            unit = self.units.get_active_id()
            factor = self.dpi.get_value()/2.54 if unit=='cm' else self.dpi.get_value() if unit=='inch' else 1
            fractional = self.percent or unit in ('cm','inch')
            for widget,value in zip((self.width,self.height),self.settings.values(self.percent)):
                value /= factor
                widget.set_digits(3 if unit in ('cm','inch') else 2 if self.percent else 0)
                widget.set_range(.001 if fractional else 1,8_000_000_000 if self.percent else 80_000_000)
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

    def resolution_changed(self,widget):
        ident = widget.get_active_id()
        if ident == 'none': return
        if ident=='screen':
            parent=self.get_transient_for()
            monitor=parent.get_display().get_monitor_at_surface(parent.get_surface())
            geometry=monitor.get_geometry()
            width,height=geometry.width,geometry.height
        else:
            width,height = map(int,ident.split('x'))
        if self.settings.locked:
            factor = min(width/self.settings.original[0],height/self.settings.original[1])
            self.settings.preset(factor*100)
        else:
            self.settings.width,self.settings.height = width,height
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
            self.dpi.update()
            self.on_apply(width,height,self.method.get_active_id(),self.dpi.get_value())
        parent = self.get_transient_for()
        parent.set_scrim(False)
        if self in parent.dialogs:
            parent.dialogs.remove(self)
        self.destroy()
