import unittest
from unittest.mock import Mock
from PIL import Image
from gi.repository import Gio
from bildblick import Window, Gdk
from advanced_ui import AdvancedFeatures
from menus import build_menus, RESIZE_ACCELERATOR
from resize_settings import ResizeSettings
from image_model import ImageModel


class MenuWindow:
    def __init__(self):
        self.group = Gio.SimpleActionGroup()
        self.handlers = {}
        self.crop_toggle = Mock()
        self.model = ImageModel(); self.model.image = Image.new('RGBA',(8,6))

    def add_action(self,action):
        self.group.add_action(action)

    def __getattr__(self,name):
        if not hasattr(Window,name):
            raise AttributeError(name)
        return self.handlers.setdefault(name,Mock())


class ResizeMenuTests(unittest.TestCase):
    def test_visible_menu_and_resize_action(self):
        window = MenuWindow()
        menu,actions = build_menus(window)
        names = [menu.get_item_attribute_value(i,'label',None).unpack() for i in range(menu.get_n_items())]
        self.assertEqual(names,['Datei','Bearbeiten','Bild','Ansicht','Extras','Hilfe'])
        image_menu = menu.get_item_link(2,'submenu')
        self.assertEqual(image_menu.get_item_attribute_value(0,'action',None).unpack(),'win.resize')
        self.assertEqual(image_menu.get_item_attribute_value(0,'accel',None).unpack(),RESIZE_ACCELERATOR)
        window.group.activate_action('resize',None)
        window.resize_dialog.assert_called_once_with()
        for action in ('adjust','filter','batch','text','watermark'):
            self.assertTrue(window.group.has_action(action))

    def test_ctrl_r_and_ctrl_shift_r_open_resize(self):
        window = MenuWindow()
        for key in (Gdk.KEY_r,Gdk.KEY_R):
            self.assertTrue(AdvancedFeatures.extra_key(window,key,Gdk.ModifierType.CONTROL_MASK))
        self.assertEqual(window.resize_dialog.call_count,2)
        window.rotate.assert_not_called()

    def test_locked_width_and_height_both_control_size(self):
        state = ResizeSettings(1200,800)
        state.set_dimension('width',600)
        self.assertEqual(state.dimensions(),(600,400))
        state.set_dimension('height',200)
        self.assertEqual(state.dimensions(),(300,200))

    def test_percent_and_pixel_units_do_not_compound_resize(self):
        state = ResizeSettings(1200,800)
        state.set_dimension('height',50,percent=True)
        self.assertEqual(state.dimensions(),(600,400))
        self.assertEqual(state.values(True),(50,50))
        state.set_dimension('width',25,percent=True)
        self.assertEqual(state.dimensions(),(300,200))

    def test_unlock_and_relock_uses_last_changed_axis(self):
        state = ResizeSettings(1200,800)
        state.set_locked(False)
        state.set_dimension('height',100)
        self.assertEqual(state.dimensions(),(1200,100))
        state.set_locked(True)
        self.assertEqual(state.dimensions(),(150,100))

    def test_presets_and_size_limit(self):
        state = ResizeSettings(1200,800)
        state.preset(200)
        self.assertEqual(state.dimensions(),(2400,1600))
        state.set_dimension('width',90000)
        with self.assertRaises(ValueError):
            state.dimensions()
        for value in (0,-5,float('inf'),float('nan')):
            with self.assertRaises(ValueError):
                state.set_dimension('width',value)

    def test_resize_actual_pixels_and_undo(self):
        model = ImageModel()
        model.image = Image.new('RGBA',(2,1))
        model.image.putdata([(255,0,0,255),(0,0,255,255)])
        model.resize(4,2,'nearest')
        self.assertEqual(model.image.size,(4,2))
        self.assertEqual([model.image.getpixel((x,0)) for x in range(4)],[(255,0,0,255)]*2+[(0,0,255,255)]*2)
        model.undo()
        self.assertEqual(model.image.size,(2,1))
        self.assertFalse(model.dirty)
        with self.assertRaises(ValueError):
            model.resize(4,2,'unknown')


if __name__=='__main__':
    unittest.main()
