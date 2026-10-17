"""Pixel/percentage resize dialog with two-way aspect-ratio locking."""
from i18n import tr
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from PIL import Image
from dialog_layout import StandardDialog
from resize_settings import ResizeSettings
from image_tools import to_pixels
from ui_theme import card, label, accessible, preview_surface, ratio_link_state
from edit_controls import ChoiceButtons


class ResizeDialog(StandardDialog):
    PRESETS = (
        ('Eigene Größe', None), ('25 %', ('percent',25)), ('50 %', ('percent',50)),
        ('100 %', ('percent',100)), ('200 %', ('percent',200)),
        ('Full HD · 1920 × 1080', ('size',1920,1080)),
        ('QHD · 2560 × 1440', ('size',2560,1440)),
        ('4K UHD · 3840 × 2160', ('size',3840,2160)),
        ('Quadratisch · 1080 × 1080', ('size',1080,1080)),
        ('Story · 1080 × 1920', ('size',1080,1920)),
        ('Bildschirmgröße', ('screen',)),
    )

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

        # Use the StandardDialog body directly so its single outer scroller owns
        # overflow and the persistent action row never covers the last control.
        body = self.body
        body.set_spacing(12)
        body.append(label('Größe ändern','dialog-title'))

        summary_row = Gtk.Box(spacing=14,hexpand=True)
        preview_box = Gtk.Box(width_request=184,height_request=120,
                              halign=Gtk.Align.CENTER,valign=Gtk.Align.CENTER)
        self.preview_picture = Gtk.Picture(can_shrink=True,halign=Gtk.Align.CENTER,
                                           valign=Gtk.Align.CENTER)
        preview_surface(self.preview_picture)
        preview_box.append(self.preview_picture)
        summary_row.append(preview_box)
        summary_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5,
                               valign=Gtk.Align.CENTER,hexpand=True)
        summary_text.append(label(f'Original · {self.settings.width} × {self.settings.height} px','small muted'))
        self.summary = label('', 'section-title', wrap=True)
        summary_text.append(self.summary)
        summary_row.append(summary_text)
        body.append(summary_row)

        dimensions = card('Abmessungen')
        dimensions.set_spacing(12)
        body.append(dimensions)

        unit_field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5)
        unit_field.append(label('Einheit','small muted'))
        self.units = ChoiceButtons(columns=4,hexpand=True)
        self.units.add_css_class('segmented-choice')
        for key,title in [('pixels','Pixel'),('percent','Prozent'),('cm','cm'),('inch','Zoll')]:
            self.units.append(key,title)
        self.units.set_active_id('pixels')
        unit_field.append(self.units)
        dimensions.append(unit_field)

        dimension_grid = Gtk.Grid(column_spacing=8,row_spacing=4,hexpand=True)
        dimension_grid.set_column_homogeneous(False)
        dimensions.append(dimension_grid)
        self.width, width_field = self.dimension_field('Breite','width')
        self.height, height_field = self.dimension_field('Höhe','height')
        dimension_grid.attach(width_field,0,0,1,1)

        self.ratio_button = Gtk.ToggleButton(child=Gtk.Image.new_from_icon_name('insert-link-symbolic'),
                                               active=True,valign=Gtk.Align.CENTER)
        self.ratio_button.add_css_class('ratio-link')
        self.ratio_button.set_tooltip_text(tr('Seitenverhältnis beibehalten'))
        accessible(self.ratio_button,'Seitenverhältnis beibehalten')
        self.ratio_button.connect('toggled',self.lock_changed)
        dimension_grid.attach(self.ratio_button,1,0,1,1)
        dimension_grid.attach(height_field,2,0,1,1)

        preset_row = Gtk.Box(spacing=12,hexpand=True)
        preset_row.append(label('Vorgabe','small muted'))
        self.preset = Gtk.DropDown.new_from_strings([tr(title) for title,_spec in self.PRESETS])
        self.preset.set_hexpand(True)
        self.preset.set_selected(0)
        accessible(self.preset,'Größenvorgabe')
        self.preset.connect('notify::selected',self.preset_changed)
        preset_row.append(self.preset)
        dimensions.append(preset_row)

        self.advanced = Gtk.Expander(label='Erweiterte Einstellungen')
        advanced_grid = Gtk.Grid(column_spacing=16,row_spacing=8,hexpand=True,
                                 margin_top=8)
        self.advanced.set_child(advanced_grid)
        self.method_field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5)
        self.method_field.append(label('Interpolation','small muted'))
        self.method = ChoiceButtons(columns=2,hexpand=True)
        self.method.add_css_class('segmented-choice')
        for ident,title in [('lanczos','Lanczos'),('bicubic','Bikubisch'),
                            ('bilinear','Bilinear'),('nearest','Pixelgrafik')]:
            self.method.append(ident,title)
        self.method.set_active_id('lanczos')
        self.method_field.append(self.method)
        advanced_grid.attach(self.method_field,0,0,1,1)
        dpi_field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5)
        dpi_field.append(label('DPI · Druckauflösung','small muted'))
        self.dpi = Gtk.SpinButton.new_with_range(1,9600,1)
        self.dpi.set_hexpand(True)
        self.dpi.set_update_policy(Gtk.SpinButtonUpdatePolicy.ALWAYS)
        self.dpi.set_value(parent.model.dpi)
        self.dpi.set_tooltip_text(tr('Pfeiltasten: 1 DPI · Bild auf/ab: 10 DPI'))
        accessible(self.dpi,'DPI – Druckauflösung')
        self.dpi.connect('value-changed',lambda *_:self.sync_fields())
        dpi_row = Gtk.Box(spacing=6)
        dpi_row.append(self.dpi)
        dpi_row.append(label('DPI','small muted unit-suffix'))
        dpi_field.append(dpi_row)
        advanced_grid.attach(dpi_field,0,1,2,1)
        advanced_grid.attach(label('DPI allein ändert keine Pixel und erzeugt keine zusätzlichen Details.','small muted',wrap=True),0,2,2,1)
        body.append(self.advanced)

        # Keep a reference to the model image; resize directly to the small
        # display preview rather than copying a potentially huge source image.
        self.source_image = parent.model.image

        self.units.connect('changed',self.unit_changed)
        self.connect('response',self.on_response)
        self.connect('close-request',lambda *_:(self.on_response(self,Gtk.ResponseType.CANCEL),True)[1])
        self.sync_fields()

    def dimension_field(self,title,axis):
        group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5,hexpand=True)
        group.append(label(title,'small muted'))
        row = Gtk.Box(spacing=6,hexpand=True)
        widget = Gtk.SpinButton.new_with_range(1,80_000_000,1)
        widget.set_hexpand(True)
        widget.set_numeric(True)
        widget.set_update_policy(Gtk.SpinButtonUpdatePolicy.ALWAYS)
        widget.set_snap_to_ticks(False)
        widget.set_activates_default(True)
        widget.set_alignment(0.0)
        widget.add_css_class('left-aligned')
        widget.set_increments(1,10)
        widget.set_tooltip_text(tr('Pfeiltasten: 1; Bild auf/ab: 10.'))
        accessible(widget,title+' des Bildes')
        widget.connect('value-changed',self.dimension_changed,axis)
        suffix = label('px','small muted')
        suffix.add_css_class('unit-suffix')
        row.append(widget); row.append(suffix)
        group.append(row)
        setattr(self,axis+'_unit',suffix)
        return widget,group

    def dimension_changed(self,widget,axis):
        if self.syncing:
            return
        unit = self.units.get_active_id()
        value = widget.get_value()
        if unit in ('cm','inch'):
            value = to_pixels(value,unit,self.dpi.get_value())
        self.settings.set_dimension(axis,value,self.percent)
        self.sync_fields(custom=True)

    def sync_fields(self,custom=False):
        self.syncing = True
        try:
            unit = self.units.get_active_id()
            factor = self.dpi.get_value()/2.54 if unit=='cm' else self.dpi.get_value() if unit=='inch' else 1
            fractional = self.percent or unit in ('cm','inch')
            suffix = {'pixels':'px','percent':'%','cm':'cm','inch':'in'}[unit]
            for axis,value in zip(('width','height'),self.settings.values(self.percent)):
                widget=getattr(self,axis)
                widget.set_alignment(0.0)
                widget.set_digits(3 if unit in ('cm','inch') else 2 if self.percent else 0)
                widget.set_snap_to_ticks(False)
                widget.set_range(.001 if fractional else 1,8_000_000_000 if self.percent else 80_000_000)
                steps={'pixels':(1,10),'percent':(.1,1),'cm':(.01,.1),'inch':(.01,.1)}[unit]
                widget.set_increments(*steps)
                step_text=f'{steps[0]:g} {suffix}'
                page_text=f'{steps[1]:g} {suffix}'
                widget.set_tooltip_text(tr(f'Pfeiltasten: {step_text}; Bild auf/ab: {page_text}.'))
                widget.set_value(value/factor)
                getattr(self,axis+'_unit').set_text(suffix)
            if custom and self.preset.get_selected()!=0:
                self.preset.set_selected(0)
        finally:
            self.syncing = False
        try:
            width,height = self.settings.dimensions()
            self.summary.remove_css_class('error')
            self.summary.set_text(tr(f'Neue Größe · {width} × {height} px  ·  {width*height/1_000_000:.2f} MP'))
            self.apply_button.set_sensitive(True)
            ratio=width/height
            pw,ph=(160,round(160/ratio)) if ratio>=1 else (round(112*ratio),112)
            pw,ph=max(1,pw),max(1,ph)
            resized=self.source_image.resize((pw,ph),Image.Resampling.LANCZOS).convert('RGBA')
            pixbuf=GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(resized.tobytes()),
                GdkPixbuf.Colorspace.RGB,True,8,pw,ph,pw*4)
            self.preview_picture.set_pixbuf(pixbuf)
            self.preview_picture.set_size_request(pw,ph)
        except ValueError as error:
            self.summary.add_css_class('error')
            self.summary.set_text(tr(str(error)))
            self.apply_button.set_sensitive(False)

    def unit_changed(self,_widget):
        self.percent = self.units.get_active_id()=='percent'
        self.sync_fields(custom=True)

    def lock_changed(self,widget):
        self.settings.set_locked(widget.get_active())
        ratio_link_state(widget)
        self.sync_fields(custom=True)

    def preset_changed(self,widget,_pspec):
        if self.syncing:
            return
        index=widget.get_selected()
        if index<=0 or index>=len(self.PRESETS):
            return
        spec=self.PRESETS[index][1]
        if spec[0]=='percent':
            self.settings.preset(spec[1])
        elif spec[0]=='size':
            width,height=spec[1:]
            if self.settings.locked:
                self.settings.preset(min(width/self.settings.original[0],height/self.settings.original[1])*100)
            else:
                self.settings.width,self.settings.height=width,height
        elif spec[0]=='screen':
            parent=self.get_transient_for()
            monitor=parent.get_display().get_monitor_at_surface(parent.get_surface())
            geometry=monitor.get_geometry()
            if self.settings.locked:
                self.settings.preset(min(geometry.width/self.settings.original[0],
                                         geometry.height/self.settings.original[1])*100)
            else:
                self.settings.width,self.settings.height=geometry.width,geometry.height
        self.sync_fields()

    def on_response(self,_dialog,answer):
        if answer==Gtk.ResponseType.ACCEPT:
            try:
                width,height=self.settings.dimensions()
            except ValueError as error:
                self.summary.set_text(tr(str(error)))
                return
            self.on_apply(width,height,self.method.get_active_id(),self.dpi.get_value())
        parent=self.get_transient_for()
        parent.set_scrim(False)
        if self in parent.dialogs:
            parent.dialogs.remove(self)
        self.destroy()
