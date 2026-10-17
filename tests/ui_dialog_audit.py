"""Exercise every app-owned dialog family at the common footprint, including expanded states."""
import os, sys, tempfile, traceback, time, base64
from pathlib import Path
from PIL import Image, ImageGrab
from bildblick import Window, Gtk, Gdk, Gio, GLib
from dialog_layout import StandardDialog, module_window, dialog_size, control_count, children

scratch=tempfile.TemporaryDirectory(prefix='bildblick-dialog-audit-')
os.environ['XDG_CONFIG_HOME']=scratch.name
sample=Path(scratch.name)/'long-sample-name-for-dialog-width-check.png'
Image.new('RGB',(960,600),'#668877').save(sample)
app=Gtk.Application(application_id='local.bildblick.DialogAudit',flags=Gio.ApplicationFlags.NON_UNIQUE)
failures=[]; cases=[]; index=0; current=None; phase=0; started=time.monotonic()
VISUAL_TYPES=(Gtk.Button,Gtk.CheckButton,Gtk.Entry,Gtk.Scale,Gtk.DropDown,Gtk.Switch,Gtk.TextView,Gtk.Label,Gtk.Picture)

def capture(name):
    output=Path('tests/screenshots'); output.mkdir(exist_ok=True)
    target=output/('audit-'+name+'.png'); ImageGrab.grab().save(target)
    if os.environ.get('BILDBLICK_SCREENSHOT_LOG') and name in ('save_dialog','effects_dialog','paint_dialog','show_info','adjust_dialog','menu_0','menu_2'):
        print('SCREENSHOT audit-'+name+' '+base64.b64encode(target.read_bytes()).decode(),flush=True)

def expanded(widget):
    if isinstance(widget,Gtk.Expander): widget.set_expanded(True)
    for child in children(widget): expanded(child)

def clipped_items(scroll,root):
    clipped=[]
    def visit(widget):
        if widget.get_visible() and isinstance(widget,VISUAL_TYPES):
            ok,rect=widget.compute_bounds(scroll)
            if ok and (rect.get_y() < -1 or rect.get_y()+rect.get_height() > scroll.get_height()+1):
                clipped.append((type(widget).__name__,rect.get_y(),rect.get_height()))
        for child in children(widget): visit(child)
    visit(root)
    return clipped

def check(window,name):
    if isinstance(window,Gtk.PopoverMenu):
        monitor=window.get_display().get_monitor_at_surface(window.get_native().get_surface())
        bounds=monitor.get_geometry()
        assert 0<window.get_width()<=bounds.width-32,(name,'menu width',window.get_width())
        assert window.get_height()<=bounds.height-32,(name,'menu height',window.get_height())
        print('PASS MENU',name,window.get_width(),window.get_height(),flush=True)
        return
    elements=control_count(window.body) if isinstance(window,StandardDialog) else control_count(window.module_content)
    expected=dialog_size(window.get_transient_for(),elements)
    actual=(window.get_surface().get_width(),window.get_surface().get_height())
    parent=window.get_transient_for()
    display=window.get_display()
    surface=parent.get_surface() if parent else None
    monitor=display.get_monitor_at_surface(surface) if surface else None
    monitor=monitor or display.get_monitors().get_item(0)
    bounds=monitor.get_geometry()
    assert 0<actual[0]<=bounds.width-32 and 0<actual[1]<=bounds.height-32,(name,'screen bounds',actual,bounds.width,bounds.height)
    if isinstance(window,StandardDialog):
        # Check expanded content too: no horizontal clipping inside the body.
        width=window.body.get_width()
        allowed_width=bounds.width-32
        assert width<=allowed_width-48,(name,'body width',width,allowed_width)
        if name=='save_dialog':
            assert window.destination_section.get_visible()
            for entry in (window.name,window.folder):
                ancestor=entry.get_parent()
                while ancestor is not window:
                    assert not isinstance(ancestor,Gtk.Expander),'Destination hidden in expander'
                    ancestor=ancestor.get_parent()
        if name=='show_info':
            assert len(window.info_sections)==4 and len(window.values)==15
        def visit(widget):
            if isinstance(widget,Gtk.ToggleButton) and hasattr(widget,'selection_marker'):
                assert widget.selection_marker.get_opacity()==(1 if widget.get_active() else 0)
            if isinstance(widget,Gtk.SpinButton):
                assert widget.get_alignment()==1,(name,'numeric alignment',widget.get_value(),widget.get_alignment())
            if isinstance(widget,Gtk.Picture) and widget.has_css_class('preview-surface'):
                assert widget.get_content_fit()==Gtk.ContentFit.CONTAIN
            if widget.get_visible():
                assert widget.get_width()<=width+2,(name,type(widget).__name__,'overflows',widget.get_width(),width)
            for child in children(widget): visit(child)
        visit(window.body)
        for button in window.action_buttons:
            ok,rect=button.compute_bounds(window)
            assert ok and rect.get_y()>=0 and rect.get_y()+rect.get_height()<=actual[1],(name,'footer clipped')
        scroll=window.body_scroll.get_vadjustment()
        min_height,natural_height=window.body.measure(Gtk.Orientation.VERTICAL,max(240,window.body.get_width()))[:2]
        clipped=clipped_items(window.body_scroll,window.body)
        needs_scroll=bool(clipped)
        print(f'AUDIT {name}: controls={elements}, width-target={expected[0]}, actual={actual[0]}x{actual[1]}, body-min/natural={min_height}/{natural_height}, scroll-needed={needs_scroll}, clipped={clipped[:3]}',flush=True)
        scroll.set_value(max(0,scroll.get_upper()-scroll.get_page_size()))
    else:
        print(f'AUDIT {name}: controls={elements}, width-target={expected[0]}, actual={actual[0]}x{actual[1]}',flush=True)
    print('PASS DIALOG',name,actual,flush=True)

def tick(w):
    global index,current,phase
    try:
        if time.monotonic()-started>90: raise TimeoutError('dialog audit timed out')
        if w.busy or not w.folder_files: return True
        if index==len(cases):
            print(f'{"FAIL" if failures else "PASS"}: {len(cases)} dialog/module/menu cases, common geometry, expanded content and fixed actions',flush=True)
            w.cleanup(); app.quit(); return False
        name,factory=cases[index]
        if phase==0:
            current=factory()
            if current is None: current=w.dialogs[-1]
            expanded(current); phase=1; return True
        try: check(current,name)
        except AssertionError: failures.append(traceback.format_exc())
        capture(name)
        if isinstance(current,StandardDialog): current.response(Gtk.ResponseType.CANCEL)
        elif isinstance(current,Gtk.PopoverMenu): current.popdown(); current.unparent()
        else: current.close()
        index+=1;phase=0
    except Exception:
        failures.append(traceback.format_exc());w.cleanup();app.quit();return False
    return True

def activate(application):
    w=Window(application);w.present();w.request_load(sample)
    names=['save_dialog','resize_dialog','effects_dialog','adjust_dialog','adjust_values_dialog','filter_dialog',
           'paint_dialog','show_info','fine_rotation_dialog','border_dialog','canvas_dialog','selection_dialog',
           'text_dialog','blank_dialog','auto_crop_dialog','palette_dialog','swap_dialog',
           'preferences_dialog','slideshow_settings','export_options','print_image','shortcut_help','recent_folders']
    cases.extend((name,getattr(w,name)) for name in names)
    from save_options import FORMAT_CHOICES
    def export_format(fmt):
        w.save_dialog(); d=w.dialogs[-1]; d.format.set_active_id(fmt)
        d.resolution_tiles['custom'].set_active(True)
        return d
    cases.extend(('export_'+fmt,lambda fmt=fmt:export_format(fmt)) for fmt in FORMAT_CHOICES)
    model=w.menu_bar.get_menu_model()
    def menu(i):
        popover=Gtk.PopoverMenu.new_from_model(model.get_item_link(i,'submenu'))
        popover.set_parent(w.menu_bar)
        anchor=Gdk.Rectangle(); anchor.x=8; anchor.y=0; anchor.width=1; anchor.height=w.menu_bar.get_height()
        popover.set_pointing_to(anchor); popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_has_arrow(False); popover.popup();return popover
    cases.extend(('menu_'+str(i),lambda i=i:menu(i)) for i in range(model.get_n_items()))
    def metadata():
        info=w.show_info(); child=info.show_metadata('exif')
        child.connect('response',lambda *_:info.close_dialog()); return child
    cases.append(('metadata',metadata))
    def red_eye(): w.selection=(10,10,100,100); return w.red_eye_dialog()
    cases.append(('red_eye',red_eye))
    cases.append(('rename',lambda:w.file_action('rename')))
    def panorama():
        choose=w.choose
        try:
            w.choose=lambda _title,callback,**kwargs:callback([sample,sample])
            w.panorama_dialog()
        finally: w.choose=choose
    cases.append(('panorama',panorama))
    def message(): w.message('Eine sehr lange Meldung mit verständlichem Titel','/long/path/'*100)
    cases.append(('message',message))
    cases.append(('batch_options',lambda:w.batch_options([sample],Path(scratch.name))))
    def thumbs(): w.toggle_sidebar(); return w.thumbnail_window
    cases.append(('thumbnails',thumbs));cases.append(('histogram',w.histogram_dialog))
    def media():
        window=module_window(w,'Medienwiedergabe'); window.set_child(Gtk.Video());window.present();return window
    cases.append(('media',media))
    # Progress uses the same shell, without executing or cancelling real batch work.
    def progress():
        d=StandardDialog(title='Stapelverarbeitung',transient_for=w,modal=True)
        d.add_button('Nach aktueller Datei abbrechen',Gtk.ResponseType.CANCEL)
        d.get_content_area().append(Gtk.Label(label='12 / 24 · '+sample.name,wrap=True))
        d.connect('response',lambda *_:d.destroy());d.present();return d
    cases.append(('batch_progress',progress))
    GLib.timeout_add(350,tick,w)

app.connect('activate',activate);app.run([sys.argv[0]])
if failures: print('\n'.join(failures),file=sys.stderr);sys.exit(1)
