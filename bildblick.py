#!/usr/bin/python3
"""Bildblick: native GTK 4 image viewer; independent implementation."""
import argparse
from pathlib import Path
import sys
import cairo
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib
from image_model import ImageModel, crop_box
from advanced_ui import AdvancedFeatures
from save_dialog import SaveAsDialog
from editor_ui import EditorUI
from ui_theme import install_theme, label, icon_button
from copy import copy


class Window(EditorUI, AdvancedFeatures, Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Bildblick', default_width=1280, default_height=900)
        self.theme = install_theme()
        self.model = ImageModel()
        self.pixbuf = None
        self.scale = 1.0
        self.fit = True
        self.selection = None
        self.drag_start = None
        self.origin = (0, 0)
        self.dialogs = []
        self.allow_close = False
        tile = cairo.ImageSurface(cairo.FORMAT_RGB24, 32, 32)
        ctx = cairo.Context(tile)
        ctx.set_source_rgb(.94, .94, .92)
        ctx.paint()
        ctx.set_source_rgb(.88, .88, .86)
        ctx.rectangle(0, 0, 16, 16)
        ctx.rectangle(16, 16, 16, 16)
        ctx.fill()
        self.checker = cairo.SurfacePattern(tile)
        self.checker.set_extend(cairo.EXTEND_REPEAT)
        self.connect('close-request', self.on_close)
        header = Gtk.HeaderBar()
        self.set_titlebar(header)
        self.title_label = Gtk.Label(label='Bildblick')
        self.title_label.set_ellipsize(3)
        self.title_label.set_max_width_chars(36)
        brand = label('bildblick', 'brand')
        header.pack_start(brand)
        header.set_title_widget(self.title_label)
        self.button(header, 'Öffnen', self.open_dialog, 'Strg+O', start=True)
        self.save_button = self.button(header, 'Bild speichern', self.save_dialog, 'Strg+Umschalt+S')
        self.save_button.add_css_class('primary')
        self.header = header
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(root)
        toolbar = Gtk.Box(spacing=8, margin_start=16, margin_end=16, margin_top=4, margin_bottom=8)
        toolbar.add_css_class('tool-strip')
        root.append(toolbar)
        self.edit_buttons = []
        for icon, callback, hint in [
            ('object-rotate-left-symbolic', lambda:self.rotate(False), '90° nach links drehen'),
            ('object-rotate-right-symbolic', lambda:self.rotate(True), '90° nach rechts drehen (R)'),
        ]:
            button = icon_button(icon,hint,callback)
            toolbar.append(button)
            self.edit_buttons.append(button)
        self.crop_toggle = Gtk.ToggleButton(label='Ausschnitt')
        self.crop_toggle.set_tooltip_text('Ausschnitt auf dem Bild auswählen')
        self.crop_toggle.connect('toggled', self.toggle_crop)
        toolbar.append(self.crop_toggle)
        self.crop_button = self.button(toolbar, 'Zuschneiden', self.apply_crop, 'Auswahl übernehmen (Eingabe)')
        self.undo_button = icon_button('edit-undo-symbolic','Rückgängig (Strg+Z)',self.undo)
        toolbar.append(self.undo_button)
        self.redo_button = icon_button('edit-redo-symbolic','Wiederholen (Strg+Umschalt+Z)',self.redo)
        toolbar.append(self.redo_button)
        toolbar.append(Gtk.Box(hexpand=True))
        self.tools_toggle = Gtk.ToggleButton(label='Bearbeiten',active=True)
        self.tools_toggle.connect('toggled',lambda b:self.inspector_scroll.set_visible(b.get_active()) if hasattr(self,'inspector_scroll') else None)
        toolbar.append(self.tools_toggle)
        self.scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.canvas_overlay = Gtk.Overlay(hexpand=True,vexpand=True)
        self.canvas_overlay.set_child(self.scroll)
        root.append(self.canvas_overlay)
        self.empty_state = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16,
                                   halign=Gtk.Align.CENTER,valign=Gtk.Align.CENTER)
        self.empty_state.append(label('Raum für deine Bilder.', 'dialog-title'))
        self.empty_state.append(label('Ein Bild hierher ziehen oder eine Datei öffnen.', 'muted'))
        self.button(self.empty_state,'Bild öffnen',self.open_dialog,'Datei auswählen (Strg+O)').add_css_class('primary')
        self.canvas_overlay.add_overlay(self.empty_state)
        dock = Gtk.Box(spacing=4,halign=Gtk.Align.CENTER,valign=Gtk.Align.END,margin_bottom=24)
        dock.add_css_class('zoom-dock')
        for icon, title, callback in [('zoom-out-symbolic','Verkleinern (−)',lambda:self.zoom(.8))]:
            dock.append(icon_button(icon,title,callback))
        self.zoom_label = Gtk.Button(label='100 %',tooltip_text='Originalgröße (1)')
        self.zoom_label.connect('clicked',lambda *_:self.actual_size())
        dock.append(self.zoom_label)
        dock.append(icon_button('zoom-in-symbolic','Vergrößern (+)',lambda:self.zoom(1.25)))
        dock.append(icon_button('zoom-fit-best-symbolic','Bild einpassen (F)',self.fit_image))
        self.canvas_overlay.add_overlay(dock)
        self.canvas = Gtk.DrawingArea(hexpand=True, vexpand=True)
        self.canvas.set_draw_func(self.draw)
        self.scroll.set_child(self.canvas)
        self.status = Gtk.Label(label='Bild öffnen · PNG, JPEG, WebP, TIFF und weitere Formate', xalign=0,
                                margin_start=14, margin_end=14, margin_top=9, margin_bottom=9)
        self.status.add_css_class('status-bar')
        self.status.set_ellipsize(3)
        root.append(self.status)
        drag = Gtk.GestureDrag()
        drag.set_button(1)
        drag.connect('drag-begin', self.begin_drag)
        drag.connect('drag-update', self.update_drag)
        drag.connect('drag-end', self.end_drag)
        self.canvas.add_controller(drag)
        keys = Gtk.EventControllerKey()
        keys.connect('key-pressed', self.key_pressed)
        self.add_controller(keys)
        drop = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop.connect('drop', self.drop_file)
        self.canvas.add_controller(drop)
        self.setup_advanced(root,header,toolbar)
        self.setup_editor()
        self.refresh()

    def button(self, parent, label, callback, hint, start=False):
        button = Gtk.Button(label=label, tooltip_text=hint)
        button.connect('clicked', lambda *_: callback())
        if isinstance(parent, Gtk.HeaderBar):
            (parent.pack_start if start else parent.pack_end)(button)
        else:
            parent.append(button)
        return button

    def message(self, title, text, callback=None):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, text=title, secondary_text=text)
        if callback:
            dialog.add_button('Abbrechen', Gtk.ResponseType.CANCEL)
            dialog.add_button('Fortfahren', Gtk.ResponseType.ACCEPT)
        else:
            dialog.add_button('OK', Gtk.ResponseType.OK)
        def response(dlg, answer):
            dlg.destroy()
            self.dialogs.remove(dlg)
            if callback and answer == Gtk.ResponseType.ACCEPT:
                callback()
        dialog.connect('response', response)
        self.dialogs.append(dialog)
        dialog.present()

    def guard(self, action):
        if self.busy:
            return
        self.stop_slideshow()
        if self.model.dirty or self.has_preview():
            self.message('Ungespeicherte Änderungen verwerfen?',
                         'Abbrechen, um zurückzukehren und das Bild zuerst zu speichern.', action)
        else:
            action()

    def on_close(self, *_):
        if self.busy:
            self.message('Vorgang läuft','Bitte den laufenden Lade- oder Speichervorgang abwarten.')
            return True
        if self.allow_close or not (self.model.dirty or self.has_preview()):
            self.cleanup()
            return False
        def discard():
            self.allow_close = True
            self.close()
        self.guard(discard)
        return True

    def open_dialog(self):
        if not self.busy:
            self.stop_slideshow()
            self.file_dialog(False)

    def save_dialog(self):
        if self.has_preview() and not self.busy:
            self.edit(lambda _m:None,after=self.save_dialog)
            return
        if self.model.image and not self.busy:
            self.stop_slideshow()
            for dialog in self.dialogs:
                if isinstance(dialog, SaveAsDialog):
                    dialog.present()
                    return
            def save(path, settings):
                self.save_settings = settings
                self.export_quality = settings.quality
                self.request_save(path, settings=settings)
            dialog = SaveAsDialog(self, self.save_settings, save)
            self.dialogs.append(dialog)
            dialog.present()

    def file_dialog(self, save):
        if save:
            self.save_dialog()
            return
        chooser = Gtk.FileChooserNative.new('Bild öffnen', self,
                    Gtk.FileChooserAction.OPEN, 'Öffnen', 'Abbrechen')
        chooser.set_modal(True)
        filt = Gtk.FileFilter(name='Bilder')
        filt.add_mime_type('image/*')
        chooser.add_filter(filt)
        all_files = Gtk.FileFilter(name='Alle Dateien')
        all_files.add_pattern('*')
        chooser.add_filter(all_files)
        def response(dlg, result):
            file = dlg.get_file() if result == Gtk.ResponseType.ACCEPT else None
            dlg.destroy()
            self.dialogs.remove(dlg)
            if file and file.get_path():
                self.guard(lambda:self.request_load(file.get_path()))
        chooser.connect('response', response)
        self.dialogs.append(chooser)
        chooser.show()

    def request_save(self, path, settings=None):
        if self.busy:
            return
        path = Path(path)
        if not path.suffix:
            path = path.with_suffix('.png')
        settings = settings if settings is not None else self.save_settings
        def save(overwrite=False):
            resized = settings.output_width and (settings.output_width,settings.output_height) != self.model.image.size
            self.edit(lambda m:(copy(m) if resized else m).save(path,overwrite=overwrite,settings=settings),
                      after=lambda:self.status.set_text(f'Exportiert: {path}' if resized else f'Gespeichert: {path}'))
        if self.model.multiframe and path.resolve() == self.model.source_path.resolve():
            self.message('Mehrseiten-Original bleibt erhalten',
                         'Speichern exportiert die aktuelle Seite. Bitte einen anderen Dateinamen wählen.')
            return
        if path.exists():
            self.message('Vorhandene Datei ersetzen?', str(path), lambda: save(True))
        else:
            save()

    def load(self, path):
        try:
            model = ImageModel()
            model.load(path)
            self.adopt_model(model)
        except Exception as error:
            self.message('Bild konnte nicht geöffnet werden', str(error))

    def drop_file(self, _target, file, _x, _y):
        if file.get_path():
            self.guard(lambda: self.request_load(file.get_path()))
            return True
        return False

    def refresh(self, pixels=False):
        image = self.model.image
        loaded = image is not None
        if pixels and loaded:
            data = GLib.Bytes.new(image.tobytes())
            self.pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB,
                            True, 8, image.width, image.height, image.width * 4)
        for button in self.edit_buttons + [self.save_button, self.crop_toggle]:
            button.set_sensitive(loaded)
        self.crop_button.set_sensitive(self.selection is not None)
        self.undo_button.set_sensitive(bool(self.model.history))
        name = self.model.path.name if loaded else 'Bildblick'
        title = ('● ' if self.model.dirty else '') + name
        self.title_label.set_text(title)
        self.set_title(title + ' — Bildblick' if loaded else 'Bildblick')
        self.resize_canvas()
        self.update_status()
        self.update_advanced()
        self.update_editor()
        self.canvas.queue_draw()

    def resize_canvas(self):
        image = self.model.image
        self.scroll.set_policy(Gtk.PolicyType.NEVER if self.fit else Gtk.PolicyType.AUTOMATIC,
                               Gtk.PolicyType.NEVER if self.fit else Gtk.PolicyType.AUTOMATIC)
        self.canvas.set_content_width(1 if self.fit or not image else round(image.width*self.scale))
        self.canvas.set_content_height(1 if self.fit or not image else round(image.height*self.scale))

    def update_status(self):
        image = self.model.image
        if image:
            text = f'{image.width} × {image.height} px  ·  {self.scale*100:.0f} %'
            if self.model.multiframe:
                text += f'  ·  Seite {self.model.frame_index+1} / {self.model.frame_count} (Export: aktuelle Seite)'
            if self.selection:
                x1,y1,x2,y2 = self.selection
                text += f'  ·  Auswahl: {x2-x1} × {y2-y1} px  ·  Eingabe zum Zuschneiden'
            elif self.crop_toggle.get_active():
                text += '  ·  Mit der Maus einen Ausschnitt aufziehen'
            self.status.set_text(text)
        if hasattr(self,'zoom_label'):
            self.zoom_label.set_label(f'{self.scale*100:.0f} %')
        return False

    def draw(self, _area, cr, width, height):
        cr.set_source_rgb(245/255, 245/255, 243/255)
        cr.paint()
        if not self.pixbuf:
            return
        iw, ih = self.model.image.size
        if self.fit:
            scale = min(max(1,width-32)/iw, max(1,height-110)/ih, 1.0)
            if abs(scale-self.scale) > .0001:
                self.scale = scale
                GLib.idle_add(self.update_status)
        self.origin = (max(0, (width-iw*self.scale)/2), max(0, (height-ih*self.scale)/2))
        ox, oy = self.origin
        cr.save()
        cr.rectangle(ox, oy, iw*self.scale, ih*self.scale)
        cr.clip()
        # A checkerboard makes transparency visible.
        cr.set_source(self.checker)
        cr.paint()
        cr.translate(ox, oy)
        cr.scale(self.scale, self.scale)
        shown = self.preview_pixbuf or self.pixbuf
        cr.scale(iw/shown.get_width(),ih/shown.get_height())
        Gdk.cairo_set_source_pixbuf(cr, shown, 0, 0)
        cr.paint()
        cr.restore()
        if self.selection:
            x1,y1,x2,y2 = self.selection
            cr.rectangle(ox+x1*self.scale, oy+y1*self.scale, (x2-x1)*self.scale, (y2-y1)*self.scale)
            cr.set_source_rgba(1, 1, 1, .25)
            cr.fill_preserve()
            cr.set_source_rgb(.15, .15, .15)
            cr.set_line_width(2)
            cr.stroke()

    def to_image(self, x, y):
        return ((x-self.origin[0])/self.scale, (y-self.origin[1])/self.scale)

    def begin_drag(self, _gesture, x, y):
        self.drag_start = None
        if self.busy:
            return
        if self.model.image and self.crop_toggle.get_active():
            ix, iy = self.to_image(x, y)
            if 0 <= ix < self.model.image.width and 0 <= iy < self.model.image.height:
                self.drag_start = (x, y)
                self.selection = None
                self.refresh()

    def update_drag(self, _gesture, dx, dy):
        if self.drag_start:
            x,y = self.drag_start
            self.selection = (crop_box(self.to_image(x,y), self.to_image(x+dx,y+dy), self.model.image.size)
                              if abs(dx) >= 3 and abs(dy) >= 3 else None)
            self.crop_button.set_sensitive(self.selection is not None)
            self.lookup_action('crop').set_enabled(self.selection is not None)
            self.canvas.queue_draw()
            self.update_status()

    def end_drag(self, gesture, dx, dy):
        self.update_drag(gesture, dx, dy)
        self.drag_start = None

    def toggle_crop(self, *_):
        if self.crop_toggle.get_active():
            self.stop_slideshow()
        self.canvas.set_cursor_from_name('crosshair' if self.crop_toggle.get_active() else 'default')
        if not self.crop_toggle.get_active():
            self.selection = None
        self.refresh()

    def apply_crop(self):
        if self.selection:
            box = self.selection
            self.edit(lambda model:model.crop(box))

    def rotate(self, clockwise):
        if self.model.image:
            self.edit(lambda model:model.rotate(clockwise))

    def undo(self):
        if self.has_preview() and not self.busy:
            self.reset_preview()
            return
        if self.busy:
            return
        self.stop_slideshow()
        self.model.undo()
        self.selection = None
        self.refresh(True)

    def zoom(self, factor):
        if self.model.image:
            self.fit = False
            self.scale = max(.02, min(8, self.scale*factor))
            self.refresh()

    def fit_image(self):
        self.fit = True
        self.refresh()

    def actual_size(self):
        self.fit = False
        self.scale = 1
        self.refresh()

    def key_pressed(self, _controller, key, _code, modifiers):
        if self.busy:
            return False
        if self.extra_key(key,modifiers):
            return True
        focus = self.get_focus()
        if isinstance(focus, (Gtk.Editable, Gtk.Scale, Gtk.SpinButton)):
            return False
        ctrl = modifiers & Gdk.ModifierType.CONTROL_MASK
        if ctrl:
            actions = {Gdk.KEY_o:self.open_dialog, Gdk.KEY_s:self.save_dialog, Gdk.KEY_z:self.undo}
        else:
            actions = {Gdk.KEY_plus:lambda:self.zoom(1.25), Gdk.KEY_equal:lambda:self.zoom(1.25),
                       Gdk.KEY_minus:lambda:self.zoom(.8), Gdk.KEY_1:self.actual_size,
                       Gdk.KEY_f:self.fit_image, Gdk.KEY_r:lambda:self.rotate(True),
                       Gdk.KEY_Return:self.apply_crop,
                       Gdk.KEY_Escape:lambda:self.crop_toggle.set_active(False)}
        action = actions.get(Gdk.keyval_to_lower(key))
        if action:
            action()
            return True
        return False


def main():
    parser = argparse.ArgumentParser(description='Bildblick – nativer Linux-Bildbetrachter')
    parser.add_argument('image', nargs='?')
    args = parser.parse_args()
    Gtk.init()
    Gtk.Window.set_default_icon_name('local.bildblick.Viewer')
    if Gdk.Display.get_default() is None:
        print('Keine Verbindung zur grafischen Sitzung. Bitte start.sh im Terminal deiner Linux-Desktop-Sitzung starten.', file=sys.stderr)
        return 1
    app = Gtk.Application(application_id='local.bildblick.Viewer', flags=Gio.ApplicationFlags.NON_UNIQUE)
    def activate(application):
        window = Window(application)
        window.present()
        if args.image:
            path = Path(args.image)
            if path.is_dir():
                window.set_folder(path,open_first=True)
            else:
                window.request_load(path)
    app.connect('activate', activate)
    return app.run([sys.argv[0]])


if __name__ == '__main__':
    raise SystemExit(main())
