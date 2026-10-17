"""Native Save As dialog with format-specific options and named profiles."""
from i18n import tr
from pathlib import Path
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, Pango, GLib
from dialog_layout import StandardDialog
from copy import copy
from dataclasses import replace
from tempfile import TemporaryDirectory
from image_export import write_image
from editor_ui import preview_pixbuf
from ui_theme import card, label, accessible
from edit_controls import ChoiceButtons, SliderField
from resize_settings import ResizeSettings
from save_options import ALIASES, FORMAT_CHOICES, SaveSettings, SaveProfiles, filename_for_format


class SaveAsDialog(StandardDialog):
    def __init__(self, parent, settings, on_save):
        super().__init__(title='Bild exportieren', transient_for=parent, modal=True)
        self.set_titlebar(Gtk.Box())
        parent.set_scrim(True)
        self.on_save = on_save
        self.profiles = SaveProfiles()
        self.chooser = None
        self.checks = {}
        self.alive = True
        self.preview_serial = 0
        self.preview_timer = 0
        self.preview_busy = False
        self.initializing = True
        self.size_state = ResizeSettings(*parent.model.image.size)
        self.size_syncing = False
        self.add_button('Abbrechen', Gtk.ResponseType.CANCEL)
        self.save_button = self.add_button('Bild speichern', Gtk.ResponseType.ACCEPT)
        self.save_button.add_css_class('primary')
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        actions = self.save_button.get_parent()
        actions.set_margin_start(24)
        actions.set_margin_end(24)
        actions.set_margin_top(12)
        actions.set_margin_bottom(20)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=8, margin_bottom=8, margin_start=24, margin_end=24)
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(body)
        self.get_content_area().append(scroll)
        body.append(label('Bild exportieren', 'dialog-title'))
        path = parent.model.path
        width, height = parent.model.image.size
        summary = Gtk.Box(spacing=12)
        thumb = parent.model.image.copy()
        thumb.thumbnail((44,44))
        picture = Gtk.Picture.new_for_pixbuf(preview_pixbuf(thumb))
        picture.set_size_request(44,44)
        accessible(picture,'Vorschau des zu exportierenden Bildes')
        summary.append(picture)
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4,hexpand=True)
        name_label = label(path.name)
        name_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        name_label.set_max_width_chars(24)
        info.append(name_label)
        info.append(label(f'{width} × {height} px · aktuelle Seite','small muted'))
        summary.append(info)
        self.size_label = label('Berechnung …','small muted')
        self.size_label.set_tooltip_text(tr('Tatsächlich kodierte Dateigröße mit den gewählten Einstellungen'))
        summary.append(self.size_label)
        body.append(summary)
        layout = Gtk.Grid(column_spacing=16,row_spacing=12,hexpand=True)
        body.append(layout)
        formats = card('Format')
        self.format = ChoiceButtons(columns=5,hexpand=True)
        self.format.add_css_class('segmented-choice')
        accessible(self.format,'Ausgabeformat')
        for fmt, (_, title) in FORMAT_CHOICES.items():
            self.format.append(fmt, title)
        fmt = ALIASES.get(path.suffix.lower(), 'PNG')
        self.format.set_active_id(fmt)
        formats.append(self.format)
        layout.attach(formats,0,0,2,1)
        self.name = Gtk.Entry(text=path.stem+'-bearbeitet'+FORMAT_CHOICES[fmt][0],hexpand=True,activates_default=True)
        name_label.set_text(self.name.get_text())
        self.name.connect('changed',lambda entry:name_label.set_text(entry.get_text()))
        self.folder = Gtk.Entry(text=str(path.parent),hexpand=True,activates_default=True)
        self.quality_row = card()
        quality_heading = Gtk.Box(spacing=8)
        quality_heading.append(label('Qualität','section-title',hexpand=True))
        self.quality_value = label('95 %','numeric-value')
        quality_heading.append(self.quality_value)
        self.quality_row.append(quality_heading)
        self.quality = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,1,100,1)
        self.quality.set_draw_value(False)
        self.quality.set_digits(0)
        self.quality.set_value_pos(Gtk.PositionType.RIGHT)
        accessible(self.quality,'Exportqualität')
        self.quality.connect('value-changed',lambda scale:self.quality_value.set_text(tr(f'{round(scale.get_value())} %')))
        self.quality_row.append(self.quality)
        captions = Gtk.Box()
        captions.append(label('Kleinere Datei','small muted',hexpand=True))
        captions.append(label('Beste Qualität','small muted'))
        self.quality_row.append(captions)
        layout.attach(self.quality_row,0,1,1,1)
        resolution = card('Auflösung')
        row = Gtk.Box(spacing=8,homogeneous=True)
        self.resolution_tiles = {}
        group = None
        for key,title,subtitle in [('half','50 %',f'{max(1,round(width/2))} × {max(1,round(height/2))}'),
                                   ('full','100 %',f'{width} × {height}'),('custom','Eigene','Pixelmaße')]:
            tile = Gtk.ToggleButton()
            tile.add_css_class('choice')
            if group:
                tile.set_group(group)
            else:
                group = tile
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
            content.append(label(title))
            content.append(label(subtitle,'small muted',wrap=True))
            tile.set_child(content)
            accessible(tile,title+' · '+subtitle)
            tile.connect('toggled',self.resolution_changed,key)
            self.resolution_tiles[key] = tile
            row.append(tile)
        resolution.append(row)
        self.custom_size = Gtk.Box(spacing=8)
        self.custom_size.add_css_class('export-dimensions')
        for axis,title in [('width','Breite'),('height','Höhe')]:
            field = Gtk.SpinButton.new_with_range(1,80_000_000,1)
            field.set_hexpand(True)
            field.set_update_policy(Gtk.SpinButtonUpdatePolicy.ALWAYS)
            field.set_increments(1,10)
            field.set_tooltip_text(tr('Pfeiltasten: 1 px; Bild auf/ab: 10 px.'))
            accessible(field,title+' in Pixel')
            field.connect('value-changed',self.dimension_changed,axis)
            setattr(self,'output_'+axis,field)
            column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
            column.set_hexpand(True)
            column.append(label(title,'small muted'))
            measurement = Gtk.Box(spacing=6,hexpand=True)
            measurement.append(field)
            measurement.append(label('px','small muted unit-suffix'))
            column.append(measurement)
            self.custom_size.append(column)
            if axis=='width':
                link=Gtk.Image.new_from_icon_name('insert-link-symbolic')
                link.add_css_class('ratio-link-indicator')
                link.set_valign(Gtk.Align.CENTER)
                link.set_tooltip_text(tr('Seitenverhältnis bleibt erhalten'))
                accessible(link,'Breite und Höhe sind proportional verknüpft')
                self.custom_size.insert_child_after(link,column)
        resolution.append(self.custom_size)
        resolution.append(label('Seitenverhältnis bleibt erhalten.','small muted'))
        layout.attach(resolution,0,2,1,1)
        metadata = card()
        row = Gtk.Box(spacing=12)
        column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4,hexpand=True)
        column.append(label('Metadaten entfernen'))
        column.append(label('EXIF, Standort, Kommentare, Farbprofil','small muted',wrap=True))
        row.append(column)
        self.remove_metadata = Gtk.Switch(valign=Gtk.Align.CENTER)
        accessible(self.remove_metadata,'Alle Metadaten entfernen')
        self.remove_metadata.connect('notify::active',self.metadata_changed)
        row.append(self.remove_metadata)
        metadata.append(row)
        layout.attach(metadata,1,2,1,1)
        destination_card = card('Speicherziel')
        destination_card.set_spacing(16)
        self.destination_section = destination_card
        name_field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
        name_field.append(label('Dateiname','small muted'))
        name_field.append(accessible(self.name,'Dateiname'))
        destination_card.append(name_field)
        folder_field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
        folder_field.append(label('Zielordner','small muted'))
        folder_row = Gtk.Box(spacing=8)
        folder_row.append(accessible(self.folder,'Zielordner'))
        browse = Gtk.Button(label=tr('Wählen'))
        browse.connect('clicked',self.browse)
        folder_row.append(browse)
        folder_field.append(folder_row)
        destination_card.append(folder_field)
        self.folder.set_tooltip_text(self.folder.get_text())
        self.folder.connect('changed',lambda entry:entry.set_tooltip_text(entry.get_text()))
        layout.attach(destination_card,0,3,2,1)
        advanced = Gtk.Expander(label='Erweiterte Optionen & Profile')
        options = Gtk.Grid(column_spacing=16,row_spacing=12,margin_top=12,hexpand=True)
        advanced.set_child(options)
        body.append(advanced)
        self.stack = Gtk.Stack()
        options.attach(self.stack,0,0,1,2)
        jpeg = self.page('JPEG','JPEG-Optionen')
        self.check(jpeg,'progressive','Progressives JPEG')
        self.check(jpeg,'grayscale','Graustufen')
        self.check(jpeg,'chroma444','Volle Farbauflösung (4:4:4)')
        self.limit = Gtk.CheckButton(label=tr('Dateigröße begrenzen (KiB)'))
        jpeg.append(self.limit)
        self.target = Gtk.SpinButton.new_with_range(1,1_000_000,1)
        accessible(self.target,'Maximale JPEG-Dateigröße in KiB')
        self.target.set_value(65)
        target_row = Gtk.Box(spacing=6)
        target_row.append(self.target)
        target_row.append(label('KiB','small muted unit-suffix'))
        jpeg.append(target_row)
        gif = self.page('GIF','GIF-Optionen')
        self.check(gif,'gif_interlace','Interlaced speichern')
        self.check(gif,'gif_transparency','Transparenz beibehalten')
        gif.append(self.note('Maximal 256 Farben; Teiltransparenz wird auf Weiß reduziert.'))
        png = self.page('PNG','PNG-Optionen')
        png.append(label('Kompression: 0 = schnell, 9 = kleiner','small muted'))
        self.compression = SliderField(0,9,1,title='PNG-Kompression')
        accessible(self.compression,'PNG-Kompression')
        png.append(self.compression)
        webp = self.page('WEBP','WebP-Optionen')
        self.check(webp,'webp_lossless','Verlustfrei speichern')
        generic = self.page('other','Formatoptionen')
        generic.append(self.note('Standardoptionen für dieses Format.'))
        meta = card('Metadaten einzeln übernehmen')
        for key,title in [('keep_exif','EXIF-Daten'),('keep_icc','ICC-Farbprofil'),('keep_comment','Kommentar'),('keep_xmp','XMP-Daten')]:
            self.check(meta,key,title)
        meta.append(self.note('Nur vorhandene, vom Format unterstützte Daten. IPTC wird nicht übernommen.'))
        options.attach(meta,1,0,1,1)
        self.format_note = self.note('')
        options.attach(self.format_note,0,2,2,1)
        profiles = card('Profile')
        self.profile = Gtk.ComboBoxText.new_with_entry()
        self.profile.get_child().set_placeholder_text(tr('Profilname'))
        accessible(self.profile,'Exportprofil')
        profiles.append(self.profile)
        row = Gtk.Box(spacing=8,homogeneous=True)
        for title,callback in [('Laden',self.load_profile),('Speichern',self.save_profile),('Löschen',self.delete_profile)]:
            button = Gtk.Button(label=tr(title))
            button.connect('clicked',callback)
            row.append(button)
        profiles.append(row)
        options.attach(profiles,1,1,1,1)
        self.status = label('','error',wrap=True)
        body.append(self.status)
        self.reload_profiles()
        self.populate(settings)
        if self.profiles.error:
            self.status.set_text(tr(self.profiles.error))
        self.format.connect('changed',self.format_changed)
        self.limit.connect('toggled',lambda *_:self.target.set_sensitive(self.limit.get_active()))
        self.checks['grayscale'].connect('toggled',lambda *_:self.update_options())
        self.connect('response',self.on_response)
        self.connect('close-request',self.close_requested)
        for widget in [self.quality,self.compression,self.target]:
            widget.connect('value-changed',self.schedule_size)
        for widget in self.checks.values():
            widget.connect('toggled',self.schedule_size)
        self.limit.connect('toggled',self.schedule_size)
        self.initializing = False
        self.update_options()
        self.schedule_size()

    def resolution_changed(self, widget, key):
        if not widget.get_active() or not hasattr(self,'custom_size'):
            return
        self.custom_size.set_visible(key == 'custom')
        if key != 'custom':
            self.size_state.preset(50 if key == 'half' else 100)
        self.sync_size()

    def dimension_changed(self, widget, axis):
        if self.size_syncing:
            return
        self.size_state.set_dimension(axis,widget.get_value())
        self.sync_size()

    def sync_size(self):
        self.size_syncing = True
        self.output_width.set_value(self.size_state.width)
        self.output_height.set_value(self.size_state.height)
        self.size_syncing = False
        self.schedule_size()

    def metadata_changed(self, *_):
        self.update_options()
        self.schedule_size()

    def schedule_size(self, *_):
        if self.initializing or not self.alive:
            return
        self.preview_serial += 1
        if self.preview_timer:
            GLib.source_remove(self.preview_timer)
        self.preview_timer = GLib.timeout_add(350,self.calculate_size)
        self.size_label.set_text(tr('Berechnung …'))

    def calculate_size(self):
        self.preview_timer = 0
        if not self.alive:
            return False
        if self.preview_busy:
            self.preview_timer = GLib.timeout_add(350,self.calculate_size)
            return False
        try:
            settings = self.settings()
            self.status.set_text(tr(''))
            self.save_button.set_sensitive(True)
        except ValueError as error:
            self.status.set_text(tr(str(error)))
            self.size_label.set_text(tr('Ungültige Größe'))
            self.save_button.set_sensitive(False)
            return False
        parent = self.get_transient_for()
        snapshot = copy(parent.model)
        fmt = self.format.get_active_id()
        serial = self.preview_serial
        self.preview_busy = True
        def work():
            with TemporaryDirectory(prefix='bildblick-preview-') as temp:
                target = Path(temp)/('preview'+FORMAT_CHOICES[fmt][0])
                write_image(snapshot,target,fmt,settings)
                return target.stat().st_size
        def done(size):
            self.preview_busy = False
            if self.alive and serial == self.preview_serial:
                text = f'{size/1024/1024:.2f} MB' if size >= 1024*1024 else f'{size/1024:.1f} KB'
                self.size_label.set_text(text)
        def failed(error):
            self.preview_busy = False
            if self.alive and serial == self.preview_serial:
                self.size_label.set_text(tr('Nicht verfügbar'))
                self.status.set_text(tr(f'Export prüfen: {error}'))
        parent.submit(work,done,failed)
        return False

    def close_requested(self, *_):
        self.on_response(self,Gtk.ResponseType.CANCEL)
        return True

    @staticmethod
    def note(text):
        label = Gtk.Label(label=tr(text), xalign=0, wrap=True, max_width_chars=42)
        label.add_css_class('dim-label')
        return label

    def page(self, name, title):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        heading = Gtk.Label(label=tr(title), xalign=0)
        heading.add_css_class('heading')
        box.append(heading)
        self.stack.add_named(box, name)
        return box

    def check(self, box, key, text, tooltip=None):
        check = Gtk.CheckButton(label=tr(text))
        if tooltip:
            check.set_tooltip_text(tr(tooltip))
        self.checks[key] = check
        box.append(check)

    def populate(self, settings):
        for key, check in self.checks.items():
            check.set_active(getattr(settings, key))
        self.quality.set_value(settings.quality)
        self.quality_value.set_text(tr(f'{settings.quality} %'))
        self.compression.set_value(settings.png_compression)
        self.limit.set_active(settings.target_kib > 0)
        self.target.set_value(settings.target_kib or 65)
        self.target.set_sensitive(settings.target_kib > 0)
        self.remove_metadata.set_active(not any(getattr(settings,key) for key in ('keep_exif','keep_icc','keep_comment','keep_xmp')))
        if settings.output_width:
            self.size_state.width, self.size_state.height = settings.output_width, settings.output_height
            self.resolution_tiles['custom'].set_active(True)
        else:
            self.resolution_tiles['full'].set_active(True)
        self.sync_size()

    def settings(self):
        self.target.update()
        self.compression.update()
        values = {key: check.get_active() for key, check in self.checks.items()}
        if self.remove_metadata.get_active():
            values.update({key:False for key in ('keep_exif','keep_icc','keep_comment','keep_xmp')})
        width,height = self.size_state.dimensions()
        if self.resolution_tiles['full'].get_active():
            width,height = 0,0
        return SaveSettings(**values, output_width=width, output_height=height, quality=round(self.quality.get_value()),
                            png_compression=self.compression.get_value_as_int(),
                            target_kib=self.target.get_value_as_int() if self.limit.get_active() else 0)

    def format_changed(self, *_):
        try:
            self.name.set_text(filename_for_format(self.name.get_text(), self.format.get_active_id()))
        except ValueError:
            pass  # A blank name is validated when the user presses Save.
        self.update_options()
        self.schedule_size()

    def update_options(self):
        fmt = self.format.get_active_id()
        self.stack.set_visible_child_name(fmt if fmt in ('JPEG', 'PNG', 'GIF', 'WEBP') else 'other')
        self.quality_row.set_visible(fmt in ('JPEG', 'WEBP'))
        for key, formats in {'keep_exif': ('JPEG', 'PNG', 'WEBP'),
                             'keep_icc': ('JPEG', 'PNG', 'WEBP', 'TIFF', 'PDF'),
                             'keep_comment': ('JPEG', 'GIF'), 'keep_xmp': ('JPEG', 'WEBP')}.items():
            self.checks[key].set_sensitive(not self.remove_metadata.get_active() and fmt in formats and not (
                key == 'keep_icc' and fmt == 'JPEG' and self.checks['grayscale'].get_active()))
        notes = {'JPEG': 'JPEG wird neu kodiert. Transparente Bereiche erhalten einen weißen Hintergrund.',
                 'ICO': 'ICO wird auf die unterstützten Icon-Größen verkleinert.',
                 'GIF': 'Speichert nur die aktuelle Seite. Für Animationen: Datei → Alle Seiten exportieren.'}
        self.format_note.set_text(tr(notes.get(fmt, 'Speichert die aktuelle Seite. Optionen verändern das Bild im Editor nicht.')))

    def browse(self, *_):
        if self.chooser:
            self.chooser.show()
            return
        chooser = Gtk.FileChooserNative.new('Zielordner wählen', self,
                    Gtk.FileChooserAction.SELECT_FOLDER, 'Auswählen', 'Abbrechen')
        self.chooser = chooser
        chooser.set_modal(True)
        folder = Path(self.folder.get_text()).expanduser()
        if folder.is_dir():
            chooser.set_current_folder(Gio.File.new_for_path(str(folder.absolute())))
        def chosen(dialog, answer):
            file = dialog.get_file() if answer == Gtk.ResponseType.ACCEPT else None
            if file and file.get_path():
                self.folder.set_text(file.get_path())
            dialog.destroy()
            self.chooser = None
        chooser.connect('response', chosen)
        chooser.show()

    def reload_profiles(self, name=''):
        self.profile.remove_all()
        for key in sorted(self.profiles.profiles):
            self.profile.append_text(key)
        self.profile.get_child().set_text(name)

    def profile_name(self):
        return self.profile.get_child().get_text().strip()

    def load_profile(self, *_):
        try:
            fmt, settings = self.profiles.load(self.profile_name())
            self.populate(settings)
            self.format.set_active_id(fmt)
            self.update_options()
            self.status.set_text(tr('Profil geladen.'))
        except KeyError:
            self.status.set_text(tr('Bitte ein vorhandenes Profil wählen.'))

    def save_profile(self, *_):
        name = self.profile_name()
        try:
            self.profiles.save(name, self.format.get_active_id(), self.settings())
            self.reload_profiles(name)
            self.status.set_text(tr('Profil gespeichert.'))
        except (OSError, ValueError) as error:
            self.status.set_text(tr(str(error)))

    def delete_profile(self, *_):
        try:
            self.profiles.delete(self.profile_name())
            self.reload_profiles()
            self.status.set_text(tr('Profil gelöscht.'))
        except KeyError:
            self.status.set_text(tr('Bitte ein vorhandenes Profil wählen.'))
        except (OSError, ValueError) as error:
            self.status.set_text(tr(str(error)))

    def on_response(self, _dialog, answer):
        if answer == Gtk.ResponseType.ACCEPT:
            try:
                name = filename_for_format(self.name.get_text(), self.format.get_active_id())
                self.name.set_text(name)
                folder = Path(self.folder.get_text().strip()).expanduser()
                if not self.folder.get_text().strip() or not folder.is_absolute() or not folder.is_dir():
                    raise ValueError('Bitte einen vorhandenen Zielordner mit vollständigem Pfad wählen.')
                settings = self.settings()
            except (ValueError, OSError) as error:
                self.status.set_text(tr(str(error)))
                return
            self.on_save(folder / name, settings)
        self.alive = False
        if self.preview_timer:
            GLib.source_remove(self.preview_timer)
            self.preview_timer = 0
        if self.chooser:
            self.chooser.destroy()
        parent = self.get_transient_for()
        parent.set_scrim(False)
        if self in parent.dialogs:
            parent.dialogs.remove(self)
        self.destroy()
