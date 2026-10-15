"""Real menu actions, shared by the menu bar, toolbar and accelerators."""
from gi.repository import Gio, GLib

RESIZE_ACCELERATOR = '<Primary>r'


def build_menus(window):
    menu = Gio.Menu()
    actions = []
    groups = [
        ('Datei', [
            ('open','Öffnen …',window.open_dialog,False),
            ('open-folder','Ordner öffnen …',window.open_folder,False),
            ('save-as','Speichern unter …',window.save_dialog,True),
            ('export-pages','Alle Seiten exportieren …',window.export_pages,True),
            ('export-options','Exportoptionen …',window.export_options,False),
            ('print','Drucken …',window.print_image,True),
            ('close','Schließen',window.close,False)]),
        ('Bearbeiten', [
            ('undo','Rückgängig',window.undo,True),
            ('redo','Wiederholen',window.redo,True),
            ('select','Ausschnitt auswählen',lambda:window.crop_toggle.set_active(True),True),
            ('crop','Zuschneiden',window.apply_crop,True)]),
        ('Bild', [
            ('resize','Größe ändern …',window.resize_dialog,True),
            ('rotate-left','90° nach links drehen',lambda:window.rotate(False),True),
            ('rotate-right','90° nach rechts drehen',lambda:window.rotate(True),True),
            ('mirror','Horizontal spiegeln',lambda:window.edit(lambda m:m.effect('mirror')),True),
            ('flip','Vertikal spiegeln',lambda:window.edit(lambda m:m.effect('flip')),True),
            ('grayscale','Graustufen',lambda:window.edit(lambda m:m.effect('grayscale')),True),
            ('invert','Negativ',lambda:window.edit(lambda m:m.effect('invert')),True),
            ('autocontrast','Automatischer Kontrast',lambda:window.edit(lambda m:m.effect('autocontrast')),True),
            ('adjust','Bildanpassungen …',window.adjust_dialog,True),
            ('adjust-values','Helligkeit / Kontrast / Farbe als Werte …',window.adjust_values_dialog,True),
            ('filter','Schärfen / Weichzeichnen …',window.filter_dialog,True),
            ('text','Text einfügen …',window.text_dialog,True),
            ('watermark','Wasserzeichen …',window.watermark_dialog,True),
            ('info','Bildinformationen',window.show_info,True)]),
        ('Ansicht', [
            ('zoom-in','Vergrößern',lambda:window.zoom(1.25),True),
            ('zoom-out','Verkleinern',lambda:window.zoom(.8),True),
            ('fit','Einpassen',window.fit_image,True),
            ('actual-size','100 % anzeigen',window.actual_size,True),
            ('fullscreen','Vollbild (F11)',window.toggle_fullscreen,False),
            ('thumbnails','Vorschaubilder …',window.toggle_sidebar,False),
            ('slideshow','Diashow starten / stoppen (F5)',window.toggle_slideshow,True),
            ('slideshow-options','Diashow-Intervall …',window.slideshow_settings,False),
            ('animation','Animation starten / stoppen',lambda:window.toggle_slideshow(True),True)]),
        ('Extras', [('batch','Stapelverarbeitung …',window.batch_dialog,False)]),
    ]
    for title, entries in groups:
        submenu = Gio.Menu()
        for name,label,callback,requires_image in entries:
            action = Gio.SimpleAction.new(name,None)
            action.connect('activate',lambda _a,_p,cb=callback:cb())
            window.add_action(action)
            actions.append((action,requires_image))
            item = Gio.MenuItem.new(label,'win.'+name)
            if name == 'resize':
                item.set_attribute_value('accel',GLib.Variant('s',RESIZE_ACCELERATOR))
            elif name == 'save-as':
                item.set_attribute_value('accel',GLib.Variant('s','<Primary><Shift>s'))
            submenu.append_item(item)
        menu.append_submenu(title,submenu)
    return menu, actions
