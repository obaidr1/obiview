import os
import unittest
from unittest.mock import patch

from i18n import language, tr
from menus import build_menus


class LocalizationTests(unittest.TestCase):
    def test_language_can_be_selected_and_german_remains_available(self):
        with patch.dict(os.environ, {'BILDBLICK_LANGUAGE': 'en'}, clear=False):
            self.assertEqual(language(), 'en')
            self.assertEqual(tr('Größe ändern'), 'Resize')
        with patch.dict(os.environ, {'BILDBLICK_LANGUAGE': 'de'}, clear=False):
            self.assertEqual(language(), 'de')
            self.assertEqual(tr('Größe ändern'), 'Größe ändern')
        with patch.dict(os.environ, {'BILDBLICK_LANGUAGE': 'fr'}, clear=False):
            self.assertEqual(language(), 'en')
            self.assertEqual(tr('Größe ändern'), 'Resize')

    def test_menu_titles_and_commands_are_english_in_english_mode(self):
        class Window:
            def add_action(self, _action):
                pass

            def __getattr__(self, _name):
                return lambda *_args: None

        with patch.dict(os.environ, {'BILDBLICK_LANGUAGE': 'en'}, clear=False):
            menu, _actions = build_menus(Window())
            titles = [menu.get_item_attribute_value(i, 'label', None).unpack()
                      for i in range(menu.get_n_items())]
            self.assertEqual(titles, ['File', 'Edit', 'Image', 'View', 'Tools', 'Help'])
            image_menu = menu.get_item_link(2, 'submenu')
            commands = []
            for section_index in range(image_menu.get_n_items()):
                section = image_menu.get_item_link(section_index, 'section')
                if section:
                    commands.extend(section.get_item_attribute_value(i, 'label', None).unpack()
                                    for i in range(section.get_n_items()))
            self.assertIn('Resize / Resample…', commands)
            self.assertIn('Image Information', commands)

    def test_user_text_is_not_rewritten(self):
        with patch.dict(os.environ, {'BILDBLICK_LANGUAGE': 'en'}, clear=False):
            self.assertEqual(tr('my vacation picture.png'), 'my vacation picture.png')
            self.assertEqual(tr('Bikubisch'), 'Bicubic')
            self.assertEqual(tr('3D-Schaltfläche'), '3D Button')


if __name__ == '__main__':
    unittest.main()
