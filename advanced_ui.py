"""GTK features around the image canvas. Worker results return via GLib."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import threading
from PIL import Image, ImageOps, UnidentifiedImageError
from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf, Pango
from dialog_layout import StandardDialog, module_window
from image_model import ImageModel, image_files
from batch import plan_batch, run_batch
from menus import build_menus, RESIZE_ACCELERATOR
from resize_dialog import ResizeDialog
from save_options import SaveSettings
from dataclasses import replace
from adjustments import adjusted
from ui_theme import icon_button, label as ui_label


def pixbuf(image):
    image = image.convert('RGBA')
    return GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(image.tobytes()),
        GdkPixbuf.Colorspace.RGB, True, 8, image.width, image.height, image.width*4)


class AdvancedFeatures:
    def setup_advanced(self, root, header, toolbar):
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='bildblick')
        self.busy = False
        self.closed = False
        self.folder_files = []
        self.folder = None
        self.folder_generation = 0
        self.thumb_generation = 0
        self.thumb_limit = 100
        self.slide_source = 0
        self.slide_interval = 3
        self.animation = False
        self.full = False
        self.export_quality = 95
        self.keep_metadata = True
        self.save_settings = SaveSettings()
        self.batch_cancel = None
        self.connect('destroy', self.cleanup)
        self.menu_model, self.actions = build_menus(self)
        self.menu_bar = Gtk.PopoverMenuBar.new_from_model(self.menu_model)
        self.previous = icon_button('go-previous-symbolic','Vorheriges Bild (Pfeil links)',lambda:self.navigate(-1))
        self.next_button = icon_button('go-next-symbolic','Nächstes Bild (Pfeil rechts)',lambda:self.navigate(1))
        self.page_previous = icon_button('go-up-symbolic','Vorherige Seite (Strg+Bild auf)',lambda:self.change_frame(-1))
        self.page_next = icon_button('go-down-symbolic','Nächste Seite (Strg+Bild ab)',lambda:self.change_frame(1))
        for button in (self.previous,self.next_button,self.page_previous,self.page_next):
            toolbar.append(button)
        self.position_label = Gtk.Label(label='0 / 0',width_chars=7)
        self.position_label.add_css_class('file-counter')
        toolbar.append(self.position_label)
        toolbar.append(Gtk.Box(hexpand=True))
        self.resize_button = icon_button('transform-scale-symbolic','Größe ändern (Strg+R)',self.resize_dialog)
        self.resize_button.set_action_name('win.resize')
        toolbar.append(self.resize_button)
        self.adjust_button = icon_button('preferences-system-symbolic','Bildanpassungen …',self.adjust_dialog)
        toolbar.append(self.adjust_button)
        self.edit_buttons.append(self.adjust_button)
        self.slide_button = Gtk.Button(label='Diashow')
        self.spinner = Gtk.Spinner(width_request=14)
        toolbar.append(self.spinner)
        root.prepend(self.menu_bar)
        self.thumbnail_window = None
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, width_request=200)
        self.search = Gtk.SearchEntry(placeholder_text='Dateinamen filtern …')
        self.search.connect('search-changed',lambda *_:self.rebuild_thumbnails())
        self.sidebar.add_css_class('sidebar')
        self.sidebar.append(self.search)
        thumb_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=False)
        self.thumbnails = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                                      min_children_per_line=1, max_children_per_line=1)
        thumb_scroll.set_child(self.thumbnails)
        self.sidebar.append(thumb_scroll)
        self.more_thumbs = self.button(self.sidebar,'Weitere Vorschaubilder',self.more_thumbnails,'Weitere 100 Dateien anzeigen')
        self.sidebar.set_visible(False)

    def cleanup(self, *_):
        self.closed = True
        if getattr(self,'growth_timer',0):
            GLib.source_remove(self.growth_timer); self.growth_timer=0
        self.preview_generation = getattr(self,'preview_generation',0)+1
        if getattr(self,'preview_timer',0):
            GLib.source_remove(self.preview_timer)
            self.preview_timer = 0
        self.stop_slideshow()
        if getattr(self,'cursor_timer',0): GLib.source_remove(self.cursor_timer); self.cursor_timer=0
        self.thumb_generation += 1
        if self.batch_cancel:
            self.batch_cancel.set()
        self.pool.shutdown(wait=False,cancel_futures=True)

    def submit(self, work, done, failure=None):
        def deliver(future):
            if self.closed:
                return False
            try:
                value = future.result()
            except Exception as error:
                if failure:
                    failure(error)
                else:
                    self.message('Vorgang fehlgeschlagen',str(error))
            else:
                done(value)
            return False
        future = self.pool.submit(work)
        future.add_done_callback(lambda f:GLib.idle_add(deliver,f))

    def set_busy(self, value):
        self.busy = value
        self.spinner.set_spinning(value)
        self.refresh()

    def update_advanced(self):
        loaded = self.model.image is not None
        for action, requires_image in self.actions:
            action.set_enabled(not self.busy and (loaded or not requires_image))
        self.lookup_action('undo').set_enabled(not self.busy and bool(self.model.history))
        self.lookup_action('redo').set_enabled(not self.busy and bool(self.model.future))
        self.lookup_action('crop').set_enabled(not self.busy and self.selection is not None)
        for button in self.edit_buttons+[self.save_button,self.crop_toggle,self.undo_button,self.crop_button]:
            if self.busy:
                button.set_sensitive(False)
        for button in (self.previous,self.next_button):
            button.set_sensitive(bool(self.folder_files) and not self.busy)
        self.redo_button.set_sensitive(not self.busy and bool(self.model.future))
        self.page_previous.set_sensitive(loaded and self.model.frame_index>0 and not self.busy)
        self.page_next.set_sensitive(loaded and self.model.frame_index+1<self.model.frame_count and not self.busy)
        self.slide_button.set_sensitive(loaded and not self.busy)
        current = self.model.source_path
        position = self.folder_files.index(current)+1 if current in self.folder_files else 0
        self.position_label.set_text(f'{position} / {len(self.folder_files)}' if self.folder else '0 / 0')
        self.position_label.set_tooltip_text(str(self.folder) if self.folder else 'Kein Bildordner')

    def request_load(self, path, frame=0, playing=False):
        if self.busy:
            return
        if not playing:
            self.stop_slideshow()
        self.set_busy(True)
        self.status.set_text('Bild wird geladen …')
        def work():
            model = ImageModel()
            model.load(path, frame=frame)
            return model
        def done(model):
            self.adopt_model(model)
            self.set_busy(False)
            if playing:
                self.schedule_slide()
        def failed(error):
            self.set_busy(False)
            self.stop_slideshow()
            self.message('Bild konnte nicht geöffnet werden',str(error))
        self.submit(work,done,failed)

    def adopt_model(self, model):
        self.reset_preview()
        self.model = model
        if not getattr(self,'zoom_locked',False):
            if not self.full: self.view_mode='window'; self.fit=True
        else: self.view_mode='manual'; self.fit=False; self.scale_y=self.scale
        self.selection = None
        self.crop_toggle.set_active(False)
        self.refresh(True)
        self.canvas.grab_focus()
        if model.source_path and self.folder != model.source_path.parent:
            self.set_folder(model.source_path.parent)

    def edit(self, operation, after=None):
        if self.busy or self.model.image is None:
            return
        self.stop_slideshow()
        self.set_busy(True)
        def done(_):
            self.selection = None
            self.crop_toggle.set_active(False)
            self.set_busy(False)
            self.refresh(True)
            if after:
                after()
        def failed(error):
            self.set_busy(False)
            self.refresh(True)
            self.message('Bearbeitung fehlgeschlagen',str(error))
        pending = self.recipe() if self.has_preview() else None
        def work():
            if pending:
                self.model.replace(adjusted(self.model.image,*pending))
            operation(self.model)
        self.reset_preview()
        self.submit(work,done,failed)

    def choose(self, title, callback, folder=False, multiple=False):
        self.stop_slideshow()
        chooser = Gtk.FileChooserNative.new(title,self,Gtk.FileChooserAction.SELECT_FOLDER if folder else Gtk.FileChooserAction.OPEN,
                                           'Auswählen','Abbrechen')
        chooser.set_select_multiple(multiple)
        chooser.set_modal(True)
        def response(dlg,answer):
            paths = []
            if answer == Gtk.ResponseType.ACCEPT:
                files = dlg.get_files()
                paths = [Path(files.get_item(i).get_path()) for i in range(files.get_n_items()) if files.get_item(i).get_path()]
            dlg.destroy()
            self.dialogs.remove(dlg)
            if paths:
                callback(paths if multiple else paths[0])
        chooser.connect('response',response)
        self.dialogs.append(chooser)
        chooser.show()

    def open_folder(self):
        if not self.busy:
            self.choose('Bildordner öffnen',lambda p:self.set_folder(p,open_first=True),folder=True)

    def set_folder(self, path, open_first=False):
        path = Path(path).absolute()
        self.folder = path
        self.folder_files = []
        self.thumb_limit = 100
        self.thumb_generation += 1
        self.folder_generation += 1
        token = self.folder_generation
        def done(files):
            if self.folder != path or token != self.folder_generation:
                return
            self.folder_files = files
            if hasattr(self,'remember_folder'): self.remember_folder(path)
            self.rebuild_thumbnails()
            self.update_advanced()
            if open_first:
                if files:
                    self.guard(lambda:self.request_load(files[0]))
                else:
                    self.message('Keine Bilder gefunden',str(path))
        self.submit(lambda:image_files(path),done)

    def navigate(self, direction, playing=False):
        if self.busy or not self.folder_files:
            return
        current = self.model.source_path
        index = self.folder_files.index(current) if current in self.folder_files else -1
        target = self.folder_files[(index+direction)%len(self.folder_files)]
        if playing:
            self.request_load(target,playing=True)
        else:
            self.stop_slideshow()
            self.guard(lambda:self.request_load(target))

    def change_frame(self, direction):
        if self.busy:
            return
        frame = self.model.frame_index+direction
        if 0 <= frame < self.model.frame_count:
            self.stop_slideshow()
            self.guard(lambda:self.request_load(self.model.source_path,frame))

    def more_thumbnails(self):
        self.thumb_limit += 100
        self.rebuild_thumbnails()

    def rebuild_thumbnails(self):
        self.thumb_generation += 1
        token = self.thumb_generation
        child = self.thumbnails.get_first_child()
        while child:
            self.thumbnails.remove(child)
            child = self.thumbnails.get_first_child()
        query = self.search.get_text().casefold()
        matches = [p for p in self.folder_files if query in p.name.casefold() and (not self.tag_filter.get_active() or str(p) in self.tags)]
        self.more_thumbs.set_visible(len(matches)>self.thumb_limit)
        if not self.sidebar.get_visible():
            return
        rows = []
        for path in matches[:self.thumb_limit]:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3)
            picture = Gtk.Picture(width_request=160,height_request=105,can_shrink=True)
            label = Gtk.Label(label=('★ ' if str(path) in self.tags else '')+path.name,max_width_chars=24,ellipsize=Pango.EllipsizeMode.MIDDLE)
            box.append(picture)
            box.append(label)
            button = Gtk.Button(tooltip_text=str(path))
            button.set_child(box)
            button.connect('clicked',lambda _b,p=path:self.guard(lambda:self.request_load(p)) if not self.busy else None)
            self.thumbnails.append(button)
            rows.append((path,picture))
        def work():
            for path,picture in rows:
                if self.closed or token != self.thumb_generation:
                    break
                try:
                    try:
                        with Image.open(path) as image:
                            image.thumbnail((160,105))
                            thumb = ImageOps.exif_transpose(image).convert('RGBA')
                    except UnidentifiedImageError:
                        from native_codecs import decode
                        thumb, _count, _metadata = decode(path)
                        thumb.thumbnail((160,105))
                    GLib.idle_add(show,picture,thumb)
                except Exception:
                    pass
        def show(picture,thumb):
            if not self.closed and token == self.thumb_generation:
                picture.set_pixbuf(pixbuf(thumb))
            return False
        self.submit(work,lambda _:None)

    def toggle_sidebar(self):
        if self.thumbnail_window:
            self.thumbnail_window.close()
            return
        self.thumbnail_window = module_window(self, 'Vorschaubilder')
        self.sidebar.set_visible(True)
        self.thumbnail_window.set_child(self.sidebar)
        def close(window):
            window.set_child(None)
            self.sidebar.set_visible(False)
            self.thumbnail_window = None
            return False
        self.thumbnail_window.connect('close-request',close)
        keys=Gtk.EventControllerKey(); keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect('key-pressed',self.thumbnail_key); self.thumbnail_window.add_controller(keys)
        self.thumbnail_window.present()
        self.rebuild_thumbnails()

    def toggle_fullscreen(self):
        self.leave_fullscreen() if self.full else self.enter_fullscreen()

    def stop_slideshow(self):
        if self.slide_source:
            GLib.source_remove(self.slide_source)
        self.slide_source = 0
        self.playing = False
        if hasattr(self,'slide_button'):
            self.slide_button.set_label('Diashow')

    def toggle_slideshow(self, animation=False):
        if self.busy:
            return
        if getattr(self,'playing',False):
            self.stop_slideshow()
            return
        if self.model.image is None:
            return
        if not animation and not self.folder_files:
            self.message('Kein Bildordner geladen','Bitte zuerst einen Ordner öffnen oder dessen Einlesen abwarten.')
            return
        if animation and self.model.frame_count < 2:
            self.message('Keine Animation / Mehrseiten-Datei','Diese Datei enthält nur ein Bild.')
            return
        def start():
            # Playback always reloads original source frames; edited pixels stay until the next tick.
            self.animation = animation
            self.playing = True
            self.slide_button.set_label('Stopp')
            self.schedule_slide()
        self.guard(start)

    def schedule_slide(self):
        if not getattr(self,'playing',False):
            return
        delay = self.model.duration if self.animation else int(self.slide_interval*1000)
        def tick():
            self.slide_source = 0
            if not self.playing or self.closed:
                return False
            if self.animation:
                self.request_load(self.model.source_path,(self.model.frame_index+1)%self.model.frame_count,playing=True)
            else:
                self.navigate(1,playing=True)
            return False
        self.slide_source = GLib.timeout_add(max(20,delay),tick)

    def form(self, title, fields, callback):
        from tool_dialogs import ToolDialog
        self.stop_slideshow()
        precise = {'width','height','x','y','size'}
        sliders = [key for key,_label,_initial,kind in fields if isinstance(kind,tuple) and key not in precise]
        return ToolDialog(self,title,fields,callback,sliders=sliders)

    def resize_dialog(self):
        if self.busy or self.model.image is None:
            return
        self.stop_slideshow()
        for dialog in self.dialogs:
            if isinstance(dialog,ResizeDialog):
                dialog.present()
                return
        dialog = ResizeDialog(self,lambda w,h,method,dpi:self.edit(lambda m:m.resize(w,h,method,dpi)))
        self.dialogs.append(dialog)
        dialog.present()

    def adjust_values_dialog(self):
        def operation(image, values):
            temp = ImageModel(); temp.image = image
            for name in ('brightness','contrast','color'):
                if values[name] != 100: temp.effect(name,values[name]/100)
            return temp.image
        return self.preview_tool('Helligkeit, Kontrast und Farbe',[
            ('brightness','Helligkeit (%)',100,(0,300,1)),
            ('contrast','Kontrast (%)',100,(0,300,1)),
            ('color','Sättigung (%)',100,(0,300,1))],operation,
            '100 % entspricht dem Original. Die Vorschau verändert die Arbeitsdatei erst beim Anwenden.',
            sliders=('brightness','contrast','color'))

    def filter_dialog(self):
        def operation(image, values):
            temp = ImageModel(); temp.image = image
            self.apply_filters(temp,values)
            return temp.image
        return self.preview_tool('Schärfen und Weichzeichnen',[
            ('sharpness','Schärfe (%)',100,(0,500,1)),
            ('blur','Weichzeichnen (Radius)',0,(0,30,.5))],operation,
            sliders=('sharpness','blur'))

    @staticmethod
    def apply_filters(model, values):
        temp = ImageModel()
        temp.image = model.image
        if values['sharpness'] != 100:
            temp.effect('sharpness',values['sharpness']/100)
        if values['blur']:
            temp.effect('blur',values['blur'])
        model.replace(temp.image)

    def text_dialog(self):
        self.form('Text einfügen', [('text','Text','',str),('x','X',20,(0,50000,1)),('y','Y',20,(0,50000,1)),
                  ('size','Schriftgröße',32,(8,500,1)),('color','Farbe (#RRGGBB)','#ffffff',str)],
                  lambda v:self.edit(lambda m:m.add_text(v['text'],v['x'],v['y'],v['size'],v['color'])))

    def watermark_dialog(self):
        self.choose('Wasserzeichen wählen (unten rechts, 50 % Deckkraft)',lambda p:self.edit(lambda m:m.watermark(p)))

    def redo(self):
        if not self.busy:
            self.reset_preview()
            self.stop_slideshow()
            self.model.redo()
            self.selection = None
            self.refresh(True)

    def slideshow_settings(self):
        self.form('Diashow', [('seconds','Sekunden pro Bild',self.slide_interval,(.5,120,.5))],
                  lambda v:setattr(self,'slide_interval',v['seconds']))

    def export_options(self):
        def apply(v):
            self.export_quality = int(v['quality'])
            self.keep_metadata = v['metadata']
            self.save_settings = replace(self.save_settings, quality=self.export_quality,
                keep_exif=v['metadata'], keep_icc=v['metadata'],
                keep_comment=v['metadata'], keep_xmp=v['metadata'])
        self.form('Exportoptionen', [('quality','JPEG-/WebP-Qualität',self.export_quality,(1,100,1)),
                  ('metadata','EXIF / ICC übernehmen (soweit Format unterstützt)',self.keep_metadata,'bool')],apply)

    def show_info(self):
        from info_dialog import ImageInfoDialog
        if self.busy or self.model.image is None: return
        self.stop_slideshow()
        for dialog in self.dialogs:
            if isinstance(dialog,ImageInfoDialog): dialog.present(); return dialog
        return ImageInfoDialog(self)

    def export_pages(self):
        self.stop_slideshow()
        chooser = Gtk.FileChooserNative.new('Alle Seiten: Originalseiten + aktuell bearbeitete Seite',self,
                    Gtk.FileChooserAction.SAVE,'Exportieren','Abbrechen')
        chooser.set_modal(True)
        chooser.set_current_name(self.model.source_path.stem+'-alle-seiten.tiff')
        def response(dlg,answer):
            file = dlg.get_file() if answer == Gtk.ResponseType.ACCEPT else None
            dlg.destroy()
            self.dialogs.remove(dlg)
            if file and file.get_path():
                target = Path(file.get_path())
                def export(overwrite=False):
                    self.edit(lambda m:m.export_document(target,overwrite),
                              lambda:self.status.set_text(f'Alle Seiten exportiert: {target}'))
                if target.exists():
                    self.message('Datei ersetzen?',str(target),lambda:export(True))
                else:
                    export()
        chooser.connect('response',response)
        self.dialogs.append(chooser)
        chooser.show()

    def print_image(self):
        if self.has_preview():
            self.edit(lambda _m:None,after=self.print_image)
            return
        self.stop_slideshow()
        operation = Gtk.PrintOperation()
        operation.set_n_pages(1)
        buffer = self.pixbuf
        def draw_page(_op,context,_page):
            cr = context.get_cairo_context()
            scale = min(context.get_width()/buffer.get_width(),context.get_height()/buffer.get_height())
            cr.translate((context.get_width()-buffer.get_width()*scale)/2,(context.get_height()-buffer.get_height()*scale)/2)
            cr.scale(scale,scale)
            cr.set_source_rgb(1,1,1)
            cr.paint()
            Gdk.cairo_set_source_pixbuf(cr,buffer,0,0)
            cr.paint()
        operation.connect('draw-page',draw_page)
        try:
            operation.run(Gtk.PrintOperationAction.PRINT_DIALOG,self)
        except Exception as error:
            self.message('Drucken fehlgeschlagen',str(error))

    def batch_dialog(self):
        self.choose('Quelldateien für Stapelverarbeitung',self.batch_sources,multiple=True)

    def batch_sources(self, sources):
        self.choose('Zielordner (Originale bleiben erhalten)',lambda folder:self.batch_options(sources,folder),folder=True)

    def batch_options(self, sources, folder):
        def preview(v):
            ext = v['format'].strip().lower()
            if ext != 'copy' and not ext.startswith('.'):
                ext = '.'+ext
            plan = plan_batch(sources,folder,ext,v['pattern'])
            details = '\n'.join(f'{p.source.name} → {p.destination.name}' for p in plan[:15])
            if len(plan)>15:
                details += f'\n… und {len(plan)-15} weitere'
            details += '\n\nVorhandene Dateien werden nicht überschrieben.'
            self.message(f'{len(plan)} Dateien verarbeiten?',details,lambda:self.start_batch(plan,v,ext=='copy'))
        self.form('Stapelverarbeitung', [('format','Zielformat oder copy für umbenannte Kopien','png',str),
                  ('pattern','Namensvorlage: {stem}, {index:04d}','{stem}',str),
                  ('width','Max. Breite (0 = unverändert)',0,(0,50000,1)),
                  ('height','Max. Höhe (0 = unverändert)',0,(0,50000,1)),
                  ('rotate','90° im Uhrzeigersinn drehen',False,'bool'),
                  ('quality','JPEG-/WebP-Qualität',95,(1,100,1)),
                  ('metadata','Metadaten übernehmen',True,'bool')],preview)

    def start_batch(self, plan, values, copy_only):
        if self.batch_cancel is not None:
            self.message('Stapelverarbeitung läuft bereits','Bitte zuerst den laufenden Auftrag beenden.')
            return
        cancel = threading.Event()
        self.batch_cancel = cancel
        dialog = StandardDialog(title='Stapelverarbeitung',transient_for=self,modal=True)
        dialog.add_button('Nach aktueller Datei abbrechen',Gtk.ResponseType.CANCEL)
        label = Gtk.Label(label=f'0 / {len(plan)}',margin_top=20,margin_bottom=20,margin_start=20,margin_end=20)
        dialog.get_content_area().append(label)
        dialog.connect('response',lambda *_:cancel.set())
        dialog.connect('close-request',lambda *_:(cancel.set(),True)[1])
        dialog.present()
        def progress(done,total,result):
            GLib.idle_add(lambda:(label.set_text(f'{done} / {total}  ·  {Path(result["source"]).name}'),False)[1])
        def finished(results):
            dialog.destroy()
            self.batch_cancel = None
            good = sum(r['ok'] for r in results)
            errors = [f'{Path(r["source"]).name}: {r["error"]}' for r in results if not r['ok']]
            self.message('Stapelverarbeitung beendet',f'{good} erfolgreich, {len(errors)} Fehler, {len(plan)-len(results)} nicht bearbeitet.\n'+'\n'.join(errors[:12]))
        self.submit(lambda:run_batch(plan,max_width=int(values['width']),max_height=int(values['height']),
                    clockwise=values['rotate'],quality=int(values['quality']),metadata=values['metadata'],
                    copy_only=copy_only,cancel=cancel,progress=progress),finished,
                    lambda e:(dialog.destroy(),setattr(self,'batch_cancel',None),self.message('Stapelverarbeitung fehlgeschlagen',str(e))))

    def extra_key(self, key, modifiers):
        from shortcuts import dispatch
        return dispatch(self,key,modifiers)
