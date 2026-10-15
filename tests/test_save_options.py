"""Verify exported bytes and profile persistence, not just UI flag values."""
from dataclasses import replace
from pathlib import Path
import random
import tempfile
import unittest
from PIL import Image, JpegImagePlugin
from image_model import ImageModel
from save_options import SaveSettings, SaveProfiles, filename_for_format


class SaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source.png'
        Image.new('RGBA', (64, 48), (210, 40, 70, 255)).save(self.source)
        self.model = ImageModel()
        self.model.load(self.source)

    def export(self, name, **kwargs):
        path = self.root/name
        self.model.save(path, settings=SaveSettings(**kwargs))
        return path

    def test_progressive_and_chroma_sampling_in_encoded_jpeg(self):
        for progressive, chroma in ((True, True), (False, False)):
            path = self.export(f'{progressive}.jpg', progressive=progressive, chroma444=chroma)
            with Image.open(path) as image:
                self.assertEqual(bool(image.info.get('progressive')), progressive)
                self.assertEqual(JpegImagePlugin.get_sampling(image), 0 if chroma else 2)

    def test_grayscale_does_not_change_canvas_and_drops_rgb_profile(self):
        self.model.icc = b'rgb-profile'
        original = self.model.image.tobytes()
        path = self.export('gray.jpg', grayscale=True)
        with Image.open(path) as image:
            self.assertEqual(image.mode, 'L')
            self.assertNotIn('icc_profile', image.info)
        self.assertEqual(self.model.image.mode, 'RGBA')
        self.assertEqual(self.model.image.tobytes(), original)

    def test_quality_changes_output_size(self):
        self.model.image = Image.frombytes('RGB', (256, 256), random.Random(7).randbytes(256*256*3)).convert('RGBA')
        low = self.export('low.jpg', quality=10)
        high = self.export('high.jpg', quality=95)
        self.assertLess(low.stat().st_size, high.stat().st_size)

    def test_target_size_is_respected_and_retains_dimensions(self):
        self.model.image = Image.frombytes('RGB', (256, 256), random.Random(3).randbytes(256*256*3)).convert('RGBA')
        path = self.export('limited.jpg', quality=95, target_kib=12, progressive=True)
        self.assertLessEqual(path.stat().st_size, 12*1024)
        with Image.open(path) as image:
            self.assertEqual(image.size, (256, 256))

    def test_unreachable_target_preserves_destination_and_dirty_state(self):
        self.model.comment = b'x'*3000
        self.model.rotate()
        path = self.root/'existing.jpg'
        path.write_bytes(b'existing file')
        with self.assertRaisesRegex(ValueError, 'nicht erreichbar'):
            self.model.save(path, overwrite=True, settings=SaveSettings(target_kib=1))
        self.assertEqual(path.read_bytes(), b'existing file')
        self.assertTrue(self.model.dirty)
        self.assertEqual(self.model.path, self.source)
        self.assertFalse(list(self.root.glob('.bildblick-*')))

    def test_metadata_readback_and_independent_switches(self):
        source = self.root/'metadata.jpg'
        exif = Image.Exif()
        exif[315] = 'Bildblick test'
        exif[274] = 6
        xmp = b'<x:xmpmeta xmlns:x="adobe:ns:meta/">test metadata</x:xmpmeta>'
        Image.new('RGB', (64, 48), 'red').save(source, exif=exif, comment=b'original comment',
                icc_profile=b'test rgb profile', xmp=xmp)
        self.model.load(source)
        expected = {'keep_exif': ('exif', None), 'keep_icc': ('icc_profile', b'test rgb profile'),
                    'keep_xmp': ('xmp', xmp), 'keep_comment': ('comment', b'original comment')}
        kept = self.export('kept.jpg')
        with Image.open(kept) as image:
            self.assertEqual(image.size, (48, 64))
            self.assertEqual(image.getexif()[315], 'Bildblick test')
            self.assertNotIn(274, image.getexif())
            for field, value in expected.values():
                if value:
                    self.assertEqual(image.info[field], value)
        for flag, (field, _) in expected.items():
            path = self.export(flag+'.jpg', **{flag: False})
            with Image.open(path) as image:
                self.assertNotIn(field, image.info)
                for other_field, _ in expected.values():
                    if other_field != field:
                        self.assertIn(other_field, image.info)

    def test_metadata_optout_prevents_inherited_info_leaking(self):
        exif = Image.Exif()
        exif[315] = 'private name'
        self.model.image.info.update(exif=exif.tobytes(), comment=b'private comment', xmp=b'private xmp')
        for ext in ('jpg', 'png', 'webp', 'gif'):
            target = self.root/('stripped.'+ext)
            self.model.save(target, metadata=False)
            with Image.open(target) as image:
                for field in ('exif', 'comment', 'xmp'):
                    self.assertNotIn(field, image.info)
        self.assertEqual(self.model.image.info['comment'], b'private comment')

    def test_gif_transparency_toggle_and_interlace(self):
        self.model.image = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
        self.model.image.putpixel((0, 0), (0, 255, 0, 0))
        self.model.image.putpixel((1, 0), (0, 255, 0, 127))
        self.model.image.putpixel((2, 0), (0, 255, 0, 128))
        for enabled in (True, False):
            path = self.export(f'alpha-{enabled}.gif', gif_transparency=enabled, gif_interlace=enabled)
            with Image.open(path) as image:
                # Decoder tile arguments describe the on-disk interlace flag.
                self.assertEqual(bool(image.tile[0].args[1]), enabled)
                result = image.convert('RGBA')
                self.assertEqual(result.getpixel((0, 0))[3], 0 if enabled else 255)
                self.assertEqual(result.getpixel((1, 0))[3], 0 if enabled else 255)
                self.assertEqual(result.getpixel((2, 0))[3], 255)
                self.assertEqual(result.getpixel((20, 20)), (255, 0, 0, 255))
                if not enabled:
                    self.assertEqual(result.getpixel((0, 0)), (255, 255, 255, 255))

    def test_png_compression_is_lossless_and_webp_lossless(self):
        for name, options in (('fast.png', {'png_compression': 0}), ('small.png', {'png_compression': 9}),
                              ('lossless.webp', {'webp_lossless': True})):
            path = self.export(name, **options)
            with Image.open(path) as image:
                self.assertEqual(image.convert('RGBA').tobytes(), self.model.image.tobytes())
        self.assertLess((self.root/'small.png').stat().st_size, (self.root/'fast.png').stat().st_size)

    def test_profile_roundtrip_delete_and_no_target_path_stored(self):
        path = self.root/'config'/'profiles.json'
        store = SaveProfiles(path)
        settings = SaveSettings(quality=78, progressive=True, keep_exif=False, target_kib=65)
        store.save('Web – klein', 'JPEG', settings)
        fresh = SaveProfiles(path)
        self.assertEqual(fresh.load('Web – klein'), ('JPEG', settings))
        fresh.save('Web – klein', 'PNG', replace(settings, png_compression=9))
        self.assertEqual(SaveProfiles(path).load('Web – klein')[0], 'PNG')
        fresh.delete('Web – klein')
        self.assertEqual(SaveProfiles(path).profiles, {})
        self.assertFalse(list(path.parent.glob('.save-profiles-*')))

    def test_corrupt_profile_is_reported_and_not_overwritten(self):
        path = self.root/'profiles.json'
        path.write_text('{broken')
        store = SaveProfiles(path)
        self.assertIsNotNone(store.error)
        with self.assertRaises(ValueError):
            store.save('Web', 'JPEG', SaveSettings())
        self.assertEqual(path.read_text(), '{broken')

    def test_format_matches_suffix_and_validates_filename(self):
        for name, fmt, expected in (('photo', 'JPEG', 'photo.jpg'), ('photo.PNG', 'JPEG', 'photo.jpg'),
                                    ('photo.JPEG', 'JPEG', 'photo.JPEG'), ('photo.v2.png', 'WEBP', 'photo.v2.webp')):
            self.assertEqual(filename_for_format(name, fmt), expected)
        for name in ('', ' ', '..', '../outside', '/tmp/image.png', 'bad\x00name'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                filename_for_format(name, 'PNG')

    def test_invalid_settings_rejected(self):
        for values in ({'quality': 101}, {'target_kib': -1}, {'png_compression': 10}, {'keep_exif': 'false'}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                SaveSettings(**values)


if __name__ == '__main__':
    unittest.main()
