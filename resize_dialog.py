"""Pixel/percentage resize dialog with two-way aspect-ratio locking."""
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk
from dialog_layout import StandardDialog
from resize_settings import ResizeSettings
from image_tools import to_pixels
from ui_theme import card, label, accessible
from edit_controls import ChoiceButtons


class ResizeDialog(StandardDialog):
    def __init__(self,parent,on_apply):
        super().__init__(title='Größe ändern',transient_for=parent,modal=True)
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
        body.append(label(f'Original: {self.settings.width} × {self.settings.height} Pixel','muted'))
        self.summary = label('', 'section-title', wrap=True)
        body.append(self.summary)
        def field(section, title, widget, column=0, row=0, width=1):
            group=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
            group.append(label(title)); group.append(widget)
            section.attach(group,column,row,width,1)
        section = card('Abmessungen'); section.set_spacing(16); body.append(section)
        dimensions = Gtk.Grid(column_spacing=12,row_spacing=10,hexpand=True)
        section.append(dimensions)
        self.units = ChoiceButtons()
        for key,title in [('pixels','Pixel'),('percent','Prozent'),('cm','Zentimeter'),('inch','Zoll')]:
            self.units.append(key,title)
        self.units.set_active_id('pixels'); field(dimensions,'Einheit',self.units,0,0,2)
        self.width = Gtk.SpinButton.new_with_range(1,80_000_000,1)
        self.height = Gtk.SpinButton.new_with_range(1,80_000_000,1)
        for column,(title,widget,axis) in enumerate([('Breite',self.width,'width'),('Höhe',self.height,'height')]):
            accessible(widget,title+' des Bildes'); widget.set_hexpand(True)
            widget.set_numeric(True); widget.set_activates_default(True)
            widget.connect('value-changed',self.dimension_changed,axis); field(dimensions,title,widget,column,1)
        self.lock = Gtk.CheckButton(label='Seitenverhältnis beibehalten',active=True)
        self.lock.connect('toggled',self.lock_changed); dimensions.attach(self.lock,0,2,2,1)
        presets=Gtk.Box(spacing=8,homogeneous=True)
        for amount in (25,50,100,200):
            button=Gtk.Button(label=f'{amount} %')
            button.connect('clicked',lambda _button,p=amount:self.use_preset(p)); presets.append(button)
        field(dimensions,'Schnelle Größenänderung',presets,0,3,2)
        calculation=card('Berechnung'); calculation.set_spacing(16); body.append(calculation)
        calculation_grid=Gtk.Grid(column_spacing=12,row_spacing=8,hexpand=True)
        calculation.append(calculation_grid)
        self.method = ChoiceButtons()
        for ident,title in [('lanczos','Lanczos'),('bicubic','Bikubisch'),('bilinear','Bilinear'),('nearest','Pixelgrafik')]:
            self.method.append(ident,title)
        self.method.set_active_id('lanczos'); field(calculation_grid,'Interpolation',self.method,0,0)
        self.dpi=Gtk.SpinButton.new_with_range(1,9600,1)
        accessible(self.dpi,'DPI – Druckauflösung'); self.dpi.set_value(parent.model.dpi)
        self.dpi.connect('value-changed',lambda *_:self.sync_fields())
        field(calculation_grid,'DPI (Druckauflösung)',self.dpi,1,0)
        calculation_grid.attach(label('DPI allein ändert keine Pixel und erzeugt keine zusätzlichen Details.','small muted',wrap=True),0,1,2,1)
        sizes=card('Größenvorgaben'); body.append(sizes)
        self.resolution=ChoiceButtons(columns=3); self.resolution.append('none','Keine Vorgabe')
        for w,h in ((640,480),(800,600),(1024,768),(1280,720),(1920,1080),(3840,2160)):
            self.resolution.append(f'{w}x{h}',f'{w} × {h}')
        self.resolution.append('screen','Bildschirmgröße'); self.resolution.set_active_id('none')
        self.resolution.connect('changed',self.resolution_changed); sizes.append(self.resolution)
        sizes.append(label('Mit gesperrtem Seitenverhältnis wird das Bild in die gewählte Größe eingepasst.','small muted',wrap=True))
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
            self.summary.remove_css_class('error')
            self.summary.set_text(f'Neue Größe: {width} × {height} Pixel  ·  {width*height/1_000_000:.2f} Megapixel')
            self.apply_button.set_sensitive(True)
        except ValueError as error:
            self.summary.add_css_class('error')
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
