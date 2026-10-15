import tempfile
import unittest
from pathlib import Path
from PIL import Image
from image_model import ImageModel
from image_tools import (to_pixels, fine_rotate, red_eye, frame, effect, EFFECTS,
                         text_image, selection_drag, print_layout, panorama, add_canvas)
from adjustments import adjusted
from save_options import SaveSettings
from image_export import write_image


class ImageToolsTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGBA',(80,60),(90,120,160,100))
        self.image.putpixel((40,30),(240,20,30,180))

    def test_physical_dimensions(self):
        self.assertEqual(to_pixels(2.54,'cm',300),300)
        self.assertEqual(to_pixels(2,'inch',600),1200)
        self.assertEqual(to_pixels(123,'px',300),123)
        for value in (float('nan'),float('inf')):
            with self.assertRaises(ValueError): to_pixels(value)
        with self.assertRaises(ValueError): to_pixels(10,'cm',0)

    def test_dpi_only_resize_is_undoable_and_does_not_change_pixels(self):
        model=ImageModel(); model.image=self.image
        original=self.image.tobytes()
        model.resize(80,60,dpi=300)
        self.assertEqual(model.dpi,300)
        self.assertEqual(model.image.tobytes(),original)
        model.undo(); self.assertEqual(model.dpi,96)
        model.redo(); self.assertEqual(model.dpi,300)
        model.rotate(); self.assertEqual(model.dpi,300)

    def test_dpi_export_and_reopen(self):
        model=ImageModel(); model.image=self.image
        model.resize(80,60,dpi=300)
        exif=Image.Exif(); exif[282]=72; exif[283]=72; exif[296]=2
        model.exif=exif.tobytes()
        with tempfile.TemporaryDirectory() as folder:
            for fmt in ('PNG','JPEG','TIFF','BMP'):
                path=Path(folder)/('image.'+fmt.lower())
                write_image(model,path,fmt,SaveSettings())
                with Image.open(path) as result:
                    self.assertAlmostEqual(result.info['dpi'][0],300,delta=.1)
                    if fmt in ('PNG','JPEG'): self.assertEqual(result.getexif()[282],300)
                loaded=ImageModel(); loaded.load(path)
                self.assertAlmostEqual(loaded.dpi,300,delta=.1)

    def test_fine_rotation_direction_size_and_fill(self):
        source=Image.new('RGBA',(2,1)); source.putdata([(255,0,0,255),(0,0,255,255)])
        result=fine_rotate(source,90)
        self.assertEqual(result.size,(1,2))
        self.assertEqual(result.getpixel((0,0)),(255,0,0,255))
        result=fine_rotate(self.image,15,'#abcdef')
        self.assertGreater(result.width,80)
        self.assertEqual(result.getpixel((0,0)),(171,205,239,255))
        self.assertEqual(fine_rotate(self.image,-15,expand=False).size,self.image.size)

    def test_red_eye_only_changes_red_pixels_inside_selection(self):
        self.image.putpixel((2,2),(250,10,20,170))
        result=red_eye(self.image,(35,25,45,35))
        self.assertEqual(result.getpixel((40,30)),(25,20,30,180))
        self.assertEqual(result.getpixel((2,2)),self.image.getpixel((2,2)))
        self.assertEqual(result.getpixel((41,30)),self.image.getpixel((41,30)))
        with self.assertRaises(ValueError): red_eye(self.image,None)

    def test_every_effect_is_real_deterministic_and_preserves_alpha(self):
        for name in EFFECTS:
            with self.subTest(name=name):
                result=effect(self.image,name,5)
                self.assertEqual(result.size,self.image.size)
                self.assertEqual(result.getchannel('A').tobytes(),self.image.getchannel('A').tobytes())
                self.assertNotEqual(result.tobytes(),self.image.tobytes())
                self.assertEqual(result.tobytes(),effect(self.image,name,5).tobytes())

    def test_frame_styles_and_asymmetric_canvas_preserve_original(self):
        for style,total in (('plain',4),('double',6),('bevel',4)):
            result=frame(self.image,4,'#ffffff',style,2,'#000000')
            self.assertEqual(result.size,(80+2*total,60+2*total))
            self.assertEqual(result.crop((total,total,total+80,total+60)).tobytes(),self.image.tobytes())
        result=add_canvas(self.image,1,2,3,4,'#abcdef')
        self.assertEqual(result.size,(84,66))
        self.assertEqual(result.crop((1,2,81,62)).tobytes(),self.image.tobytes())
        self.assertEqual(result.getpixel((0,0)),(171,205,239,255))
        self.assertEqual(add_canvas(self.image,left=-1).tobytes(),self.image.crop((1,0,80,60)).tobytes())
        with self.assertRaises(ValueError): add_canvas(self.image,left=-80)

    def test_selection_moving_and_resizing_clamp_to_image(self):
        box=(10,10,40,30)
        self.assertEqual(selection_drag(box,(10,10),(-100,90),(80,60),'move'),(0,40,30,60))
        self.assertEqual(selection_drag(box,(40,30),(90,80),(80,60),'es'),(10,10,80,60))
        self.assertEqual(selection_drag(box,(10,10),(20,15),(80,60),'wn'),(20,15,40,30))
        self.assertEqual(selection_drag(None,(70,50),(10,10),(80,60)),(10,10,70,50))

    def test_gamma_and_rgb_independent(self):
        original=Image.new('RGBA',(1,1),(64,64,64,50))
        gamma=adjusted(original,{'gamma':50})
        self.assertEqual(gamma.getpixel((0,0)),(128,128,128,50))
        red=adjusted(original,{'red':20})
        self.assertEqual(red.getpixel((0,0)),(115,64,64,50))

    def test_text_font_style_color_and_selection_clip(self):
        source=Image.new('RGBA',(180,120),(0,0,0,255))
        result=text_image(source,'Hello world\nSecond line',(20,20,160,100),'Sans',30,'#ff0000',True,True)
        self.assertNotEqual(result.tobytes(),source.tobytes())
        self.assertEqual(result.crop((0,0,180,20)).tobytes(),source.crop((0,0,180,20)).tobytes())
        self.assertEqual(result.crop((160,0,180,120)).tobytes(),source.crop((160,0,180,120)).tobytes())
        self.assertGreater(result.getchannel('R').getextrema()[1],0)
        self.assertEqual(result.getchannel('G').getextrema(),(0,0))

    def test_print_layout_fit_physical_scale_offsets(self):
        self.assertEqual(print_layout((200,100),(600,800)),(0,250,600,300))
        x,y,w,h=print_layout((300,150),(600,800),'custom',width_cm=2.54,centered=False,x_cm=2.54,y_cm=5.08)
        self.assertEqual((x,y,w,h),(72,144,72,36))
        x,y,w,h=print_layout((300,150),(600,800),'scale',dpi=300,scale_x=50,scale_y=200)
        self.assertEqual((w,h),(36,72))

    def test_panorama_order_gap_and_orientation(self):
        images=[Image.new('RGBA',(3,2),'red'),Image.new('RGBA',(2,3),'blue')]
        result=panorama(images,gap=1)
        self.assertEqual(result.size,(6,3))
        self.assertEqual(result.getpixel((3,1)),(255,255,255,255))
        self.assertEqual(result.getpixel((4,1)),(0,0,255,255))
        self.assertEqual(panorama(images,vertical=True,gap=2).size,(3,7))
        with self.assertRaises(ValueError): panorama(images[:1])

    def test_effect_model_single_undo_preserves_original(self):
        model=ImageModel(); model.image=self.image
        model.replace(effect(model.image,'sepia'))
        self.assertEqual(len(model.history),1)
        model.undo(); self.assertEqual(model.image.tobytes(),self.image.tobytes())
        self.assertFalse(model.dirty)

class MenuToolTests(unittest.TestCase):
    def test_cut_inside_and_outside(self):
        from image_tools import erase_selection
        image=Image.new('RGBA',(10,10),'red')
        result=erase_selection(image,(2,2,8,8))
        self.assertEqual(result.getpixel((3,3)),(255,255,255,255))
        self.assertEqual(result.getpixel((0,0)),(255,0,0,255))
        result=erase_selection(image,(2,2,8,8),True)
        self.assertEqual(result.getpixel((3,3)),(255,0,0,255))
        self.assertEqual(result.getpixel((0,0)),(255,255,255,255))

    def test_auto_crop_transparent_and_solid(self):
        from image_tools import auto_crop
        for background in ('white',(0,0,0,0)):
            image=Image.new('RGBA',(20,20),background)
            image.paste('red',(4,3,14,13))
            self.assertEqual(auto_crop(image).size,(10,10))
        with self.assertRaises(ValueError): auto_crop(Image.new('RGBA',(10,10),'white'))

    def test_palette_and_channel_swap(self):
        from image_tools import reduce_colors,swap_channels
        image=Image.new('RGBA',(16,16))
        image.putdata([(x*16,y*16,30,100) for y in range(16) for x in range(16)])
        result=reduce_colors(image,16,False)
        self.assertLessEqual(len(result.convert('RGB').getcolors(256)),16)
        self.assertEqual(result.getchannel('A').tobytes(),image.getchannel('A').tobytes())
        self.assertEqual(swap_channels(image,'BGR').getpixel((1,2)),(30,32,16,100))

    def test_paint_strokes_preserve_source_and_draw_shapes(self):
        from paint_dialog import paint_strokes
        image=Image.new('RGBA',(100,80),'white')
        for kind in ('pen','line','arrow','rectangle','ellipse'):
            result=paint_strokes(image,[(kind,[(10,10),(60,50)],'#ff0000',4)])
            self.assertNotEqual(result.tobytes(),image.tobytes())
            self.assertEqual(result.getpixel((0,0)),(255,255,255,255))
        self.assertEqual(image.getpixel((10,10)),(255,255,255,255))

    def test_shortcuts_crop_and_redo_are_distinct(self):
        from unittest.mock import Mock
        from advanced_ui import AdvancedFeatures
        from bildblick import Gdk
        window=Mock()
        AdvancedFeatures.extra_key(window,Gdk.KEY_y,Gdk.ModifierType.CONTROL_MASK)
        window.apply_crop.assert_called_once_with(); window.redo.assert_not_called()
        AdvancedFeatures.extra_key(window,Gdk.KEY_z,Gdk.ModifierType.CONTROL_MASK|Gdk.ModifierType.SHIFT_MASK)
        window.redo.assert_called_once_with()

    def test_reopened_new_document_keeps_save_state(self):
        model=ImageModel(); model.image=Image.new('RGBA',(8,6),'red')
        model.revision=1; model.next_revision=2
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'Bild mit Leerzeichen.png'
            model.save(path)
            self.assertFalse(model.dirty)
            self.assertIsNone(model.source_path)
            model.export_document(Path(directory)/'document.pdf')
            self.assertTrue((Path(directory)/'document.pdf').read_bytes().startswith(b'%PDF-'))

    def test_clipboard_provider_offers_native_texture(self):
        from tool_dialogs import image_clipboard_provider
        from gi.repository import Gdk
        provider=image_clipboard_provider(Image.new('RGBA',(4,3),'red'))
        self.assertTrue(provider.ref_formats().contain_gtype(Gdk.Texture))
