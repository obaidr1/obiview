"""Pending navigation must never run after cancellation, failure or partial export."""
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from unittest.mock import Mock
import tempfile
import unittest
from PIL import Image
from bildblick import Window
from image_model import ImageModel
from save_options import SaveSettings


class SaveContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'saved.png'
        model=ImageModel(); model.image=Image.new('RGBA',(8,6),'red')
        self.c=SimpleNamespace(busy=False,model=model,save_settings=SaveSettings(),status=Mock(),message=Mock(),edit=Mock())
        self.after=Mock()

    def complete(self):
        operation=self.c.edit.call_args.args[0]
        operation(self.c.model)
        self.c.edit.call_args.kwargs['after']()

    def test_continues_only_after_successful_write(self):
        Window.request_save(self.c,self.path,after=self.after)
        self.after.assert_not_called(); self.assertFalse(self.path.exists())
        self.complete()
        self.assertTrue(self.path.is_file()); self.after.assert_called_once_with()

    def test_write_failure_does_not_continue(self):
        Window.request_save(self.c,self.path/'missing'/'image.png',after=self.after)
        with self.assertRaises(OSError): self.complete()
        self.after.assert_not_called()

    def test_rejecting_overwrite_does_not_continue_or_write(self):
        self.path.write_bytes(b'untouched')
        Window.request_save(self.c,self.path,after=self.after)
        self.c.edit.assert_not_called(); self.after.assert_not_called()
        self.assertEqual(self.path.read_bytes(),b'untouched')

    def test_confirmed_overwrite_continues_after_write(self):
        self.path.write_bytes(b'old')
        Window.request_save(self.c,self.path,after=self.after)
        self.c.message.call_args.args[2]()
        self.after.assert_not_called(); self.complete(); self.after.assert_called_once_with()

    def test_resized_copy_does_not_discard_working_image(self):
        settings=replace(self.c.save_settings,output_width=4,output_height=3)
        Window.request_save(self.c,self.path,settings=settings,after=self.after)
        self.complete(); self.after.assert_not_called()
        self.assertEqual(self.c.model.image.size,(8,6))
        self.c.message.assert_called_once()
