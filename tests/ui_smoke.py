"""Actual GTK integration test; exit 77 when display access is denied."""
import sys
from pathlib import Path
import tempfile
import time
import traceback
import os
import base64
from PIL import Image, ImageDraw, ImageGrab, ImageEnhance, ImageFilter
from bildblick import Window, Gtk, Gdk, Gio, GLib
from image_tools import EFFECTS, EFFECT_PARAMETERS, mixed_effect
from image_tools import fine_rotate, frame, red_eye, reduce_colors, swap_channels, auto_crop, add_canvas
from edit_controls import SliderField, ChoiceButtons
from paint_dialog import paint_strokes

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
        if any(getattr(dialog,'pending_accept',False) for dialog in window.dialogs):
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
            window.unmaximize()
            window.set_default_size(720,640)
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
            assert window.menu_model.get_n_items()==6
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
                assert dialog.get_surface().get_width()==520 and dialog.get_surface().get_height()==760, (dialog.get_surface().get_width(),dialog.get_surface().get_height())
                assert dialog.body_scroll.get_height()>100, 'Scrollable effects body remains usable'
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
            def close_popovers(widget):
                if isinstance(widget,Gtk.Popover): widget.popdown()
                child=widget.get_first_child()
                while child:
                    close_popovers(child)
                    child=child.get_next_sibling()
            close_popovers(window.menu_bar)
            assert not window.dialogs and window.scrim_depth==0
            def rgba_result(image, result):
                result=result.convert('RGBA'); result.putalpha(image.getchannel('A')); return result
            window.tool_cases=[
                ('adjust_values_dialog',{'contrast':135},lambda im:rgba_result(im,ImageEnhance.Contrast(im.convert('RGB')).enhance(1.35))),
                ('filter_dialog',{'sharpness':125,'blur':2},lambda im:rgba_result(im,ImageEnhance.Sharpness(im.convert('RGB')).enhance(1.25).filter(ImageFilter.GaussianBlur(2)))),
                ('fine_rotation_dialog',{'angle':22},lambda im:fine_rotate(im,22)),
                ('border_dialog',{'style':'bevel','width':8},lambda im:frame(im,8,style='bevel')),
                ('red_eye_dialog',{'strength':65},lambda im:red_eye(im,(0,0,*im.size),65)),
                ('palette_dialog',{'colors':8,'dither':False},lambda im:reduce_colors(im,8,False)),
                ('swap_dialog',{'order':'GRB'},lambda im:swap_channels(im,'GRB')),
                ('auto_crop_dialog',{'tolerance':12},lambda im:auto_crop(im,12)),
                ('canvas_dialog',{'left':10,'right':0,'top':5,'bottom':0},lambda im:add_canvas(im,left=10,top=5)),
            ]
            window.tool_index=0; window.tool_phase=0
        elif step == 45:
            factory,changes,expected=window.tool_cases[window.tool_index]
            if window.tool_phase==0:
                window.tool_before=window.model.image.copy()
                window.tool_revision=window.model.revision
                window.tool_history=len(window.model.history)
                window.selection=(0,0,*window.model.image.size)
                dialog=getattr(window,factory)()
                for key,value in changes.items():
                    widget=dialog.widgets[key]
                    if isinstance(widget,ChoiceButtons):
                        widget.buttons[value].set_active(True)
                        assert sum(b.get_active() for b in widget.buttons.values())==1
                    elif isinstance(widget,Gtk.CheckButton): widget.set_active(value)
                    elif isinstance(widget,SliderField):
                        if widget.number is not None:
                            widget.number.set_value(value+1)
                            assert widget.scale.get_value()==widget.number.get_value()
                        widget.scale.set_value(value)
                        assert widget.get_value()==value
                    else: widget.set_value(value)
                if factory=='border_dialog': assert not dialog.widgets['inner_width'].get_sensitive()
                window.tool_phase=1
                return True
            elif window.tool_phase==1:
                dialog=window.dialogs[-1]
                if not dialog.preview_ready: return True
                assert window.model.revision==window.tool_revision
                assert window.model.image.tobytes()==window.tool_before.tobytes()
                result=expected(window.tool_before)
                assert bytes(dialog.preview_buffer.get_pixels())==result.tobytes(), factory
                dialog.compare.set_active(True); dialog.compare.set_active(False)
                if factory in ('adjust_values_dialog','border_dialog','swap_dialog','filter_dialog'):
                    screenshot(factory)
                dialog.reset()
                for key,_title,value,kind in dialog.fields:
                    if isinstance(kind,tuple): assert dialog.widgets[key].get_value()==value
                    elif isinstance(kind,list): assert dialog.widgets[key].get_active_id()==value
                delayed=None
                if factory=='adjust_values_dialog':
                    submit=window.submit; captured=[]
                    window.submit=lambda work,done,failure:captured.append((work,done,failure))
                    try:
                        GLib.source_remove(dialog.preview_timer); dialog.preview_timer=0
                        dialog.render_preview()
                    finally: window.submit=submit
                    work,done,failure=captured[0]; delayed=work()
                    dialog.widgets['contrast'].scale.set_value(99)
                    done(delayed)
                    assert not dialog.preview_ready
                dialog.response(Gtk.ResponseType.CANCEL)
                if delayed is not None:
                    done(delayed); failure(RuntimeError('late result'))
                assert window.model.image.tobytes()==window.tool_before.tobytes()
                assert not window.dialogs and window.scrim_depth==0
                dialog=getattr(window,factory)()
                for key,value in changes.items():
                    widget=dialog.widgets[key]
                    if isinstance(widget,ChoiceButtons): widget.set_active_id(value)
                    elif isinstance(widget,Gtk.CheckButton): widget.set_active(value)
                    else: widget.set_value(value)
                dialog.response(Gtk.ResponseType.ACCEPT)
                window.tool_phase=2
                return True
            else:
                assert window.model.image.tobytes()==expected(window.tool_before).tobytes(), factory
                assert len(window.model.history)==window.tool_history+1, factory
                window.undo()
                assert window.model.image.tobytes()==window.tool_before.tobytes(), factory
                window.tool_index+=1; window.tool_phase=0
                if window.tool_index<len(window.tool_cases): return True
        elif step == 46:
            dialog=window.paint_dialog()
            assert not dialog.undo_button.get_sensitive()
            assert isinstance(dialog.tool,ChoiceButtons) and isinstance(dialog.width,SliderField)
            dialog.tool.buttons['arrow'].set_active(True)
            dialog.width.scale.set_value(12)
            assert dialog.tool.get_active_id()=='arrow' and dialog.width.get_value()==12
            screenshot('drawing-choices')
            dialog.response(Gtk.ResponseType.CANCEL)
            window.resize_dialog()
            dialog=window.dialogs[-1]
            assert all(isinstance(w,ChoiceButtons) for w in (dialog.units,dialog.method,dialog.resolution))
            dialog.method.buttons['nearest'].set_active(True)
            assert dialog.method.get_active_id()=='nearest'
        elif step == 47:
            screenshot('resize-choices')
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.tool_before=window.model.image.copy()
            dialog=window.canvas_dialog()
            dialog.widgets['left'].set_value(-window.model.image.width)
            dialog.widgets['right'].set_value(0)
        elif step == 48:
            dialog=window.dialogs[-1]
            if not dialog.error.get_text(): return True
            assert not dialog.accept.get_sensitive() and not dialog.preview_ready
            assert window.model.image.tobytes()==window.tool_before.tobytes()
            dialog.widgets['left'].set_value(0)
        elif step == 49:
            dialog=window.dialogs[-1]
            if not dialog.preview_ready: return True
            assert dialog.accept.get_sensitive() and not dialog.error.get_text()
            dialog.response(Gtk.ResponseType.CANCEL)
            assert window.model.image.tobytes()==window.tool_before.tobytes()
            window.unmaximize(); window.set_default_size(720,640)
            window.request_load(sample)
        elif step == 50:
            window.set_focus(None)
            assert window.key_pressed(None,Gdk.KEY_i,0,Gdk.ModifierType(0))
            dialog=window.dialogs[-1]
            assert window.show_info() is dialog
            assert '960 × 600' in dialog.values['original_size'].get_text()
            assert dialog.values['filename'].get_text()=='sample.png'
            assert 'Millisekunden' in dialog.values['load_time'].get_text()
            window.info_pixels=window.model.image.tobytes()
            dialog.dpi_x.set_value(300); dialog.dpi_y.set_value(600)
            dialog.dpi_button.emit('clicked')
        elif step == 51:
            dialog=window.dialogs[-1]
            assert window.model.dpi_pair==(300,600)
            assert window.model.image.tobytes()==window.info_pixels
            assert '8.13 × 2.54 cm' in dialog.values['print_size'].get_text()
            if 'Berechnung' in dialog.count_label.get_text(): return True
            assert int(dialog.count_label.get_text().replace(' ',''))>2
            screenshot('image-information')
            for kind in ('exif','iptc','comment'):
                child=dialog.show_metadata(kind)
                buffer=child.text_view.get_buffer()
                assert buffer.get_text(*buffer.get_bounds(),False)
                child.response(Gtk.ResponseType.CLOSE)
            dialog.count_active.set_active(False)
            assert dialog.count_label.get_text()=='Deaktiviert'
            dialog.count_active.set_active(True)
            dialog.response(Gtk.ResponseType.CLOSE)
            assert not window.dialogs and window.scrim_depth==0
            window.undo()
            window.actual_size()
        elif step == 52:
            assert not window.is_maximized()
            window.grown_size=tuple(window.get_default_size())
            assert window.grown_size[0]>720 and window.grown_size[1]>640,window.grown_size
            assert window.scroll.get_width()>=960 and window.scroll.get_height()>=600
            window.zoom(1.25)
        elif step == 53:
            size=tuple(window.get_default_size())
            assert size[0]>window.grown_size[0] and size[1]>window.grown_size[1],size
            assert window.scale==1.25
            screenshot('zoom-grown')
            window.zoom(2)
        elif step == 54:
            if not window.is_maximized(): return True
            limit=window.available_window_size(); surface=window.get_surface()
            assert surface.get_width()<=limit[0] and surface.get_height()<=limit[1]
            assert window.scale==2.5 and not window.fit
            assert window.scroll.get_hadjustment().get_upper()>window.scroll.get_hadjustment().get_page_size()
            screenshot('zoom-screen-limit')
            window.zoom(.5)
        elif step == 55:
            assert window.is_maximized() and window.scale==1.25
            window.fit_image(); window.unmaximize(); window.set_default_size(720,640)
        elif step == 56:
            dialog=window.paint_dialog()
            assert set(dialog.tool_icons)=={'pen','brush','line','arrow','rectangle','ellipse'}
            dialog.tool.buttons['brush'].set_active(True)
            dialog.width.set_value(20)
        elif step == 57:
            dialog=window.dialogs[-1]
            screenshot('drawing-symbols')
            dialog.begin(None,200,200); dialog.update(None,60,15); dialog.end(None,120,30)
            window.paint_expected=paint_strokes(window.model.image,dialog.strokes).tobytes()
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 58:
            assert window.model.image.tobytes()==window.paint_expected
            window.undo()
            assert window.model.image.tobytes()==window.info_pixels
            window.set_focus(None)
            assert window.key_pressed(None,Gdk.KEY_Return,0,Gdk.ModifierType(0))
        elif step == 59:
            if not window.is_fullscreen(): return True
            assert not window.toolbar.get_visible() and not window.menu_bar.get_visible()
            assert window.fullscreen_label.get_visible()
            window.key_pressed(None,Gdk.KEY_4,0,Gdk.ModifierType(0))
        elif step == 60:
            assert window.view_mode=='stretch' and window.scale!=window.scale_y
            screenshot('fullscreen-shortcuts')
            window.key_pressed(None,Gdk.KEY_5,0,Gdk.ModifierType(0))
        elif step == 61:
            assert window.view_mode=='width' and window.scale==window.scale_y
            window.key_pressed(None,Gdk.KEY_6,0,Gdk.ModifierType(0))
        elif step == 62:
            assert window.view_mode=='height' and window.scale==window.scale_y
            window.key_pressed(None,Gdk.KEY_n,0,Gdk.ModifierType(0))
            assert not window.fullscreen_label.get_visible()
            window.key_pressed(None,Gdk.KEY_F11,0,Gdk.ModifierType(0))
            assert window.cursor_hidden
            window.key_pressed(None,Gdk.KEY_F11,0,Gdk.ModifierType(0))
            assert not window.cursor_hidden
            window.key_pressed(None,Gdk.KEY_w,0,Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK)
            assert window.get_surface().get_property('fullscreen-mode')==Gdk.FullscreenMode.ALL_MONITORS
            window.key_pressed(None,Gdk.KEY_w,0,Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK)
            assert window.get_surface().get_property('fullscreen-mode')==Gdk.FullscreenMode.CURRENT_MONITOR
            window.key_pressed(None,Gdk.KEY_Escape,0,Gdk.ModifierType(0))
        elif step == 63:
            if window.is_fullscreen(): return True
            assert window.toolbar.get_visible() and window.menu_bar.get_visible()
            mods=Gdk.ModifierType.ALT_MASK|Gdk.ModifierType.SHIFT_MASK
            for key,widget in ((Gdk.KEY_t,window.toolbar),(Gdk.KEY_s,window.status),(Gdk.KEY_m,window.menu_bar)):
                window.key_pressed(None,key,0,mods); assert not widget.get_visible()
                window.key_pressed(None,key,0,mods); assert widget.get_visible()
            window.actual_size(); window.zoom(3)
        elif step == 64:
            before=window.model.source_path
            h=window.scroll.get_hadjustment(); v=window.scroll.get_vadjustment()
            h.set_value(0)
            window.key_pressed(None,Gdk.KEY_Right,0,Gdk.ModifierType(0))
            assert h.get_value()>0 and window.model.source_path==before
            window.key_pressed(None,Gdk.KEY_Page_Down,0,Gdk.ModifierType(0))
            assert v.get_value()==v.get_upper()-v.get_page_size()
            window.key_pressed(None,Gdk.KEY_Home,0,Gdk.ModifierType(0)); assert h.get_value()==0
            window.key_pressed(None,Gdk.KEY_l,0,Gdk.ModifierType.SHIFT_MASK)
            assert window.zoom_locked
            window.locked_zoom=window.scale
            window.request_load(sample)
        elif step == 65:
            assert not window.fit and window.scale==window.locked_zoom
            window.key_pressed(None,Gdk.KEY_l,0,Gdk.ModifierType.SHIFT_MASK)
            window.fit_image()
            window.key_pressed(None,Gdk.KEY_x,0,Gdk.ModifierType(0))
            assert str(sample) in window.tags
            window.key_pressed(None,Gdk.KEY_q,0,Gdk.ModifierType.SHIFT_MASK)
            assert window.thumbnail_window and window.tag_filter.get_active()
        elif step == 66:
            assert window.thumbnails.get_first_child()
            window.search.set_text('no-such-image-redesign-test'); window.rebuild_thumbnails()
            assert window.thumb_empty.get_visible() and window.thumb_reset.get_visible()
            window.thumb_reset.emit('clicked')
            assert window.search.get_text()=='' and not window.tag_filter.get_active()
            assert not window.thumb_empty.get_visible() and window.thumbnails.get_first_child()
            window.thumbnail_key(None,Gdk.KEY_Tab,0,Gdk.ModifierType(0))
            window.set_focus(None)
            window.key_pressed(None,Gdk.KEY_x,0,Gdk.ModifierType.SHIFT_MASK)
            assert str(sample) not in window.tags
            window.toggle_sidebar()
            window.key_pressed(None,Gdk.KEY_F1,0,Gdk.ModifierType(0))
            assert window.dialogs[-1].get_title()=='Tastenkürzel'
            assert not window.key_pressed(None,Gdk.KEY_i,0,Gdk.ModifierType(0))
        elif step == 67:
            screenshot('shortcut-help')
            window.dialogs[-1].response(Gtk.ResponseType.CLOSE)
            window.set_focus(None)
            window.key_pressed(None,Gdk.KEY_p,0,Gdk.ModifierType.SHIFT_MASK)
            def got_text(clipboard,result):
                window.copied_name=clipboard.read_text_finish(result)
            window.copied_name=None
            window.get_clipboard().read_text_async(None,got_text)
        elif step == 68:
            if window.copied_name is None: return True
            assert window.copied_name==sample.name
            window.set_focus(None)
            window.key_pressed(None,Gdk.KEY_s,0,Gdk.ModifierType.CONTROL_MASK)
            assert window.dialogs
        elif step == 69:
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            window.model.rotate(); window.refresh()
            window.guard_actions=[]
            window.guard(lambda:window.guard_actions.append('continued'))
        elif step == 70:
            dialog=window.dialogs[-1]
            assert [b.get_label() for b in dialog.action_buttons]==['Abbrechen','Verwerfen','Speichern']
            assert dialog.get_surface().get_width()==520 and dialog.get_surface().get_height()<320
            scroll=dialog.body_scroll.get_vadjustment()
            assert scroll.get_upper()<=scroll.get_page_size()+1, 'Short confirmation text is clipped'
            screenshot('compact-unsaved')
            dialog._key(None,Gdk.KEY_Escape,0,Gdk.ModifierType(0))
            assert window.model.dirty and not window.guard_actions
            window.guard(lambda:window.guard_actions.append('discarded'))
            window.dialogs[-1].response(Gtk.ResponseType.REJECT)
            assert window.guard_actions==['discarded']
            window.guard(lambda:window.guard_actions.append('saved'))
            window.dialogs[-1].response(Gtk.ResponseType.ACCEPT)
        elif step == 71:
            assert window.dialogs[-1].get_title()=='Bild exportieren'
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            assert window.model.dirty and window.guard_actions==['discarded']
            window.guard(lambda:window.guard_actions.append('saved'))
            window.dialogs[-1].response(Gtk.ResponseType.ACCEPT)
            dialog=window.dialogs[-1]; dialog.folder.set_text(temporary.name)
            dialog.name.set_text('guard-saved.png'); dialog.format.set_active_id('PNG')
            dialog.resolution_tiles['full'].set_active(True)
            dialog.response(Gtk.ResponseType.ACCEPT)
        elif step == 72:
            assert (Path(temporary.name)/'guard-saved.png').is_file()
            assert not window.model.dirty and window.guard_actions==['discarded','saved']
            window.model.rotate(); window.refresh()
            occupied=Path(temporary.name)/'occupied.png'; occupied.mkdir()
            window.request_save(occupied,after=lambda:window.guard_actions.append('incorrect'))
            window.dialogs[-1].response(Gtk.ResponseType.ACCEPT)
        elif step == 73:
            assert window.model.dirty and window.guard_actions==['discarded','saved']
            assert window.dialogs[-1].get_title()=='Bearbeitung fehlgeschlagen'
            window.dialogs[-1].response(Gtk.ResponseType.CANCEL)
            print('PASS: GTK editing and shortcuts; compact save/discard/cancel prompt, cancelled export, successful save continuation and failed save protection')
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
