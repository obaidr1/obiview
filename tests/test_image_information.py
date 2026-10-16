import tempfile
import threading
import unittest
from pathlib import Path
from PIL import Image
from image_model import ImageModel
from image_info import info_values, count_rgb_colors, color_description
from paint_dialog import paint_strokes
from window_geometry import growth_target
from image_tools import print_layout


class InformationTests(unittest.TestCase):
    def test_source_facts_survive_edit_and_dpi_axes_export(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'photo.jpg'
            exif=Image.Exif(); exif[315]='Test Author'
            Image.new('RGB',(72,144),'red').save(source,dpi=(72,144),exif=exif,comment=b'Test comment')
            model=ImageModel(); model.load(source)
            self.assertEqual(model.source_info['size'],(72,144))
            self.assertEqual(model.source_info['bits'],24)
            self.assertEqual(model.source_info['exif']['Artist'],'Test Author')
            self.assertEqual(model.comment,b'Test comment')
            self.assertGreaterEqual(model.load_ms,0)
            self.assertEqual(model.dpi_pair,(72,144))
            self.assertIn('2.54 × 2.54 cm',info_values(model,[source])['print_size'])
            model.crop((0,0,36,72))
            values=info_values(model,[source])
            self.assertIn('72 × 144',values['original_size'])
            self.assertIn('36 × 72',values['current_size'])
            self.assertEqual(values['index'],'1 / 1')
            self.assertIn(str(36*72*4),values['memory'].replace(' ',''))
            pixels=model.image.tobytes(); model.set_dpi(300,600)
            self.assertEqual(model.image.tobytes(),pixels)
            self.assertEqual(model.dpi_pair,(300,600))
            layout=print_layout((300,600),(500,500),mode='scale',dpi=model.dpi_pair)
            self.assertEqual(layout[2:],(72,72))
            for ext in ('jpg','png','tif','bmp'):
                target=Path(folder)/('out.'+ext); model.save(target)
                with Image.open(target) as result:
                    self.assertAlmostEqual(result.info['dpi'][0],300,delta=.1)
                    self.assertAlmostEqual(result.info['dpi'][1],600,delta=.1)
            model.undo(); self.assertEqual(model.dpi_pair,(72,144))

    def test_real_iptc_resource_is_read(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'iptc.jpg'; Image.new('RGB',(2,2)).save(path)
            text=b'Test title'; data=b'\x1c\x02\x05'+len(text).to_bytes(2,'big')+text
            resource=b'8BIM\x04\x04\0\0'+len(data).to_bytes(4,'big')+data
            if len(data)%2: resource+=b'\0'
            payload=b'Photoshop 3.0\0'+resource
            raw=path.read_bytes(); path.write_bytes(raw[:2]+b'\xff\xed'+(len(payload)+2).to_bytes(2,'big')+payload+raw[2:])
            model=ImageModel(); model.load(path)
            self.assertEqual(model.source_info['iptc'][(2,5)],text)

    def test_rgb_count_alpha_and_cancellation(self):
        image=Image.new('RGBA',(4,1))
        image.putdata([(255,0,0,255),(255,0,0,0),(0,0,0,255),(0,255,0,64)])
        self.assertEqual(count_rgb_colors(image),3)
        wide=Image.new('RGB',(20000,1),'red'); wide.putpixel((19999,0),(0,0,255))
        self.assertEqual(count_rgb_colors(wide),2)
        event=threading.Event(); event.set()
        self.assertIsNone(count_rgb_colors(image,event))
        self.assertIn('16 777 216',color_description('RGBA',32))
        self.assertEqual(color_description(None,None),'Nicht verfügbar')

    def test_unsaved_document_has_no_fabricated_source(self):
        model=ImageModel(); model.image=Image.new('RGBA',(10,20))
        values=info_values(model)
        self.assertEqual(values['original_size'],'Keine Quelldatei')
        self.assertEqual(values['load_time'],'Nicht aus Datei geladen')
        self.assertEqual(values['disk'],'Noch nicht gespeichert')
        with self.assertRaises(ValueError): model.set_dpi(0,300)

    def test_growth_includes_controls_and_never_shrinks(self):
        self.assertEqual(growth_target((1000,600),1,(720,640),(700,520),(1920,1040)),(1028,728))
        self.assertIsNone(growth_target((100,100),1,(720,640),(700,520),(1920,1040)))
        self.assertEqual(growth_target((1000,600),2,(720,640),(700,520),(1920,1040)),'maximize')
        self.assertEqual(growth_target((300,1200),1,(720,640),(700,520),(1920,1040)),'maximize')
        self.assertEqual(growth_target((900,500),1,(720,640),(700,520),(960,540)),'maximize')

    def test_brush_soft_edges_differ_from_pen(self):
        source=Image.new('RGBA',(80,60),(0,0,0,0))
        stroke=([(20,30),(60,30)],(255,0,0,255),14)
        brush=paint_strokes(source,[('brush',*stroke)])
        pen=paint_strokes(source,[('pen',*stroke)])
        self.assertNotEqual(brush.tobytes(),pen.tobytes())
        self.assertTrue(any(0<a<255 for a in brush.getchannel('A').get_flattened_data()))
        self.assertEqual(brush.getpixel((0,0)),(0,0,0,0))
        self.assertEqual(source.getbbox(),None)
