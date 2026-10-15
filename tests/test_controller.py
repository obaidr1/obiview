"""Regression checks for asynchronous directory races without a display server."""
from pathlib import Path
import tempfile
import unittest
import gi
gi.require_version('Gtk','4.0')
gi.require_version('GdkPixbuf','2.0')
from PIL import Image
from advanced_ui import AdvancedFeatures
from image_model import ImageModel


class Visible:
    def set_visible(self,value):
        self.visible = value


class Controller(AdvancedFeatures):
    def __init__(self):
        self.folder = None
        self.folder_generation = 0
        self.thumb_generation = 0
        self.folder_files = []
        self.model = ImageModel()
        self.sidebar = Visible()
        self.calls = []
        self.jobs = []
        self.guarded = False

    def submit(self,work,done,failure=None):
        self.jobs.append((work,done))

    def rebuild_thumbnails(self):
        self.thumb_generation += 1

    def update_advanced(self):
        pass

    def request_load(self,path,**kwargs):
        self.calls.append(path)

    def guard(self,action):
        self.guarded = True
        if not self.model.dirty:
            action()

    def message(self,*args):
        self.calls.append(args)

    def complete(self,index=0):
        work,done = self.jobs[index]
        done(work())


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder/'one.png'
        Image.new('RGB',(10,10),'red').save(self.source)
        self.controller = Controller()
        self.controller.model.load(self.source)

    def test_search_change_does_not_invalidate_pending_directory(self):
        c = self.controller
        c.set_folder(self.folder)
        c.rebuild_thumbnails()
        c.complete()
        self.assertEqual(c.folder_files,[self.source])

    def test_edits_during_directory_scan_are_guarded(self):
        c = self.controller
        c.set_folder(self.folder,open_first=True)
        c.model.rotate()
        c.complete()
        self.assertTrue(c.guarded)
        self.assertEqual(c.calls,[])
        self.assertTrue(c.model.dirty)

    def test_old_directory_response_cannot_replace_new_folder(self):
        c = self.controller
        other = self.folder/'other'
        other.mkdir()
        c.set_folder(self.folder)
        c.set_folder(other)
        c.complete(0)
        self.assertEqual(c.folder_files,[])
        self.assertEqual(c.folder,other)


if __name__=='__main__':
    unittest.main()
