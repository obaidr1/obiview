import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from PIL import Image
from bildblick import Window, Gdk, Gtk
from image_model import ImageModel
from shortcuts import BINDINGS, dispatch, normalized_key, display_scales
from viewer_shortcuts import ViewerShortcuts

C=Gdk.ModifierType.CONTROL_MASK
S=Gdk.ModifierType.SHIFT_MASK
A=Gdk.ModifierType.ALT_MASK
Z=Gdk.ModifierType(0)

class ShortcutTests(unittest.TestCase):
    def viewer(self):
        v=Mock(); v.model=ImageModel(); v.model.image=Image.new('RGBA',(100,50)); v.full=False
        return v

    def test_catalogue_has_real_handlers_and_no_duplicate_bindings(self):
        self.assertEqual(len(BINDINGS),len({key.lower() for key,*_ in BINDINGS}))
        for key,method,*_ in BINDINGS:
            self.assertTrue(callable(getattr(Window,method,None)),(key,method))
        self.assertGreater(len(BINDINGS),90)

    def test_conflicting_old_keys_follow_requested_mapping(self):
        v=self.viewer()
        for key,mods,method in [(Gdk.KEY_Return,Z,'toggle_fullscreen'),(Gdk.KEY_F5,Z,'refresh_view'),
             (Gdk.KEY_s,C,'save_dialog'),(Gdk.KEY_p,C|A,'direct_print'),(Gdk.KEY_y,C|S,'auto_crop_dialog'),
             (Gdk.KEY_n,C,'duplicate_window'),(Gdk.KEY_n,S,'blank_dialog'),(Gdk.KEY_r,C,'resize_dialog')]:
            v.reset_mock(); self.assertTrue(dispatch(v,key,mods)); getattr(v,method).assert_called_once_with()
        v.apply_crop.assert_not_called(); v.save_current.assert_not_called()

    def test_modifiers_are_exact_and_super_never_edits(self):
        v=self.viewer()
        for mods in (C|A,A,Gdk.ModifierType.SUPER_MASK,C|S):
            self.assertFalse(dispatch(v,Gdk.KEY_r,mods))
        v.rotate.assert_not_called(); v.resize_dialog.assert_not_called()
        self.assertTrue(dispatch(v,Gdk.KEY_R,S)); v.reopen.assert_called_once_with()
        self.assertEqual(normalized_key(Gdk.KEY_plus,S),'plus')
        self.assertEqual(normalized_key(Gdk.KEY_H,Gdk.ModifierType.LOCK_MASK),'h')

    def test_empty_document_and_fullscreen_number_context(self):
        v=self.viewer(); v.model.image=None
        self.assertTrue(dispatch(v,Gdk.KEY_Delete,Z)); v.file_action.assert_not_called()
        self.assertTrue(dispatch(v,Gdk.KEY_F1,Z)); v.shortcut_help.assert_called_once_with()
        v.model.image=Image.new('RGBA',(2,2))
        self.assertFalse(dispatch(v,Gdk.KEY_4,Z)); v.number_view.assert_not_called()
        v.full=True; self.assertTrue(dispatch(v,Gdk.KEY_4,Z)); v.number_view.assert_called_once_with(4)

    def test_numeric_jumps_are_signed_and_page_keys_distinct(self):
        v=self.viewer()
        for n in range(1,10):
            for shift,direction in [(Z,n),(S,-n)]:
                dispatch(v,Gdk.KEY_0+n,C|shift); v.navigate.assert_called_with(direction)
        dispatch(v,Gdk.KEY_Page_Down,C); v.change_frame.assert_called_once_with(1)
        dispatch(v,Gdk.KEY_Page_Down,Z); v.browse_or_scroll.assert_called_once_with('bottom')

    def test_arrow_keys_pan_without_changing_file_until_fitted(self):
        h=Gtk.Adjustment(value=100,lower=0,upper=1000,page_size=200,step_increment=40)
        y=Gtk.Adjustment(value=50,lower=0,upper=600,page_size=300,step_increment=40)
        v=self.viewer(); v.scroll.get_hadjustment.return_value=h; v.scroll.get_vadjustment.return_value=y
        v.is_pannable=lambda:ViewerShortcuts.is_pannable(v)
        ViewerShortcuts.browse_or_scroll(v,'right'); self.assertEqual(h.get_value(),140)
        ViewerShortcuts.browse_or_scroll(v,'bottom'); self.assertEqual(y.get_value(),300)
        ViewerShortcuts.browse_or_scroll(v,'home'); self.assertEqual(h.get_value(),0)
        v.navigate.assert_not_called()
        h.set_upper(200); y.set_upper(300)
        ViewerShortcuts.browse_or_scroll(v,'right'); v.navigate.assert_called_once_with(1)
        ViewerShortcuts.browse_or_scroll(v,'end'); v.folder_edge.assert_called_once_with(True)

    def test_all_fullscreen_scale_modes_preserve_or_stretch_as_specified(self):
        self.assertEqual(display_scales((100,50),(408,308),'small'),(1,1))
        self.assertEqual(display_scales((100,50),(408,308),'all'),(4,4))
        self.assertEqual(display_scales((100,50),(408,308),'stretch'),(4,6))
        self.assertEqual(display_scales((100,50),(408,308),'width'),(4,4))
        self.assertEqual(display_scales((100,50),(408,308),'height'),(6,6))
        self.assertEqual(display_scales((100,50),(408,308),'window',False),(1,1))
        self.assertEqual(display_scales((100,50),(408,308),'window',True),(4,4))

    def test_marks_are_persisted_and_removable_without_touching_image(self):
        with tempfile.TemporaryDirectory() as d:
            v=self.viewer(); v.tags=set(); v.tags_path=Path(d)/'tags.json'; v.model.source_path=Path(d)/'image.png'
            before=v.model.image.tobytes()
            ViewerShortcuts.tag_image(v,True); self.assertEqual(json.loads(v.tags_path.read_text()),[str(v.model.source_path)])
            ViewerShortcuts.tag_image(v,False); self.assertEqual(json.loads(v.tags_path.read_text()),[])
            self.assertEqual(v.model.image.tobytes(),before); self.assertFalse(v.model.dirty)

    def test_zoom_lock_and_select_all_toggle(self):
        v=self.viewer(); v.zoom_locked=False; v.scale=.5; v.fit=True
        ViewerShortcuts.toggle_zoom_lock(v); self.assertTrue(v.zoom_locked); self.assertFalse(v.fit); self.assertEqual(v.scale_y,.5)
        ViewerShortcuts.toggle_zoom_lock(v); self.assertFalse(v.zoom_locked)
        v.selection=(0,0,100,50); ViewerShortcuts.toggle_select_all(v); self.assertIsNone(v.selection)
        ViewerShortcuts.toggle_select_all(v); v.select_all.assert_called_once_with()

    def test_direct_print_uses_saved_values_without_opening_dialog(self):
        v=self.viewer(); v.has_preview.return_value=False; v.last_print_values={'mode':'fit'}
        ViewerShortcuts.direct_print(v); v.run_print.assert_called_once_with({'mode':'fit'},direct=True)
        v.print_image.assert_not_called()

    def test_new_window_owns_independent_pixels_and_history(self):
        v=self.viewer(); target=Mock(); v.new_window.return_value=target
        ViewerShortcuts.duplicate_window(v)
        model=target.adopt_model.call_args.args[0]
        self.assertEqual(model.image.tobytes(),v.model.image.tobytes())
        model.image.putpixel((0,0),(255,0,0,255))
        self.assertNotEqual(model.image.getpixel((0,0)),v.model.image.getpixel((0,0)))
        self.assertEqual(model.history,[]); self.assertTrue(model.dirty)
