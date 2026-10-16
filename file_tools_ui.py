"""Local file, media and scanner actions exposed through native menus."""
import io
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
from dialog_layout import module_window
from gi.repository import Gtk, Gio, GLib
from image_tools import checked_size, erase_selection, auto_crop, reduce_colors, swap_channels
from tool_dialogs import ToolDialog
from image_model import atomic_write


class FileToolsUI:
    def paint_dialog(self):
        if self.has_preview(): self.edit(lambda _m:None,after=self.paint_dialog); return
        from paint_dialog import PaintDialog
        return PaintDialog(self)

    def blank_dialog(self):
        def create(v):
            size=checked_size(v['width'],v['height'])
            self.guard(lambda:self.new_document(Image.new('RGBA',size,v['color'])))
        return ToolDialog(self,'Neues Bild',[
            ('width','Breite (Pixel)',800,(1,80000000,1)),('height','Höhe (Pixel)',600,(1,80000000,1)),
            ('color','Hintergrund','#ffffff','color')],create)

    def select_all(self):
        self.crop_toggle.set_active(True)
        self.selection=(0,0,*self.model.image.size)
        self.refresh()

    def center_selection(self):
        if not self.selection: self.select_all(); return
        x1,y1,x2,y2=self.selection
        ratio=(x2-x1)/(y2-y1)
        w=min(self.model.image.width,round(self.model.image.height*ratio)); h=round(w/ratio)
        x=(self.model.image.width-w)//2; y=(self.model.image.height-h)//2
        self.selection=(x,y,x+w,y+h); self.refresh()

    def cut_selection(self,outside=False):
        box=self.selection
        if not box:
            self.message('Keine Auswahl','Zuerst mit der Maus einen Bereich auswählen.'); return
        if self.has_preview():
            def apply_after_preview():
                self.selection=box; self.cut_selection(outside)
            self.edit(lambda _m:None,after=apply_after_preview); return
        if not outside: self.copy_image()
        self.edit(lambda m:m.replace(erase_selection(m.image,box,outside)))

    def auto_crop_dialog(self):
        return self.preview_tool('Einfarbige Ränder entfernen', [('tolerance','Farbtoleranz',10,(0,255,1))],
            lambda image,v:auto_crop(image,int(v['tolerance'])),
            'Entfernt transparente Ränder oder einen einfarbigen Hintergrund wie in der linken oberen Ecke.',sliders=('tolerance',))

    def palette_dialog(self):
        return self.preview_tool('Farben reduzieren',[
            ('colors','Anzahl Farben',256,(2,256,1)),('dither','Dithering',True,'bool')],
            lambda image,v:reduce_colors(image,int(v['colors']),v['dither']),
            'Reduziert die sichtbaren RGB-Farben; Transparenz bleibt erhalten. Die Bearbeitung arbeitet weiterhin mit RGBA.',sliders=('colors',))

    def swap_dialog(self):
        return self.preview_tool('Farbkanäle tauschen',[
            ('order','Reihenfolge','BGR',[(v,v) for v in ('RBG','GRB','GBR','BRG','BGR')])],
            lambda image,v:swap_channels(image,v['order']))

    def histogram_dialog(self):
        window=module_window(self, 'Histogramm')
        area=Gtk.DrawingArea(hexpand=True,vexpand=True,margin_start=24,margin_end=24,margin_top=24,margin_bottom=24)
        channels=self.model.image.convert('RGB').histogram()
        def draw(_area,cr,w,h):
            cr.set_source_rgb(.97,.97,.96); cr.paint()
            maximum=max(channels) or 1
            for index,color in enumerate(((.8,.2,.2),(.2,.6,.3),(.2,.4,.8))):
                cr.set_source_rgba(*color,.65); cr.set_line_width(max(1,w/256))
                for x,value in enumerate(channels[index*256:(index+1)*256]):
                    cr.move_to(x*w/256,h); cr.line_to(x*w/256,h-value/maximum*h)
                cr.stroke()
        area.set_draw_func(draw); window.set_child(area); window.present()
        return window

    def reopen(self):
        path=self.model.path
        if path and path.exists(): self.guard(lambda:self.request_load(path))
        else: self.message('Noch keine Datei','Dieses Bild zuerst speichern.')

    def save_current(self):
        if self.has_preview(): self.edit(lambda _m:None,after=self.save_current); return
        if self.model.path and self.model.path.is_file(): self.request_save(self.model.path)
        else: self.save_dialog()

    def file_action(self,action):
        path=self.model.path
        if not path or not path.is_file():
            self.message('Noch keine Datei','Dieses Bild zuerst speichern.'); return
        if self.model.dirty or self.has_preview():
            self.message('Änderungen zuerst speichern','Dateiaktionen verwenden die gespeicherte Datei. Bitte zuerst speichern oder Änderungen rückgängig machen.'); return
        def transfer(destination):
            destination=Path(destination).absolute()
            if destination==path: raise ValueError('Bitte einen anderen Dateinamen oder Ordner wählen.')
            if destination.exists(): raise FileExistsError('Das Ziel existiert bereits; es wird nicht überschrieben.')
            source=Gio.File.new_for_path(str(path)); target=Gio.File.new_for_path(str(destination))
            if action=='copy': source.copy(target,Gio.FileCopyFlags.NONE,None,None,None)
            else:
                source.move(target,Gio.FileCopyFlags.NONE,None,None,None)
                self.model.path=destination
                if self.model.source_path==path: self.model.source_path=destination
                self.set_folder(destination.parent); self.refresh()
        if action=='rename':
            def rename(v):
                name=v['name'].strip()
                if not name or Path(name).name!=name or name in ('.','..'): raise ValueError('Einen Dateinamen ohne Verzeichnis eingeben.')
                transfer(path.with_name(name))
            return ToolDialog(self,'Datei umbenennen',[('name','Name',path.name,str)],rename)
        if action in ('move','copy'):
            def chosen(folder):
                try: transfer(folder/path.name)
                except Exception as error: self.message('Dateiaktion fehlgeschlagen',str(error))
            self.choose('Zielordner wählen',chosen,folder=True)
        elif action=='trash':
            def trash():
                try:
                    Gio.File.new_for_path(str(path)).trash(None)
                    self.clear_image(); self.set_folder(path.parent)
                except Exception as error: self.message('Papierkorb nicht verfügbar',str(error))
            self.message('Datei in den Papierkorb verschieben?',str(path),trash)

    def external_editor(self):
        path=self.model.path
        if not path or not path.is_file() or self.model.dirty or self.has_preview():
            self.message('Bild zuerst speichern','Eine externe Anwendung öffnet die gespeicherte Datei.'); return
        content_type=Gio.content_type_guess(str(path),None)[0]
        apps=[app for app in Gio.AppInfo.get_all_for_type(content_type) if app.get_id()!='local.bildblick.Viewer.desktop']
        if not apps:
            self.message('Keine Anwendung registriert','Über die Linux-Dateiverwaltung eine Anwendung für dieses Dateiformat einrichten.'); return
        def launch(v): apps[int(v['app'])].launch([Gio.File.new_for_path(str(path))],None)
        return ToolDialog(self,'Öffnen mit …',[('app','Anwendung','0',[(str(i),app.get_display_name()) for i,app in enumerate(apps)])],launch)

    def search_files(self):
        if self.thumbnail_window is None: self.toggle_sidebar()
        self.search.grab_focus()

    def recent_folders(self):
        try: folders=json.loads((self.viewer_config.parent/'recent.json').read_text())
        except (OSError,ValueError): folders=[]
        folders=[p for p in folders if Path(p).is_dir()]
        if not folders:
            self.message('Keine letzten Ordner','Zuerst ein Bild oder einen Ordner öffnen.'); return
        return ToolDialog(self,'Zuletzt verwendete Ordner',[('folder','Ordner',folders[0],[(p,p) for p in folders])],
                          lambda v:self.set_folder(Path(v['folder']),open_first=True))

    def remember_folder(self,path):
        config=self.viewer_config.parent/'recent.json'
        try:
            try: folders=json.loads(config.read_text())
            except (OSError,ValueError): folders=[]
            if not isinstance(folders,list): folders=[]
            folders=[str(path)]+[p for p in folders if isinstance(p,str) and p!=str(path)]
            config.parent.mkdir(parents=True,exist_ok=True)
            atomic_write(config,lambda p:Path(p).write_text(json.dumps(folders[:10])),overwrite=True)
        except OSError: pass

    def media_dialog(self):
        def play(path):
            window=module_window(self, path.name)
            video=Gtk.Video.new_for_filename(str(path)); video.set_autoplay(False)
            window.set_child(video)
            def error(stream,*_):
                failure=stream.get_error()
                if failure: self.message('Medienwiedergabe nicht verfügbar',str(failure)+'\nGStreamer-Codecs für dieses Format installieren.')
            stream=video.get_media_stream(); stream.connect('notify::error',error)
            window.connect('close-request',lambda *_:(stream.pause(),False)[1]); window.present()
        self.choose('Audio oder Video öffnen',play)

    def scan_dialog(self,print_after=False):
        command=shutil.which('scanimage')
        if not command:
            self.message('SANE fehlt','Für Scanner-Unterstützung das Paket sane-backends installieren. Danach Scanner anschließen und erneut öffnen.'); return
        self.set_busy(True)
        def devices():
            result=subprocess.run([command,'--formatted-device-list=%d%n'],capture_output=True,text=True,timeout=30,check=True)
            return [v for v in result.stdout.splitlines() if v]
        def ready(devices):
            self.set_busy(False)
            if not devices: self.message('Kein Scanner gefunden','Scanner einschalten und die SANE-Konfiguration prüfen.'); return
            def apply(v):
                def start():
                    self.set_busy(True)
                    def work():
                        # File-backed output avoids retaining a large second copy in RAM.
                        with tempfile.TemporaryDirectory(prefix='bildblick-scan-') as directory:
                            target=Path(directory)/'scan.png'
                            with target.open('wb') as output:
                                result=subprocess.run([command,'--device-name',v['device'],'--format=png','--resolution',str(int(v['dpi'])),
                                                       '--mode',v['mode']],stdout=output,stderr=subprocess.PIPE,timeout=180)
                            if result.returncode: raise ValueError(result.stderr.decode(errors='replace')[-1500:])
                            with Image.open(target) as source:
                                checked_size(*source.size); image=source.convert('RGBA')
                            image.info['dpi']=(v['dpi'],v['dpi']); return image
                    def done(image):
                        self.new_document(image,'Scan.png'); self.set_busy(False)
                        if print_after: self.print_image()
                    self.submit(work,done,lambda e:(self.set_busy(False),self.message('Scannen fehlgeschlagen',str(e))))
                self.guard(start)
            ToolDialog(self,'Scannen und drucken' if print_after else 'Scannen',[
                ('device','Scanner',devices[0],[(d,d) for d in devices]),('dpi','DPI',300,(50,1200,1)),
                ('mode','Modus','Color',[('Color','Farbe'),('Gray','Graustufen'),('Lineart','Strichzeichnung')])],apply,
                'Die verfügbaren Auflösungen und Modi hängen vom SANE-Treiber des Scanners ab.')
        self.submit(devices,ready,lambda e:(self.set_busy(False),self.message('Scanner konnten nicht gelesen werden',str(e))))
