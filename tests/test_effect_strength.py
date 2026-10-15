import unittest
from PIL import Image
from image_tools import EFFECTS, EFFECT_PARAMETERS, effect, mixed_effect


class EffectStrengthTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGBA', (18, 16))
        self.image.putdata([(i % 256, i*7 % 256, i*13 % 256, i*19 % 256) for i in range(288)])

    def test_endpoints_for_every_effect(self):
        before = self.image.tobytes()
        for name in EFFECTS:
            with self.subTest(name=name):
                self.assertEqual(mixed_effect(self.image, name, strength=0).tobytes(), before)
                self.assertEqual(mixed_effect(self.image, name).tobytes(), effect(self.image, name).tobytes())
        self.assertEqual(self.image.tobytes(), before)

    def test_half_strength_blends_colors_and_preserves_alpha(self):
        for name in EFFECTS:
            with self.subTest(name=name):
                result = mixed_effect(self.image, name, strength=50)
                expected = Image.blend(self.image, effect(self.image, name), .5)
                self.assertEqual(result.tobytes(), expected.tobytes())
                self.assertEqual(result.getchannel('A').tobytes(), self.image.getchannel('A').tobytes())
                self.assertEqual(result.size, self.image.size)

    def test_invalid_strength_and_effect_are_rejected(self):
        for strength in (-1, 101, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                mixed_effect(self.image, 'sepia', strength=strength)
        with self.assertRaises(ValueError):
            mixed_effect(self.image, 'unknown', strength=0)

    def test_exposed_parameter_bounds_are_supported(self):
        for name, (_label, lower, upper, _unit) in EFFECT_PARAMETERS.items():
            for amount in (lower, upper):
                with self.subTest(name=name, amount=amount):
                    self.assertEqual(mixed_effect(self.image, name, amount).size, self.image.size)
