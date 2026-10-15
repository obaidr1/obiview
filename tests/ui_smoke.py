"""Actual GTK integration test; exit 77 when display access is denied."""
import sys
from pathlib import Path
import tempfile
import time
import traceback
import os
import base64
from PIL import Image, ImageDraw, ImageGrab
from bildblick import Window, Gtk, Gdk, Gio, GLib

Gtk.init()
if Gdk.Display.get_default() is None:
    print('BLOCKED: no display connection; GUI checks were not executed.',file=sys.stderr)
    raise SystemExit(77)

root = Path(__file__).resolve().parents[1]
temporary = tempfile.TemporaryDirectory(prefix='bildblick-ui-')
sample = Path(temporary.name)/'sample.png'
image = Image.new('RGB',(960,600),'#162e48')
draw = ImageDraw.Draw(image)
for y in range(600):
    draw.line((0,y,960,y),fill=(22+y//12,46+y//8,72+y//6))
draw.ellipse((610,70,790,250),fill='#f4c87b')
draw.polygon([(0,500),(250,140),(520,500)],fill='#254c65')
draw.polygon([(240,600),(620,210),(960,600)],fill='#387b83')
draw.polygon([(0,600),(0,480),(330,350),(700,600)],fill='#193d4b')
draw.text((44,40),'BILDBLICK / LINUX',fill='white',font_size=32)
draw.text((44,84),'Native Anzeige und Bildbearbeitung',fill='#b9d8e6',font_size=18)
image.save(sample)
Image.new('RGB',(100,100),'blue').save(Path(temporary.name)/'second.png')
app = Gtk.Application(application_id='local.bildblick.Smoke',flags=Gio.ApplicationFlags.NON_UNIQUE)
failed = []
step = 0
started = time.monotonic()

def screenshot(name):
    output = root/'tests'/'screenshots'
    output.mkdir(exist_ok=True)
    target = output/(name+'.png')
    ImageGrab.grab().save(target)
    if os.environ.get('BILDBLICK_SCREENSHOT_LOG'):
        # Synthetic test image only; enables review when artifact downloads are unavailable.
        print('SCREENSHOT '+name+' '+base64.b64encode(target.read_bytes()).decode())


def tick(window):
    global step
    try:
        if time.monotonic()-started>30:
            raise TimeoutError('GUI test timed out')
        if window.busy or not window.folder_files:
            return True
        if step == 0:
            assert window.pixbuf and window.canvas.get_width()>100
            window.actual_size()
            window.zoom(1.25)
            assert window.scale==1.25
            window.rotate(True)
        elif step == 1:
            assert window.model.image.size==(600,960)
            window.undo()
            assert window.model.image.size==(960,600)
            window.redo()
            assert window.model.image.size==(600,960)
            window.undo()
            window.fit_image()
        elif step == 2:
            window.crop_toggle.set_active(True)
            ox,oy = window.origin
            scale = window.scale
            window.begin_drag(None,ox+100*scale,oy+80*scale)
            window.end_drag(None,500*scale,360*scale)
            assert window.selection is not None
            window.apply_crop()
        elif step == 3:
            assert abs(window.model.image.width-500)<=1
            assert abs(window.model.image.height-360)<=1
            window.request_save(Path(temporary.name)/'cropped.png')
        elif step == 4:
            assert (Path(temporary.name)/'cropped.png').exists()
            assert not window.model.dirty
            window.request_load(sample)
        elif step == 5:
            window.toggle_sidebar()
            window.navigate(1)
        elif step == 6:
            assert window.model.source_path.name=='second.png'
            window.navigate(-1)
        elif step == 7:
            assert window.model.source_path==sample
            window.toggle_slideshow()
            assert window.playing
            window.stop_slideshow()
            assert not window.playing
            window.toggle_fullscreen()
            window.toggle_fullscreen()
        elif step == 8:
            assert window.menu_model.get_n_items()==5
            window.extra_key(Gdk.KEY_r,Gdk.ModifierType.CONTROL_MASK)
            dialog = window.dialogs[-1]
            dialog.height.set_value(300)
            assert dialog.width.get_value_as_int()==480
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 9:
            assert window.model.image.size==(480,300)
            window.undo()
            assert window.model.image.size==(960,600)
            window.lookup_action('resize').activate(None)
            dialog = window.dialogs[-1]
            dialog.response(Gtk.ResponseType.CANCEL)
            assert window.model.image.size==(960,600)
        elif step == 10:
            window.save_dialog()
            dialog = window.dialogs[-1]
            dialog.format.set_active_id('JPEG')
            assert dialog.name.get_text().endswith('.jpg')
            assert dialog.stack.get_visible_child_name()=='JPEG'
            dialog.response(Gtk.ResponseType.CANCEL)
            assert not window.dialogs
            assert not (Path(temporary.name)/'sample-bearbeitet.jpg').exists()
        elif step == 11:
            window.key_pressed(None,Gdk.KEY_S,0,Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK)
            dialog = window.dialogs[-1]
            dialog.format.set_active_id('JPEG')
            dialog.name.set_text('dialog-save.jpg')
            dialog.folder.set_text(temporary.name)
            dialog.checks['progressive'].set_active(True)
            dialog.checks['grayscale'].set_active(True)
            dialog.quality.set_value(81)
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 12:
            with Image.open(Path(temporary.name)/'dialog-save.jpg') as saved:
                assert saved.mode=='L' and saved.info.get('progressive')
            assert window.model.image.mode=='RGBA'
            assert not window.dialogs
            assert window.save_settings.quality==81
            window.request_load(sample)
        elif step == 13:
            window.adjust_sliders['brightness'].set_value(20)
        elif step == 14:
            if window.preview_running or window.preview_timer or window.preview_pixbuf is None:
                return True
            assert window.has_preview() and not window.model.dirty
            original = window.model.image.tobytes()
            window.undo()
            assert not window.has_preview() and window.model.image.tobytes()==original
            window.look_buttons['Warm'].set_active(True)
            window.edit(lambda _m:None)
        elif step == 15:
            assert window.model.dirty and not window.has_preview()
            window.undo()
            assert not window.model.dirty
            window.save_dialog()
            dialog = window.dialogs[-1]
            dialog.format.set_active_id('PNG')
            dialog.resolution_tiles['half'].set_active(True)
            dialog.remove_metadata.set_active(True)
            dialog.name.set_text('half.png')
            dialog.folder.set_text(temporary.name)
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 16:
            with Image.open(Path(temporary.name)/'half.png') as result:
                assert result.size==(480,300)
            assert window.model.image.size==(960,600)
            window.toggle_sidebar()
            window.set_default_size(1280,900)
        elif step == 17:
            assert window.inspector_scroll.get_width()<400, window.inspector_scroll.get_width()
            screenshot('editor')
            window.save_dialog()
            window.dialogs[-1].format.set_active_id('JPEG')
            window.dialogs[-1].resolution_tiles['full'].set_active(True)
        elif step == 18:
            if window.dialogs[-1].preview_busy or window.dialogs[-1].preview_timer:
                return True
            assert 'KB' in window.dialogs[-1].size_label.get_text()
            screenshot('export')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.set_default_size(1024,768)
        elif step == 19:
            screenshot('compact')
            assert window.get_width()<=1024, f'Window minimum too wide: {window.get_width()}'
            window.extra_key(Gdk.KEY_r,Gdk.ModifierType.CONTROL_MASK)
        elif step == 20:
            screenshot('resize')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            print('PASS: GTK image operations/navigation/slideshow/fullscreen/menu/resize/Ctrl+R/save dialog + screenshot')
            window.cleanup()
            app.quit()
            return False
        step += 1
    except Exception:
        failed.append(traceback.format_exc())
        window.cleanup()
        app.quit()
        return False
    return True

def activate(application):
    try:
        window = Window(application)
        window.present()
        window.request_load(sample)
        GLib.timeout_add(250,tick,window)
    except Exception:
        failed.append(traceback.format_exc())
        app.quit()

app.connect('activate',activate)
app.run([sys.argv[0]])
temporary.cleanup()
if failed:
    print('\n'.join(failed),file=sys.stderr)
    raise SystemExit(1)
