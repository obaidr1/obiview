import tempfile
import unittest
from pathlib import Path
from PIL import Image
from adjustments import adjusted, CONTROLS
from image_model import ImageModel
from image_export import write_image
from save_options import SaveSettings


class AdjustmentTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGBA',(24,16),(80,120,160,96))

    def test_neutral_is_exact_and_does_not_mutate_source(self):
        original = self.image.tobytes()
        self.assertEqual(adjusted(self.image,{}).tobytes(),original)
        adjusted(self.image,{'brightness':50},'Warm')
        self.assertEqual(self.image.tobytes(),original)

    def test_every_control_and_look_changes_pixels_and_preserves_alpha(self):
        for name in CONTROLS:
            with self.subTest(control=name):
                image = self.image.copy()
                image.putpixel((12,8),(200,20,70,160))
                output = adjusted(image,{name:50})
                self.assertNotEqual(output.tobytes(),image.tobytes())
                self.assertEqual(output.getchannel('A').tobytes(),image.getchannel('A').tobytes())
        for look in ('Film','Fade','Warm'):
            self.assertNotEqual(adjusted(self.image,{},look).tobytes(),self.image.tobytes())

    def test_grain_is_deterministic(self):
        self.assertEqual(adjusted(self.image,{'grain':70}).tobytes(),adjusted(self.image,{'grain':70}).tobytes())

    def test_export_resolution_and_metadata_do_not_mutate_canvas(self):
        model = ImageModel()
        model.image = self.image
        model.comment = b'private comment'
        settings = SaveSettings(output_width=12,output_height=8,keep_exif=False,
                                keep_icc=False,keep_xmp=False,keep_comment=False)
        with tempfile.TemporaryDirectory() as folder:
            for fmt,ext in [('PNG','png'),('JPEG','jpg'),('WEBP','webp'),('GIF','gif')]:
                target = Path(folder)/('export.'+ext)
                write_image(model,target,fmt,settings)
                with Image.open(target) as result:
                    self.assertEqual(result.size,(12,8))
                    self.assertNotIn('comment',result.info)
                self.assertEqual(model.image.size,(24,16))
                self.assertFalse(model.dirty)

    def test_invalid_export_dimensions_rejected(self):
        for width,height in [(1,0),(0,1),(10000,10000),(-1,1),(True,1)]:
            with self.assertRaises(ValueError):
                SaveSettings(output_width=width,output_height=height)
