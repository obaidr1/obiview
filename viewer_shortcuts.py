"""Viewer operations backing the full shortcut catalogue."""
import json
import random
from pathlib import Path
from gi.repository import Gtk, Gdk, GLib
from dialog_layout import StandardDialog
from shortcuts import BINDINGS, display_scales
from image_tools import selection_drag
from ui_theme import label, card


class ViewerShortcuts:
    def setup_shortcuts(self):
        self.zoom_locked=False
        self.view_mode='window'
        self.scale_y=self.scale
        self.fullscreen_info=True
        self.cursor_hidden=False
        self.span_monitors=False
        self.chrome={'menu':True,'toolbar':True,'status':True,'border':True}
        self.tags_path=self.viewer_config.parent/'tags.json'
        try:
            data=json.loads(self.tags_path.read_text())
            self.tags=set(data) if isinstance(data,list) and all(isinstance(p,str) for p in data) else set()
        except (OSError,ValueError): self.tags=set()
        self.fullscreen_label=label('', 'fullscreen-info',halign=Gtk.Align.START,valign=Gtk.Align.END,
                                    margin_start=16,margin_bottom=16,wrap=True)
        self.fullscreen_label.set_can_target(False); self.fullscreen_label.set_visible(False)
        self.canvas_overlay.add_overlay(self.fullscreen_label)
        self.tag_filter=Gtk.CheckButton(label='Nur markierte Bilder')
        self.tag_filter.connect('toggled',lambda *_:self.rebuild_thumbnails())
        self.sidebar.insert_child_after(self.tag_filter,self.search)
        self.connect('notify::fullscreened',self.fullscreen_changed)
        motion=Gtk.EventControllerMotion()
        motion.connect('motion',self.pointer_moved)
        self.canvas.add_controller(motion)
        self.cursor_timer=0

    def image_effect(self,name,amount=1):
        self.edit(lambda m:m.effect(name,amount))

    def toggle_select_all(self):
        if self.selection==(0,0,*self.model.image.size):
            self.selection=None; self.crop_toggle.set_active(False); self.refresh()
        else: self.select_all()

    def move_selection_key(self,direction):
        if not self.selection: return
        delta={'left':(-1,0),'right':(1,0),'up':(0,-1),'down':(0,1)}[direction]
        self.selection=selection_drag(self.selection,(0,0),delta,self.model.image.size,'move')
        self.refresh()

    def folder_edge(self,last):
        if self.folder_files:
            path=self.folder_files[-1 if last else 0]
            self.guard(lambda:self.request_load(path))

    def random_image(self):
        choices=[p for p in self.folder_files if p!=self.model.source_path]
        if choices:
            target=random.choice(choices); self.guard(lambda:self.request_load(target))

    def is_pannable(self):
        return any(a.get_upper()-a.get_page_size()>a.get_lower()+1 for a in
                   (self.scroll.get_hadjustment(),self.scroll.get_vadjustment()))

    def browse_or_scroll(self,direction):
        if not self.is_pannable():
            if direction in ('home','end'): self.folder_edge(direction=='end')
            else: self.navigate(-1 if direction in ('left','up','top') else 1)
            return
        horizontal=direction in ('left','right','home','end')
        adjustment=self.scroll.get_hadjustment() if horizontal else self.scroll.get_vadjustment()
        lower=adjustment.get_lower(); upper=max(lower,adjustment.get_upper()-adjustment.get_page_size())
        if direction in ('home','top'): value=lower
        elif direction in ('end','bottom'): value=upper
        else: value=adjustment.get_value()+(-1 if direction in ('left','up') else 1)*max(32,adjustment.get_step_increment())
        adjustment.set_value(max(lower,min(upper,value)))

    def center_view(self):
        for adjustment in (self.scroll.get_hadjustment(),self.scroll.get_vadjustment()):
            adjustment.set_value((adjustment.get_lower()+max(adjustment.get_lower(),adjustment.get_upper()-adjustment.get_page_size()))/2)

    def set_view_mode(self,mode):
        if mode=='actual': self.actual_size(); return
        self.view_mode=mode
        self.fit=mode in ('all','small','stretch','window')
        self.refresh()

    def number_view(self,number):
        if self.full: self.set_view_mode(('actual','small','all','stretch','width','height')[number-1])
        else: self.refresh_view()

    def refresh_view(self):
        self.refresh(True)

    def fit_toggle(self):
        if self.full:
            modes=('actual','small','all','stretch','width','height')
            current=modes.index(self.view_mode) if self.view_mode in modes else -1
            self.set_view_mode(modes[(current+1)%len(modes)])
        elif self.view_mode in ('screen','screen-small'):
            self.actual_size(); self.window_to_image()
        else: self.fit_desktop(False)

    def fit_desktop(self,only_large=False):
        if not self.model.image: return
        available=self.available_window_size()
        if not available: self.set_view_mode('small' if only_large else 'all'); return
        chrome=(max(0,self.get_width()-self.scroll.get_width()),max(0,self.get_height()-self.scroll.get_height()))
        viewport=(max(1,available[0]-chrome[0]-8),max(1,available[1]-chrome[1]-8))
        self.scale,self.scale_y=display_scales(self.model.image.size,viewport,'small' if only_large else 'all')
        self.fit=False; self.view_mode='screen-small' if only_large else 'screen'; self.refresh()

    def window_to_image(self):
        if self.full or not self.model.image: return
        available=self.available_window_size()
        if not available: return
        chrome=(max(0,self.get_width()-self.scroll.get_width()),max(0,self.get_height()-self.scroll.get_height()))
        w=round(self.model.image.width*self.scale)+chrome[0]+8
        h=round(self.model.image.height*self.scale_y)+chrome[1]+8
        self.fit=False; self.view_mode='manual'
        if w>=available[0] or h>=available[1]: self.maximize()
        else:
            self.unmaximize(); self.set_default_size(max(440,w),max(240,h))
        self.refresh()

    def toggle_zoom_lock(self):
        self.zoom_locked=not self.zoom_locked
        if self.zoom_locked:
            self.fit=False; self.view_mode='manual'; self.scale_y=self.scale
        self.refresh()

    def tag_image(self,tagged):
        path=self.model.source_path
        if path is None: return
        tags=set(self.tags); name=str(path.absolute())
        tags.add(name) if tagged else tags.discard(name)
        try:
            self.tags_path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.tags_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(sorted(tags),ensure_ascii=False)); temporary.replace(self.tags_path)
        except OSError as error: self.message('Markierung konnte nicht gespeichert werden',str(error)); return
        self.tags=tags; self.rebuild_thumbnails(); self.update_status()

    def show_tagged(self):
        if self.thumbnail_window is None: self.toggle_sidebar()
        self.search.set_text(''); self.tag_filter.set_active(True); self.rebuild_thumbnails()
        self.thumbnail_window.present()

    def copy_filename(self):
        if self.model.path: self.get_clipboard().set(self.model.path.name)

    def duplicate_window(self):
        window=self.new_window()
        if self.model.image is not None:
            # Copy working pixels rather than reloading the saved file.
            model=type(self.model)()
            model.image=self.model.image.copy(); model.path=self.model.path
            model.source_path=self.model.source_path; model.source_info=dict(self.model.source_info)
            model.exif=self.model.exif; model.icc=self.model.icc; model.comment=self.model.comment
            model.metadata=dict(self.model.metadata); model.xmp=self.model.xmp
            model.revision=1; model.next_revision=2
            window.adopt_model(model)
        return window

    def focus_thumbnails(self):
        if self.thumbnail_window is None: self.toggle_sidebar()
        self.thumbnail_window.present(); self.search.grab_focus()

    def cycle_thumbnail_focus(self):
        if self.thumbnail_window is None: self.toggle_sidebar()
        self.thumbnail_window.present()
        self.thumbnail_window.child_focus(Gtk.DirectionType.TAB_FORWARD)

    def thumbnail_key(self,controller,key,code,modifiers):
        if modifiers & Gdk.ModifierType.CONTROL_MASK and key in (Gdk.KEY_Tab,Gdk.KEY_ISO_Left_Tab):
            self.thumbnail_window.child_focus(Gtk.DirectionType.TAB_FORWARD); return True
        if not modifiers & (Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.ALT_MASK):
            if key==Gdk.KEY_Tab:
                self.present(); self.canvas.grab_focus(); return True
            if key==Gdk.KEY_Escape:
                self.thumbnail_window.close(); self.present(); return True
        return False

    def apply_chrome(self):
        self.menu_bar.set_visible(not self.full and self.chrome['menu'])
        self.toolbar.set_visible(not self.full and self.chrome['toolbar'])
        self.status.set_visible(not self.full and self.chrome['status'])
        self.header.set_visible(not self.full and self.chrome['border'])
        self.set_decorated(self.chrome['border'])
        self.fullscreen_label.set_visible(self.full and self.fullscreen_info)

    def toggle_chrome(self,part):
        self.chrome[part]=not self.chrome[part]; self.apply_chrome()

    def fullscreen_changed(self,*_):
        actual=self.is_fullscreen()
        if actual!=self.full:
            self.full=actual
            if not actual: self.restore_window_view()
        self.apply_chrome()

    def enter_fullscreen(self):
        self.window_view=(self.fit,self.scale,self.scale_y,self.view_mode)
        self.full=True
        self.view_mode='small'; self.fit=True
        self.apply_chrome(); self.fullscreen(); self.refresh()

    def restore_window_view(self):
        self.set_cursor_from_name('default')
        if self.cursor_timer: GLib.source_remove(self.cursor_timer); self.cursor_timer=0
        if hasattr(self,'window_view'):
            self.fit,self.scale,self.scale_y,self.view_mode=self.window_view
        self.apply_chrome(); self.refresh()

    def leave_fullscreen(self):
        self.full=False; self.unfullscreen(); self.restore_window_view()

    def escape_view(self):
        self.stop_slideshow()
        if self.full: self.leave_fullscreen()
        else: self.close()

    def toggle_fullscreen_text(self):
        if self.full:
            self.fullscreen_info=not self.fullscreen_info; self.apply_chrome()

    def fullscreen_cursor(self):
        if not self.full: self.enter_fullscreen(); return
        self.cursor_hidden=not self.cursor_hidden
        self.set_cursor_from_name('none' if self.cursor_hidden else 'default')

    def pointer_moved(self,*_):
        if self.full and self.cursor_hidden:
            self.set_cursor_from_name('default')
            if self.cursor_timer: GLib.source_remove(self.cursor_timer)
            def hide():
                self.cursor_timer=0
                if self.full and self.cursor_hidden: self.set_cursor_from_name('none')
                return False
            self.cursor_timer=GLib.timeout_add(1200,hide)

    def toggle_span(self):
        self.span_monitors=not self.span_monitors
        surface=self.get_surface()
        if surface:
            surface.set_property('fullscreen-mode',Gdk.FullscreenMode.ALL_MONITORS if self.span_monitors else Gdk.FullscreenMode.CURRENT_MONITOR)
        if not self.full: self.enter_fullscreen()
        else: self.fullscreen()

    def direct_print(self):
        if self.has_preview(): self.edit(lambda _m:None,after=self.direct_print); return
        values=getattr(self,'last_print_values',dict(orientation='portrait',mode='fit',width_cm=10,height_cm=10,
                    locked=True,scale_x=100,scale_y=100,centered=True,x_cm=0,y_cm=0))
        try: self.run_print(values,direct=True)
        except Exception as error: self.message('Drucken fehlgeschlagen',str(error))

    def shortcut_help(self):
        dialog=StandardDialog(title='Tastenkürzel',transient_for=self,modal=True)
        dialog.set_titlebar(Gtk.Box())
        close_button=dialog.add_button('Schließen',Gtk.ResponseType.CLOSE); close_button.add_css_class('primary')
        actions=close_button.get_parent()
        for side in ('start','end','bottom'): getattr(actions,'set_margin_'+side)(20)
        actions.set_margin_top(12)
        body=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16,margin_start=24,margin_end=24,margin_top=20,margin_bottom=20)
        body.append(label('Tastenkürzel','dialog-title'))
        body.append(label('Pfeiltasten scrollen vergrößerte Bilder; sonst wechseln sie Dateien. Strg+R bleibt Größe ändern.','muted',wrap=True))
        search=Gtk.SearchEntry(placeholder_text='Aktion oder Kürzel suchen …'); body.append(search)
        rows=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8)
        entries=[]
        for keys,_method,_args,_needs,title in BINDINGS:
            row=Gtk.Box(spacing=16); row.append(label(keys,hexpand=False,width_chars=22)); row.append(label(title,wrap=True,hexpand=True))
            rows.append(row); entries.append((row,(keys+' '+title).casefold()))
        search.connect('search-changed',lambda *_:[row.set_visible(search.get_text().casefold() in text) for row,text in entries])
        scroll=Gtk.ScrolledWindow(vexpand=True); scroll.set_child(rows); body.append(scroll)
        body.append(label('Strg+Umschalt+W fordert monitorübergreifendes Vollbild beim Fenstermanager an; Unterstützung hängt vom Desktop ab.','small muted',wrap=True))
        dialog.get_content_area().append(body)
        self.dialogs.append(dialog); self.set_scrim(True)
        def close(*_):
            if dialog in self.dialogs: self.dialogs.remove(dialog); self.set_scrim(False)
            dialog.destroy(); return True
        dialog.connect('response',close); dialog.connect('close-request',close)
        dialog.present(); return dialog

    def about_dialog(self):
        self.message('Über Bildblick','Bildblick · Native Bildanzeige und Bearbeitung für Linux.\nMIT-Lizenz · F1 zeigt alle Tastenkürzel.')
