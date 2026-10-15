"""Integration checks against native Linux codecs; no external samples needed."""
import gzip
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image
from native_codecs import decode, extra_extensions


class NativeCodecTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_capabilities_are_bounded(self):
        self.assertNotIn('.exe', extra_extensions())
        self.assertNotIn('.mvg', extra_extensions())
        self.assertNotIn('.msl', extra_extensions())

    def test_unsupported_format(self):
        path = self.root / 'file.exe'
        path.write_bytes(b'not an image')
        with self.assertRaises(ValueError):
            decode(path)

    @unittest.skipUnless('.pdf' in extra_extensions(), 'Poppler tools unavailable')
    def test_pdf_pages_and_nonascii_filename(self):
        path = self.root / 'Zwei Seiten [0] ä.pdf'
        Image.new('RGB', (20, 10), 'red').save(path, save_all=True,
              append_images=[Image.new('RGB', (10, 20), 'blue')])
        first, count, meta = decode(path)
        second, second_count, _ = decode(path, 1)
        self.assertEqual((count, second_count), (2, 2))
        self.assertGreater(first.width, first.height)
        self.assertLess(second.width, second.height)
        self.assertGreater(first.getpixel((2, 2))[0], 200)
        self.assertGreater(second.getpixel((2, 2))[2], 200)
        self.assertEqual(meta['decoder'], 'Poppler')
        with self.assertRaises(ValueError):
            decode(path, 2)

    @unittest.skipUnless('.svg' in extra_extensions(), 'SVG decoder unavailable')
    def test_svg_rasterization(self):
        path = self.root / 'drawing.svg'
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="12" height="7"><rect width="12" height="7" fill="red"/></svg>')
        image, count, meta = decode(path)
        self.assertEqual(image.size, (12, 7))
        self.assertEqual(image.getpixel((2, 2)), (255, 0, 0, 255))
        self.assertEqual(count, 1)
        self.assertTrue(meta['rasterized'])

    @unittest.skipUnless(shutil.which('magick'), 'ImageMagick unavailable')
    def test_native_raster_formats(self):
        png = self.root / 'source.png'
        Image.new('RGB', (9, 5), (200, 20, 40)).save(png)
        for extension in ('.jxl', '.exr', '.dpx', '.cin', '.mng'):
            if extension not in extra_extensions():
                continue
            with self.subTest(extension=extension):
                path = self.root / ('native' + extension)
                subprocess.run(['magick', str(png), str(path)], check=True,
                               capture_output=True, timeout=20)
                image, count, _ = decode(path)
                self.assertEqual(image.size, (9, 5))
                self.assertEqual(count, 1)
                self.assertGreater(image.getpixel((2, 2))[0], 150)

    @unittest.skipUnless('.mng' in extra_extensions(), 'MNG decoder unavailable')
    def test_mng_multiple_frames(self):
        red, blue, path = [self.root / name for name in ('red.png', 'blue.png', 'both.mng')]
        Image.new('RGB', (8, 4), 'red').save(red)
        Image.new('RGB', (8, 4), 'blue').save(blue)
        subprocess.run(['magick', str(red), str(blue), str(path)], check=True,
                       capture_output=True, timeout=20)
        image, count, _ = decode(path, 1)
        self.assertEqual(count, 2)
        self.assertEqual(image.getpixel((2, 2)), (0, 0, 255, 255))

    @unittest.skipUnless('.svgz' in extra_extensions(), 'SVG decoder unavailable')
    def test_compressed_svg(self):
        path = self.root / 'drawing.svgz'
        path.write_bytes(gzip.compress(b'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="7"/>'))
        image, count, _ = decode(path)
        self.assertEqual(image.size, (12, 7))
        self.assertEqual(count, 1)

    @unittest.skipUnless('.avif' in extra_extensions(), 'FFmpeg AVIF unavailable')
    def test_genuine_avif_still_and_animation(self):
        encoders = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, timeout=20).stdout
        if b'libaom-av1' not in encoders:
            self.skipTest('AVIF fixture encoder unavailable')
        for index, color in enumerate(('red', 'blue')):
            Image.new('RGB', (16, 12), color).save(self.root / f'frame{index}.png')
        for frames in (1, 2):
            with self.subTest(frames=frames):
                path = self.root / f'actual-{frames}.avif'
                subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '1',
                     '-filter_threads', '1', '-framerate', '2', '-i', str(self.root / 'frame%d.png'),
                     '-frames:v', str(frames), '-c:v', 'libaom-av1', '-threads', '1',
                     '-cpu-used', '8', '-pix_fmt', 'yuv444p', str(path)],
                     check=True, capture_output=True, timeout=30)
                data = path.read_bytes()
                self.assertEqual(data[4:8], b'ftyp')
                self.assertEqual(data[8:12], b'avif' if frames == 1 else b'avis')
                image, count, metadata = decode(path, frames-1)
                self.assertEqual(count, frames)
                self.assertEqual(image.size, (16, 12))
                self.assertEqual(metadata['decoder'], 'FFmpeg/AV1')
                pixel = image.getpixel((5, 5))
                self.assertGreater(pixel[0 if frames == 1 else 2], 220)
                self.assertLess(pixel[2 if frames == 1 else 0], 30)
                with self.assertRaises(ValueError):
                    decode(path, frames)

    @unittest.skipUnless('.avif' in extra_extensions(), 'FFmpeg AVIF unavailable')
    def test_fake_avif_rejected(self):
        path = self.root / 'renamed.avif'
        Image.new('RGB', (8, 8), 'red').save(path, 'PNG')
        with self.assertRaisesRegex(ValueError, 'AVIF-Dateikopf'):
            decode(path)

    @unittest.skipUnless('.svg' in extra_extensions(), 'SVG decoder unavailable')
    def test_oversized_image_rejected(self):
        path = self.root / 'huge.svg'
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100000" height="100000"/>')
        with self.assertRaises(ValueError):
            decode(path)

    def test_negative_frame_rejected(self):
        with self.assertRaises(ValueError):
            decode('/nonexistent', -1)


if __name__ == '__main__':
    unittest.main()
