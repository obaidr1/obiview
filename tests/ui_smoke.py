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
from image_tools import EFFECTS, EFFECT_PARAMETERS, mixed_effect

Gtk.init()
if Gdk.Display.get_default() is None:
    print('BLOCKED: no display connection; GUI checks were not executed.',file=sys.stderr)
    raise SystemExit(77)

root = Path(__file__).resolve().parents[1]
temporary = tempfile.TemporaryDirectory(prefix='bildblick-ui-')
os.environ['XDG_CONFIG_HOME']=str(Path(temporary.name)/'config')
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
def uncaught(kind, error, tb):
    failed.append(''.join(traceback.format_exception(kind,error,tb)))
    app.quit()

sys.excepthook = uncaught
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
        if time.monotonic()-started>90:
            raise TimeoutError('GUI test timed out')
        if window.busy or not window.folder_files:
            return True
        if step == 0:
            assert window.pixbuf and window.canvas.get_width()>100
            assert window.get_surface().get_width()==720 and window.get_surface().get_height()==640, (window.get_surface().get_width(),window.get_surface().get_height())
            assert window.menu_bar.get_visible()
            assert window.canvas.get_width()>=window.get_width()-16
            screenshot('startup')
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
            assert window.thumbnail_window is not None
            window.toggle_sidebar()
            assert window.thumbnail_window is None
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
            window.adjust_dialog()
            assert window.editor_dialog is not None
            window.adjust_sliders['brightness'].set_value(20)
        elif step == 14:
            if window.preview_running or window.preview_timer or window.preview_pixbuf is None:
                return True
            assert window.has_preview() and not window.model.dirty
            original = window.model.image.tobytes()
            window.undo()
            assert not window.has_preview() and window.model.image.tobytes()==original
            window.editor_dialog.response(Gtk.ResponseType.CANCEL)
            window.adjust_dialog()
            window.look_buttons['Warm'].set_active(True)
            window.editor_dialog.response(Gtk.ResponseType.ACCEPT)
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
            window.set_default_size(720,640)
        elif step == 17:
            assert window.inspector_panel.get_parent() is None
            assert window.canvas.get_width()>=window.get_width()-16
            assert window.get_surface().get_width()==720 and window.get_surface().get_height()==640
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
            window.set_default_size(960,720)
        elif step == 19:
            screenshot('compact')
            assert window.get_width()<=960, f'Window minimum too wide: {window.get_width()}'
            window.extra_key(Gdk.KEY_r,Gdk.ModifierType.CONTROL_MASK)
        elif step == 20:
            screenshot('resize')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.adjust_dialog()
        elif step == 21:
            screenshot('adjust')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            assert not window.dialogs
        elif step == 22:
            window.resize_dialog()
            dialog=window.dialogs[-1]
            dialog.dpi.set_value(300)
            dialog.units.set_active_id('cm')
            dialog.width.set_value(2.54)
            assert dialog.settings.dimensions()==(300,188)
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 23:
            assert window.model.image.size==(300,188) and window.model.dpi==300, (window.model.image.size,window.model.dpi)
            window.undo()
            dialog=window.selection_dialog()
            dialog.widgets['width'].set_value(320)
            dialog.widgets['ratio'].set_active_id('1')
            dialog.response(Gtk.ResponseType.ACCEPT)
            assert window.selection==(0,0,320,320)
            # Edge resize and right-button movement retain the selection.
            ox,oy=window.origin; scale=window.scale
            window.begin_drag(None,ox+320*scale,oy+160*scale)
            window.end_drag(None,20*scale,0)
            assert window.selection[2]==340
            class RightDrag:
                def get_current_button(self): return 3
            window.begin_drag(RightDrag(),ox+100*scale,oy+100*scale)
            window.end_drag(RightDrag(),10*scale,20*scale)
            assert window.selection==(10,20,350,340)
            window.clipboard_expected=window.model.image.crop(window.selection).tobytes()
            window.copy_image()
            window.crop_toggle.set_active(False)
            window.clear_image()
            assert window.model.image is None
            window.paste_image()
        elif step == 24:
            assert window.model.image.size==(340,320)
            assert window.model.image.tobytes()==window.clipboard_expected
            assert window.model.source_path is None and window.model.dirty
            # Saving a clipboard document must work without an original file.
            window.request_save(Path(temporary.name)/'clipboard.png')
        elif step == 25:
            assert (Path(temporary.name)/'clipboard.png').is_file()
            dialog=window.canvas_dialog()
            dialog.widgets['left'].set_value(1); dialog.widgets['right'].set_value(3)
            dialog.widgets['top'].set_value(2); dialog.widgets['bottom'].set_value(4)
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 26:
            assert window.model.image.size==(344,326)
            window.undo()
            dialog=window.border_dialog(); dialog.widgets['style'].set_active_id('double')
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 27:
            assert window.model.image.size==(384,364)
            window.undo()
            dialog=window.fine_rotation_dialog(); dialog.widgets['angle'].set_value(90)
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 28:
            assert window.model.image.size==(320,340)
            window.undo()
            window.effect_before=window.model.image.copy()
            window.effect_revision=window.model.revision
            window.effect_history=len(window.model.history)
            window.effects_phase=0
            dialog=window.effects_dialog()
            assert window.effects_dialog() is dialog
        elif step == 29:
            phase=window.effects_phase
            if phase < 3:
                dialog=window.dialogs[-1]
                if not dialog.ready: return True
                assert window.model.revision==window.effect_revision
                assert window.model.image.tobytes()==window.effect_before.tobytes()
            if phase == 0:
                assert len(dialog.buttons)==10 and set(dialog.buttons)==set(EFFECTS)
                assert not dialog.amount_row.get_visible()
                for name, button in dialog.buttons.items():
                    button.set_active(True)
                    assert dialog.name==name
                    assert dialog.amount_row.get_visible()==(name in EFFECT_PARAMETERS)
                dialog.buttons['pixelize'].set_active(True)
                dialog.amount.set_value(22); dialog.strength.set_value(40)
                window.effects_phase=1
                return True
            if phase == 1:
                expected=mixed_effect(window.effect_before,'pixelize',22,40)
                assert bytes(dialog.preview.get_pixels())==expected.tobytes()
                dialog.compare.set_active(True)
                assert dialog.picture.get_paintable().get_width()==window.effect_before.width
                dialog.compare.set_active(False)
                adjustment=dialog.controls_scroll.get_vadjustment()
                assert adjustment.get_upper() <= adjustment.get_page_size()+1, 'Effect controls must fit at the default dialog size'
                screenshot('effects')
                # Hold one completed worker to exercise stale and post-close delivery.
                submit=window.submit
                captured=[]
                window.submit=lambda work, done, failure: captured.append((work,done,failure))
                try:
                    dialog.strength.set_value(41)
                    GLib.source_remove(dialog.timer); dialog.timer=0
                    dialog.render()
                finally:
                    window.submit=submit
                work,done,failure=captured[0]
                dialog.buttons['sepia'].set_active(True)
                done(work())
                assert not dialog.ready and not dialog.accept.get_sensitive()
                dialog.buttons['pixelize'].set_active(True)
                assert dialog.amount.get_value()==22 and dialog.strength.get_value()==41
                dialog.reset()
                assert dialog.amount.get_value()==5 and dialog.strength.get_value()==100
                # Cancel while another preview is pending; it must not touch history.
                dialog.response(Gtk.ResponseType.CANCEL)
                done(expected)
                failure(RuntimeError('delayed preview error'))
                assert dialog.closed and not dialog.timer
                assert not window.dialogs and window.scrim_depth==0
                window.effects_dialog()
                window.effects_phase=2
                return True
            if phase == 2:
                dialog.response(Gtk.ResponseType.ACCEPT)
                window.effects_phase=3
                return True
            assert window.model.image.tobytes()==mixed_effect(window.effect_before,'sepia').tobytes()
            assert len(window.model.history)==window.effect_history+1
            window.undo()
            assert window.model.image.tobytes()==window.effect_before.tobytes()
            window.selection=(0,0,100,100)
            dialog=window.red_eye_dialog(); dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 30:
            window.undo()
            dialog=window.text_dialog(); dialog.widgets['text'].get_buffer().set_text('Bildblick')
            dialog.widgets['font'].set_font('Sans Bold Italic 48')
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 31:
            assert window.model.dirty
            window.undo()
            window.adjust_dialog(); window.adjust_sliders['gamma'].set_value(20)
            window.adjust_sliders['red'].set_value(10)
        elif step == 32:
            if window.preview_running or window.preview_timer or window.preview_pixbuf is None: return True
            window.editor_dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 33:
            assert window.model.dirty
            window.undo()
            dialog=window.preferences_dialog(); color=Gdk.RGBA(); color.parse('#344455')
            dialog.widgets['background'].set_rgba(color); dialog.response(Gtk.ResponseType.ACCEPT)
            assert window.background=='#344455' and window.viewer_config.exists()
            dialog=window.print_image()
            dialog.widgets['mode'].set_active_id('custom')
            dialog.widgets['height_cm'].set_value(10)
            assert abs(dialog.widgets['width_cm'].get_value()-10*340/320)<.02
            values=dialog.values(); dialog.response(Gtk.ResponseType.CANCEL)
            target=Path(temporary.name)/'print.pdf'
            window.run_print(values,export_path=target)
            assert target.read_bytes().startswith(b'%PDF-') and target.stat().st_size>1000
        elif step == 34:
            dialog=window.file_action('rename')
            dialog.widgets['name'].set_text('renamed.png'); dialog.response(Gtk.ResponseType.ACCEPT)
            assert window.model.path.name=='renamed.png' and window.model.path.is_file()
            assert not (Path(temporary.name)/'clipboard.png').exists()
            window.lookup_action('custom-selection').activate(None)
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            dialog=window.palette_dialog(); dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 35:
            assert window.model.dirty
            window.undo()
            dialog=window.paint_dialog()
        elif step == 36:
            dialog=window.dialogs[-1]
            dialog.begin(None,100,100); dialog.end(None,150,100)
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 37:
            assert window.model.dirty
            window.undo()
            window.select_all()
            window.selection=(10,10,50,40)
            window.extra_key(Gdk.KEY_y,Gdk.ModifierType.CONTROL_MASK)
        elif step == 38:
            assert window.model.image.size==(40,30)
            window.undo()
            window.extra_key(Gdk.KEY_z,Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK)
            assert window.model.image.size==(40,30)
            window.undo()
            # A second native window starts empty, with the same compact surface size.
            second=window.new_window(); second.allow_close=True; second.close()
            assert not window.dialogs and window.scrim_depth==0
            window.selection_dialog()
        elif step == 39:
            screenshot('selection')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.border_dialog()
        elif step == 40:
            screenshot('frame')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.text_dialog()
        elif step == 41:
            screenshot('text')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.print_image()
        elif step == 42:
            screenshot('print')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.paint_dialog()
        elif step == 43:
            screenshot('paint')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.menu_bar.get_first_child().activate()
        elif step == 44:
            screenshot('file-menu')
            assert not window.dialogs and window.scrim_depth==0
            print('PASS: GTK core + physical resize/DPI, selection move/resize, clipboard, frame, canvas, rotation, effects, text, gamma/RGB, preferences, print PDF, rename, palette, painting, shortcuts')
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
