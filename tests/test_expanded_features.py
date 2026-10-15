from pathlib import Path
import tempfile
import threading
import unittest
from PIL import Image
from image_model import ImageModel, image_files
from batch import plan_batch, run_batch


class ExpandedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root/'output'
        self.target.mkdir()
        self.source = self.root/'Bild 2.png'
        image = Image.new('RGBA',(12,8),(100,120,140,90))
        image.save(self.source)
        self.model = ImageModel()
        self.model.load(self.source)

    def test_undo_redo_save_revision_and_new_branch(self):
        self.model.rotate()
        self.model.save(self.target/'saved.png')
        self.model.undo()
        self.assertTrue(self.model.dirty)
        self.model.redo()
        self.assertFalse(self.model.dirty)
        self.model.undo()
        self.model.effect('mirror')
        self.assertTrue(self.model.dirty)
        self.assertFalse(self.model.future)

    def test_resize_and_effects_preserve_alpha(self):
        self.model.resize(6,4)
        self.assertEqual(self.model.image.size,(6,4))
        self.model.effect('invert')
        self.assertEqual(self.model.image.getpixel((1,1))[3],90)
        self.model.effect('grayscale')
        r,g,b,a = self.model.image.getpixel((1,1))
        self.assertEqual((r,a),(g,90))
        self.assertEqual(g,b)
        self.model.effect('contrast',1.4)
        self.assertEqual(self.model.image.getpixel((1,1))[3],90)
        with self.assertRaises(ValueError):
            self.model.resize(0,20)

    def test_text_watermark_and_undo(self):
        self.model.resize(100,100)
        before = self.model.image.tobytes()
        self.model.add_text('A',2,2,20,'#ffffff')
        self.assertNotEqual(self.model.image.tobytes(),before)
        self.model.undo()
        self.assertEqual(self.model.image.tobytes(),before)
        self.model.watermark(self.source)
        self.assertNotEqual(self.model.image.tobytes(),before)

    def test_pages_are_selected_and_exported_with_current_edit(self):
        source = self.root/'pages.tiff'
        Image.new('RGB',(12,8),'red').save(source,save_all=True,append_images=[Image.new('RGB',(12,8),'blue')])
        self.model.load(source,frame=1)
        self.assertEqual(self.model.frame_count,2)
        self.assertEqual(self.model.image.getpixel((0,0)),(0,0,255,255))
        self.model.effect('invert')
        target = self.target/'all.tiff'
        self.model.export_document(target)
        with Image.open(target) as result:
            self.assertEqual(result.n_frames,2)
            self.assertEqual(result.convert('RGB').getpixel((0,0)),(255,0,0))
            result.seek(1)
            self.assertEqual(result.convert('RGB').getpixel((0,0)),(255,255,0))
        self.assertTrue(self.model.dirty)
        with self.assertRaises(ValueError):
            self.model.export_document(source,overwrite=True)

    def test_gif_frames_and_duration(self):
        source = self.root/'animated.gif'
        Image.new('RGB',(12,8),'red').save(source,save_all=True,
            append_images=[Image.new('RGB',(12,8),'blue')],duration=[80,150],loop=0)
        self.model.load(source,frame=1)
        self.assertEqual(self.model.duration,150)
        self.assertEqual(self.model.frame_count,2)
        self.assertEqual(self.model.image.getpixel((0,0)),(0,0,255,255))

    def test_exif_preserved_or_stripped_without_orientation(self):
        source = self.root/'metadata.jpg'
        exif = Image.Exif()
        exif[315] = 'Test Artist'
        exif[274] = 6
        Image.new('RGB',(12,8),'red').save(source,exif=exif)
        self.model.load(source)
        self.model.rotate()
        target = self.target/'metadata.jpg'
        self.model.save(target)
        with Image.open(target) as result:
            self.assertEqual(result.getexif()[315],'Test Artist')
            self.assertNotIn(274,result.getexif())
        clean = self.target/'clean.jpg'
        self.model.save(clean,metadata=False)
        with Image.open(clean) as result:
            self.assertFalse(result.getexif())

    def test_navigation_natural_order_and_extension_filter(self):
        Image.new('RGB',(2,2)).save(self.root/'Bild 10.jpg')
        Image.new('RGB',(2,2)).save(self.root/'Bild 1.png')
        (self.root/'notes.txt').write_text('not a picture')
        self.assertEqual([p.name for p in image_files(self.root)],['Bild 1.png','Bild 2.png','Bild 10.jpg'])

    def test_batch_resize_rotate_and_original_unchanged(self):
        original = self.source.read_bytes()
        plan = plan_batch([self.source],self.target,'.jpg','Reise-{index:04d}-{stem}')
        results = run_batch(plan,max_width=4,max_height=4,clockwise=True)
        self.assertTrue(results[0]['ok'],results)
        with Image.open(plan[0].destination) as result:
            self.assertEqual(result.size,(3,4))
        self.assertEqual(self.source.read_bytes(),original)
        self.assertEqual(plan[0].destination.name,'Reise-0001-Bild 2.jpg')

    def test_batch_preview_rejects_collisions_paths_and_unknown_fields(self):
        for pattern in ('../bad','{unknown}','{stem.__class__}','{index:999999999d}'):
            with self.subTest(pattern=pattern),self.assertRaises(ValueError):
                plan_batch([self.source],self.target,'.png',pattern)
        with self.assertRaises(ValueError):
            plan_batch([self.source,self.source],self.target)
        (self.target/self.source.name).write_text('existing')
        with self.assertRaises(ValueError):
            plan_batch([self.source],self.target)

    def test_batch_racing_destination_is_never_overwritten(self):
        plan = plan_batch([self.source],self.target)
        plan[0].destination.write_bytes(b'created after preview')
        results = run_batch(plan)
        self.assertFalse(results[0]['ok'])
        self.assertEqual(plan[0].destination.read_bytes(),b'created after preview')

    def test_batch_copy_rename_is_bit_exact(self):
        plan = plan_batch([self.source],self.target,'copy','Photo-{index:03d}')
        results = run_batch(plan,copy_only=True)
        self.assertTrue(results[0]['ok'])
        self.assertEqual(plan[0].destination.read_bytes(),self.source.read_bytes())

    def test_batch_cancel_and_multiframe_rejection(self):
        plan = plan_batch([self.source],self.target)
        cancel = threading.Event()
        cancel.set()
        self.assertEqual(run_batch(plan,cancel=cancel),[])
        self.assertFalse(plan[0].destination.exists())
        source = self.root/'pages.tiff'
        Image.new('RGB',(2,2),'red').save(source,save_all=True,append_images=[Image.new('RGB',(2,2),'blue')])
        results = run_batch(plan_batch([source],self.target))
        self.assertFalse(results[0]['ok'])
        self.assertIn('Mehrseitige',results[0]['error'])

    def test_pdf_adapter_connected_to_model(self):
        source = self.root/'two.pdf'
        Image.new('RGB',(10,10),'red').save(source,save_all=True,append_images=[Image.new('RGB',(10,10),'blue')])
        self.model.load(source,frame=1)
        self.assertEqual(self.model.frame_count,2)
        self.assertGreater(self.model.image.getpixel((2,2))[2],200)


if __name__=='__main__':
    unittest.main()
