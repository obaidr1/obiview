"""Real menu actions, shared by the menu bar, toolbar and accelerators."""
from gi.repository import Gio, GLib

RESIZE_ACCELERATOR = '<Primary>r'


def build_menus(window):
    menu = Gio.Menu()
    actions = []
    groups = [
        ('Datei', [
            ('new-window','Bild in neuem Fenster',window.duplicate_window,False),
            ('open','Öffnen …',window.open_dialog,False),
            ('reopen','Erneut öffnen',window.reopen,True),
            ('external','Öffnen mit …',window.external_editor,True),
            ('media','Audio / Video öffnen …',window.media_dialog,False),
            ('open-folder','Ordner öffnen …',window.open_folder,False),
            ('search-files','Dateien suchen …',window.search_files,False),
            ('recent-folders','Letzte Ordner …',window.recent_folders,False),
            ('rename-file','Umbenennen …',lambda:window.file_action('rename'),True),
            ('move-file','Datei verschieben …',lambda:window.file_action('move'),True),
            ('copy-file','Datei kopieren …',lambda:window.file_action('copy'),True),
            ('trash-file','In den Papierkorb …',lambda:window.file_action('trash'),True),
            ('save-current','Speichern',window.save_current,True),
            ('save-as','Speichern unter …',window.save_dialog,True),
            ('export-pages','Alle Seiten exportieren …',window.export_pages,True),
            ('export-options','Exportoptionen …',window.export_options,False),
            ('print','Drucken …',window.print_image,True),
            ('direct-print','Direkt drucken',window.direct_print,True),
            ('random','Zufälliges Bild',window.random_image,True),
            ('scan','Scannen …',window.scan_dialog,False),
            ('scan-print','Scannen und drucken …',lambda:window.scan_dialog(True),False),
            ('clear','Bild schließen (D)',window.clear_image,True),
            ('close','Schließen',window.close,False)]),
        ('Bearbeiten', [
            ('undo','Rückgängig',window.undo,True),
            ('redo','Wiederholen (Strg+Umschalt+Z)',window.redo,True),
            ('paint','Zeichnen …',window.paint_dialog,True),
            ('paste','Bild einfügen (Strg+V)',window.paste_image,False),
            ('copy','Auswahl / Bild kopieren (Strg+C)',window.copy_image,True),
            ('copy-name','Dateinamen kopieren',window.copy_filename,True),
            ('clear-clipboard','Zwischenablage leeren',lambda:window.get_clipboard().set_content(None),False),
            ('select-all','Alles auswählen',window.select_all,True),
            ('center-selection','Auswahl maximieren und zentrieren',window.center_selection,True),
            ('cut','Auswahl ausschneiden',window.cut_selection,True),
            ('cut-outside','Außerhalb der Auswahl löschen',lambda:window.cut_selection(True),True),
            ('auto-crop','Einfarbige Ränder entfernen …',window.auto_crop_dialog,True),
            ('custom-selection','Eigene Auswahl …',window.selection_dialog,True),
            ('select','Ausschnitt auswählen',lambda:window.crop_toggle.set_active(True),True),
            ('crop','Zuschneiden (Strg+Y)',window.apply_crop,True)]),
        ('Bild', [
            ('resize','Größe ändern / Resample …',window.resize_dialog,True),
            ('blank','Neues Bild …',window.blank_dialog,False),
            ('palette','Farben reduzieren …',window.palette_dialog,True),
            ('swap','Farbkanäle tauschen …',window.swap_dialog,True),
            ('histogram','Histogramm …',window.histogram_dialog,True),
            ('rotate-left','90° nach links drehen',lambda:window.rotate(False),True),
            ('rotate-right','90° nach rechts drehen',lambda:window.rotate(True),True),
            ('fine-rotation','Frei drehen …',window.fine_rotation_dialog,True),
            ('red-eye','Rote Augen korrigieren …',window.red_eye_dialog,True),
            ('effects','Effekte …',window.effects_dialog,True),
            ('canvas','Leinwand erweitern …',window.canvas_dialog,True),
            ('border','Rahmen hinzufügen …',window.border_dialog,True),
            ('mirror','Horizontal spiegeln',lambda:window.edit(lambda m:m.effect('mirror')),True),
            ('flip','Vertikal spiegeln',lambda:window.edit(lambda m:m.effect('flip')),True),
            ('grayscale','Graustufen',lambda:window.edit(lambda m:m.effect('grayscale')),True),
            ('invert','Negativ',lambda:window.edit(lambda m:m.effect('invert')),True),
            ('autocontrast','Automatischer Kontrast',lambda:window.edit(lambda m:m.effect('autocontrast')),True),
            ('adjust','Bildanpassungen …',window.adjust_dialog,True),
            ('adjust-values','Helligkeit / Kontrast / Farbe …',window.adjust_values_dialog,True),
            ('filter','Schärfen / Weichzeichnen …',window.filter_dialog,True),
            ('text','Text einfügen …',window.text_dialog,True),
            ('watermark','Wasserzeichen …',window.watermark_dialog,True),
            ('info','Bildinformationen (I)',window.show_info,True)]),
        ('Ansicht', [
            ('zoom-in','Vergrößern',lambda:window.zoom(1.25),True),
            ('zoom-out','Verkleinern',lambda:window.zoom(.8),True),
            ('fit','Einpassen',window.fit_image,True),
            ('actual-size','100 % anzeigen',window.actual_size,True),
            ('fullscreen','Vollbild (Enter)',window.toggle_fullscreen,False),
            ('thumbnails','Vorschaubilder …',window.toggle_sidebar,False),
            ('slideshow','Diashow starten / stoppen (F9)',window.toggle_slideshow,True),
            ('slideshow-options','Diashow-Intervall …',window.slideshow_settings,False),
            ('refresh-view','Ansicht aktualisieren',window.refresh_view,True),
            ('fit-desktop','An Desktop anpassen',window.fit_desktop,True),
            ('fit-window','Ins Fenster einpassen',lambda:window.set_view_mode('all'),True),
            ('window-to-image','Fenster an Bild anpassen',window.window_to_image,True),
            ('zoom-lock','Zoom sperren / lösen',window.toggle_zoom_lock,True),
            ('tag','Bild markieren',lambda:window.tag_image(True),True),
            ('untag','Markierung entfernen',lambda:window.tag_image(False),True),
            ('tagged','Markierte Bilder anzeigen',window.show_tagged,False),
            ('span','Vollbild über alle Monitore',window.toggle_span,True),
            ('toggle-menu','Menüleiste ein- / ausblenden',lambda:window.toggle_chrome('menu'),False),
            ('toggle-toolbar','Symbolleiste ein- / ausblenden',lambda:window.toggle_chrome('toolbar'),False),
            ('toggle-status','Statuszeile ein- / ausblenden',lambda:window.toggle_chrome('status'),False),
            ('toggle-border','Fensterrahmen ein- / ausblenden',lambda:window.toggle_chrome('border'),False),
            ('animation','Animation starten / stoppen',lambda:window.toggle_slideshow(True),True)]),
        ('Extras', [('preferences','Ansicht einstellen …',window.preferences_dialog,False),
                    ('panorama','Bilder zusammenfügen …',window.panorama_dialog,False),
                    ('batch','Stapelverarbeitung …',window.batch_dialog,False)]),
        ('Hilfe', [('shortcuts','Tastenkürzel …',window.shortcut_help,False),
                   ('about','Über Bildblick',window.about_dialog,False)]),
    ]
    for title, entries in groups:
        submenu = Gio.Menu()
        for name,label,callback,requires_image in entries:
            action = Gio.SimpleAction.new(name,None)
            action.connect('activate',lambda _a,_p,cb=callback:cb())
            window.add_action(action)
            actions.append((action,requires_image))
            item = Gio.MenuItem.new(label,'win.'+name)
            from shortcuts import MENU_SHORTCUTS
            if name in MENU_SHORTCUTS:
                item.set_attribute_value('accel',GLib.Variant('s',MENU_SHORTCUTS[name]))
            submenu.append_item(item)
        menu.append_submenu(title,submenu)
    return menu, actions
