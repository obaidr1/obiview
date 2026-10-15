"""Native Save As dialog with format-specific options and named profiles."""
from pathlib import Path
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, Pango
from save_options import ALIASES, FORMAT_CHOICES, SaveSettings, SaveProfiles, filename_for_format


class SaveAsDialog(Gtk.Dialog):
    def __init__(self, parent, settings, on_save):
        super().__init__(title='Speichern unter', transient_for=parent, modal=True,
                         default_width=760, default_height=660)
        self.on_save = on_save
        self.profiles = SaveProfiles()
        self.chooser = None
        self.checks = {}
        self.add_button('Abbrechen', Gtk.ResponseType.CANCEL)
        button = self.add_button('Speichern', Gtk.ResponseType.ACCEPT)
        button.add_css_class('suggested-action')
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                       margin_top=16, margin_bottom=16, margin_start=18, margin_end=18)
        scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(body)
        self.get_content_area().append(scroll)
        path = parent.model.path
        width, height = parent.model.image.size
        info = Gtk.Label(label=f'{path.name}  ·  {width} × {height} Pixel  ·  aktuelle Seite', xalign=0)
        info.set_ellipsize(Pango.EllipsizeMode.END)
        body.append(info)
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        body.append(grid)
        self.name = Gtk.Entry(hexpand=True, activates_default=True)
        self.folder = Gtk.Entry(text=str(path.parent), hexpand=True, activates_default=True)
        browse = Gtk.Button(label='Durchsuchen …')
        browse.connect('clicked', self.browse)
        self.format = Gtk.ComboBoxText(hexpand=True)
        for fmt, (_, label) in FORMAT_CHOICES.items():
            self.format.append(fmt, label)
        fmt = ALIASES.get(path.suffix.lower(), 'PNG')
        self.format.set_active_id(fmt)
        self.name.set_text(path.stem + '-bearbeitet' + FORMAT_CHOICES[fmt][0])
        for row, (title, widget) in enumerate((('Dateiname', self.name), ('Zielordner', self.folder), ('Dateityp', self.format))):
            grid.attach(Gtk.Label(label=title, xalign=0), 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)
        grid.attach(browse, 2, 1, 1, 1)
        columns = Gtk.Box(spacing=18, homogeneous=True)
        body.append(columns)
        self.format_options = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        columns.append(self.format_options)
        quality_row = Gtk.Box(spacing=8)
        quality_row.append(Gtk.Label(label='Qualität', xalign=0))
        self.quality = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
        self.quality.set_hexpand(True)
        self.quality.set_digits(0)
        self.quality.set_value_pos(Gtk.PositionType.RIGHT)
        quality_row.append(self.quality)
        self.quality_row = quality_row
        self.format_options.append(quality_row)
        self.stack = Gtk.Stack()
        self.format_options.append(self.stack)
        jpeg = self.page('JPEG', 'JPEG-Optionen')
        self.check(jpeg, 'progressive', 'Als progressives JPEG speichern')
        self.check(jpeg, 'grayscale', 'Als Graustufen speichern')
        self.check(jpeg, 'chroma444', 'Keine Farbunterabtastung (4:4:4)',
                   'Erhält feine Farbkanten; erzeugt meist größere Dateien.')
        self.limit = Gtk.CheckButton(label='Dateigröße begrenzen auf (KiB)')
        jpeg.append(self.limit)
        self.target = Gtk.SpinButton.new_with_range(1, 1_000_000, 1)
        self.target.set_value(65)
        jpeg.append(self.target)
        jpeg.append(self.note('Die Qualität wird bei Bedarf bis zum Limit reduziert. '
                              'Ist das nicht möglich, wird keine Datei ersetzt.'))
        gif = self.page('GIF', 'GIF-Optionen')
        self.check(gif, 'gif_interlace', 'Interlaced speichern',
                   'Pillow verwendet Interlacing erst ab 16 × 16 Pixeln.')
        self.check(gif, 'gif_transparency', 'Transparenz beibehalten')
        gif.append(self.note('Maximal 256 Farben. Alpha unter 50 % wird transparent; '
                             'sonstige Teiltransparenz wird auf Weiß reduziert.'))
        png = self.page('PNG', 'PNG-Optionen')
        png.append(Gtk.Label(label='Kompression (0 = schnell, 9 = kleiner)', xalign=0, wrap=True))
        self.compression = Gtk.SpinButton.new_with_range(0, 9, 1)
        png.append(self.compression)
        png.append(self.note('PNG speichert die Bildpixel verlustfrei.'))
        webp = self.page('WEBP', 'WebP-Optionen')
        self.check(webp, 'webp_lossless', 'Verlustfrei speichern')
        webp.append(self.note('Bei verlustfreier Speicherung steuert Qualität den '
                              'Kompressionsaufwand, nicht den Pixelverlust.'))
        generic = self.page('other', 'Formatoptionen')
        generic.append(self.note('Für dieses Format werden die Standardoptionen verwendet.'))
        meta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        columns.append(meta)
        heading = Gtk.Label(label='Metadaten übernehmen', xalign=0)
        heading.add_css_class('heading')
        meta.append(heading)
        self.check(meta, 'keep_exif', 'EXIF-Daten', 'JPEG, PNG und WebP; Ausrichtung ist bereits normalisiert.')
        self.check(meta, 'keep_icc', 'ICC-Farbprofil', 'Ein RGB-Profil wird nicht an ein Graustufen-JPEG angehängt.')
        self.check(meta, 'keep_comment', 'Original-Kommentar', 'JPEG und GIF.')
        self.check(meta, 'keep_xmp', 'XMP-Daten', 'JPEG und WebP; soweit beim Öffnen eingelesen.')
        meta.append(self.note('Nur vorhandene, vom Zielformat unterstützte Daten. '
                              'EXIF-Ausrichtung wird automatisch korrigiert. '
                              'IPTC wird derzeit nicht übernommen.'))
        self.format_note = self.note('')
        body.append(self.format_note)
        body.append(Gtk.Separator())
        heading = Gtk.Label(label='Profile', xalign=0)
        heading.add_css_class('heading')
        body.append(heading)
        profile_row = Gtk.Box(spacing=6)
        self.profile = Gtk.ComboBoxText.new_with_entry()
        self.profile.set_hexpand(True)
        self.profile.get_child().set_placeholder_text('Profil wählen oder Namen eingeben')
        profile_row.append(self.profile)
        for label, callback in (('Laden', self.load_profile), ('Speichern', self.save_profile), ('Löschen', self.delete_profile)):
            button = Gtk.Button(label=label)
            button.connect('clicked', callback)
            profile_row.append(button)
        body.append(profile_row)
        self.status = Gtk.Label(xalign=0, wrap=True)
        body.append(self.status)
        self.reload_profiles()
        self.populate(settings)
        if self.profiles.error:
            self.status.set_text(self.profiles.error)
        self.format.connect('changed', self.format_changed)
        self.limit.connect('toggled', lambda *_: self.target.set_sensitive(self.limit.get_active()))
        self.checks['grayscale'].connect('toggled', lambda *_: self.update_options())
        self.connect('response', self.on_response)
        self.update_options()

    @staticmethod
    def note(text):
        label = Gtk.Label(label=text, xalign=0, wrap=True, max_width_chars=42)
        label.add_css_class('dim-label')
        return label

    def page(self, name, title):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        heading = Gtk.Label(label=title, xalign=0)
        heading.add_css_class('heading')
        box.append(heading)
        self.stack.add_named(box, name)
        return box

    def check(self, box, key, text, tooltip=None):
        check = Gtk.CheckButton(label=text)
        if tooltip:
            check.set_tooltip_text(tooltip)
        self.checks[key] = check
        box.append(check)

    def populate(self, settings):
        for key, check in self.checks.items():
            check.set_active(getattr(settings, key))
        self.quality.set_value(settings.quality)
        self.compression.set_value(settings.png_compression)
        self.limit.set_active(settings.target_kib > 0)
        self.target.set_value(settings.target_kib or 65)
        self.target.set_sensitive(settings.target_kib > 0)

    def settings(self):
        self.target.update()
        self.compression.update()
        values = {key: check.get_active() for key, check in self.checks.items()}
        return SaveSettings(**values, quality=round(self.quality.get_value()),
                            png_compression=self.compression.get_value_as_int(),
                            target_kib=self.target.get_value_as_int() if self.limit.get_active() else 0)

    def format_changed(self, *_):
        try:
            self.name.set_text(filename_for_format(self.name.get_text(), self.format.get_active_id()))
        except ValueError:
            pass  # A blank name is validated when the user presses Save.
        self.update_options()

    def update_options(self):
        fmt = self.format.get_active_id()
        self.stack.set_visible_child_name(fmt if fmt in ('JPEG', 'PNG', 'GIF', 'WEBP') else 'other')
        self.quality_row.set_visible(fmt in ('JPEG', 'WEBP'))
        for key, formats in {'keep_exif': ('JPEG', 'PNG', 'WEBP'),
                             'keep_icc': ('JPEG', 'PNG', 'WEBP', 'TIFF', 'PDF'),
                             'keep_comment': ('JPEG', 'GIF'), 'keep_xmp': ('JPEG', 'WEBP')}.items():
            self.checks[key].set_sensitive(fmt in formats and not (
                key == 'keep_icc' and fmt == 'JPEG' and self.checks['grayscale'].get_active()))
        notes = {'JPEG': 'JPEG wird neu kodiert. Transparente Bereiche erhalten einen weißen Hintergrund.',
                 'ICO': 'ICO wird auf die unterstützten Icon-Größen verkleinert.',
                 'GIF': 'Speichert nur die aktuelle Seite. Für Animationen: Datei → Alle Seiten exportieren.'}
        self.format_note.set_text(notes.get(fmt, 'Speichert die aktuelle Seite. Optionen verändern das Bild im Editor nicht.'))

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
            self.status.set_text('Profil geladen.')
        except KeyError:
            self.status.set_text('Bitte ein vorhandenes Profil wählen.')

    def save_profile(self, *_):
        name = self.profile_name()
        try:
            self.profiles.save(name, self.format.get_active_id(), self.settings())
            self.reload_profiles(name)
            self.status.set_text('Profil gespeichert.')
        except (OSError, ValueError) as error:
            self.status.set_text(str(error))

    def delete_profile(self, *_):
        try:
            self.profiles.delete(self.profile_name())
            self.reload_profiles()
            self.status.set_text('Profil gelöscht.')
        except KeyError:
            self.status.set_text('Bitte ein vorhandenes Profil wählen.')
        except (OSError, ValueError) as error:
            self.status.set_text(str(error))

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
                self.status.set_text(str(error))
                return
            self.on_save(folder / name, settings)
        if self.chooser:
            self.chooser.destroy()
        parent = self.get_transient_for()
        if self in parent.dialogs:
            parent.dialogs.remove(self)
        self.destroy()
