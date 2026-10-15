import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from image_model import ImageModel, crop_box


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.input = self.root / 'original.png'
        image = Image.new('RGBA', (4, 3))
        image.putdata([(x*50, y*70, 80, 255) for y in range(3) for x in range(4)])
        image.save(self.input)
        self.original = self.input.read_bytes()
        self.model = ImageModel()
        self.model.load(self.input)

    def tearDown(self):
        self.temp.cleanup()

    def test_rotation_and_undo_exact_pixels(self):
        before = self.model.image.copy()
        self.model.rotate()
        self.assertEqual(self.model.image.size, (3, 4))
        self.assertEqual(self.model.image.getpixel((2, 0)), before.getpixel((0, 0)))
        self.model.undo()
        self.assertEqual(self.model.image.tobytes(), before.tobytes())
        self.assertFalse(self.model.dirty)
        for _ in range(4):
            self.model.rotate(False)
        self.assertEqual(self.model.image.tobytes(), before.tobytes())

    def test_crop_reverse_drag_clamp_and_pixel_content(self):
        box = crop_box((3.8, 2.8), (1.1, 1.1), (4, 3))
        self.assertEqual(box, (1, 1, 4, 3))
        expected = self.model.image.getpixel((1, 1))
        self.model.crop(box)
        self.assertEqual(self.model.image.size, (3, 2))
        self.assertEqual(self.model.image.getpixel((0, 0)), expected)
        self.assertEqual(crop_box((-5, -8), (99, 99), (4, 3)), (0, 0, 4, 3))
        self.assertIsNone(crop_box((8, 8), (9, 9), (4, 3)))

    def test_invalid_crop_does_not_mutate(self):
        with self.assertRaises(ValueError):
            self.model.crop((-1, 0, 3, 3))
        self.assertEqual(self.model.image.size, (4, 3))

    def test_save_preserves_source_and_roundtrips_pixels(self):
        self.model.rotate()
        target = self.root / 'export.png'
        self.model.save(target)
        self.assertEqual(self.input.read_bytes(), self.original)
        with Image.open(target) as read:
            self.assertEqual(read.tobytes(), self.model.image.tobytes())
        self.assertFalse(self.model.dirty)
        self.model.undo()
        self.assertTrue(self.model.dirty)

    def test_existing_destination_not_overwritten_without_consent(self):
        self.model.rotate()
        with self.assertRaises(FileExistsError):
            self.model.save(self.input)
        self.assertEqual(self.input.read_bytes(), self.original)
        self.assertTrue(self.model.dirty)
        self.assertFalse(list(self.root.glob('.bildblick-*')))
        self.model.save(self.input, overwrite=True)
        with Image.open(self.input) as read:
            self.assertEqual(read.size, (3, 4))

    def test_encoder_failure_preserves_existing_destination(self):
        with patch.object(Image.Image, 'save', side_effect=OSError('simulated full disk')):
            with self.assertRaises(OSError):
                self.model.save(self.input, overwrite=True)
        self.assertEqual(self.input.read_bytes(), self.original)
        self.assertFalse(list(self.root.glob('.bildblick-*')))

    def test_transparency_and_jpeg_background(self):
        self.model.image = Image.new('RGBA', (16,16), (255,0,0,0))
        png, jpg = self.root/'alpha.png', self.root/'white.jpg'
        self.model.save(png)
        self.model.save(jpg)
        with Image.open(png) as read:
            self.assertEqual(read.getpixel((0,0))[3], 0)
        with Image.open(jpg) as read:
            self.assertEqual(read.getpixel((0,0)), (255,255,255))

    def test_exif_orientation(self):
        path = self.root/'oriented.jpg'
        image = Image.new('RGB', (5,3), 'red')
        exif = Image.Exif()
        exif[274] = 6
        image.save(path, exif=exif)
        self.model.load(path)
        self.assertEqual(self.model.image.size, (3,5))

    def test_failed_load_keeps_open_document(self):
        path = self.root/'broken.png'
        path.write_bytes(b'not an image')
        before = self.model.image
        with self.assertRaises(Exception):
            self.model.load(path)
        self.assertIs(self.model.image, before)
        self.assertEqual(self.model.path, self.input)

    def test_all_export_formats(self):
        for ext in ('png','jpg','webp','bmp','tiff'):
            target = self.root / ('export.'+ext)
            self.model.save(target)
            with Image.open(target) as image:
                image.load()
                self.assertEqual(image.size, (4,3))


if __name__ == '__main__':
    unittest.main()
