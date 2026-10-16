"""Exercise every app-owned dialog family at the common footprint, including expanded states."""
import os, sys, tempfile, traceback, time, base64
from pathlib import Path
from PIL import Image, ImageGrab
from bildblick import Window, Gtk, Gio, GLib
from dialog_layout import StandardDialog, module_window, dialog_size, children

scratch=tempfile.TemporaryDirectory(prefix='bildblick-dialog-audit-')
os.environ['XDG_CONFIG_HOME']=scratch.name
sample=Path(scratch.name)/'long-sample-name-for-dialog-width-check.png'
Image.new('RGB',(960,600),'#668877').save(sample)
app=Gtk.Application(application_id='local.bildblick.DialogAudit',flags=Gio.ApplicationFlags.NON_UNIQUE)
failures=[]; cases=[]; index=0; current=None; phase=0; started=time.monotonic()

def capture(name):
    output=Path('tests/screenshots'); output.mkdir(exist_ok=True)
    target=output/('audit-'+name+'.png'); ImageGrab.grab().save(target)
    if os.environ.get('BILDBLICK_SCREENSHOT_LOG') and name in ('save_dialog','effects_dialog','paint_dialog','show_info','adjust_dialog'):
        print('SCREENSHOT audit-'+name+' '+base64.b64encode(target.read_bytes()).decode(),flush=True)

def expanded(widget):
    if isinstance(widget,Gtk.Expander): widget.set_expanded(True)
    for child in children(widget): expanded(child)

def check(window,name):
    expected=dialog_size(window.get_transient_for())
    actual=(window.get_width(),window.get_height())
    assert actual==expected,(name,'geometry',actual,expected)
    if isinstance(window,StandardDialog):
        # Check expanded content too: no horizontal clipping inside the body.
        width=window.body.get_width()
        assert width<=expected[0]-48,(name,'body width',width)
        def visit(widget):
            if widget.get_visible():
                assert widget.get_width()<=width+2,(name,type(widget).__name__,'overflows',widget.get_width(),width)
            for child in children(widget): visit(child)
        visit(window.body)
        for button in window.action_buttons:
            ok,rect=button.compute_bounds(window)
            assert ok and rect.get_y()>=0 and rect.get_y()+rect.get_height()<=expected[1],(name,'footer clipped')
        scroll=window.body_scroll.get_vadjustment()
        scroll.set_value(max(0,scroll.get_upper()-scroll.get_page_size()))
    print('PASS DIALOG',name,actual,flush=True)

def tick(w):
    global index,current,phase
    try:
        if time.monotonic()-started>90: raise TimeoutError('dialog audit timed out')
        if w.busy or not w.folder_files: return True
        if index==len(cases):
            print(f'PASS: {len(cases)} dialog/module cases, common geometry, expanded content and fixed actions',flush=True)
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
    def metadata():
        info=w.show_info(); child=info.show_metadata('exif')
        child.connect('response',lambda *_:info.close_dialog()); return child
    cases.append(('metadata',metadata))
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
