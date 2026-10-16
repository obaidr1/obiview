"""Shared shortcut catalogue and exact modifier dispatch for the viewer."""
from gi.repository import Gdk

# Each row: keys, action method, positional arguments, needs image, description.
BINDINGS = [
 ('space','navigate',(1,),True,'Nächstes Bild'),('BackSpace','navigate',(-1,),True,'Vorheriges Bild'),
 ('Right','browse_or_scroll',('right',),True,'Nächstes Bild / nach rechts scrollen'),
 ('Left','browse_or_scroll',('left',),True,'Vorheriges Bild / nach links scrollen'),
 ('Down','browse_or_scroll',('down',),True,'Nächstes Bild / nach unten scrollen'),
 ('Up','browse_or_scroll',('up',),True,'Vorheriges Bild / nach oben scrollen'),
 ('Page_Down','browse_or_scroll',('bottom',),True,'Nächstes Bild / zum unteren Bildrand'),
 ('Page_Up','browse_or_scroll',('top',),True,'Vorheriges Bild / zum oberen Bildrand'),
 ('Home','browse_or_scroll',('home',),True,'Erste Datei / linker Bildrand'),
 ('End','browse_or_scroll',('end',),True,'Letzte Datei / rechter Bildrand'),
 ('ctrl+Page_Down','change_frame',(1,),True,'Nächste Seite / nächster Frame'),
 ('ctrl+Page_Up','change_frame',(-1,),True,'Vorherige Seite / vorheriger Frame'),
 ('ctrl+Home','folder_edge',(False,),True,'Erste Datei'),('ctrl+End','folder_edge',(True,),True,'Letzte Datei'),
 ('x','tag_image',(True,),True,'Bild markieren'),('shift+x','tag_image',(False,),True,'Markierung entfernen'),
 ('shift+q','show_tagged',(),False,'Markierte Bilder in Vorschaubildern'),
 ('F2','file_action',('rename',),True,'Datei umbenennen'),('F6','file_action',('rename',),True,'Datei umbenennen'),
 ('F7','file_action',('move',),True,'Datei verschieben'),('F8','file_action',('copy',),True,'Datei kopieren'),
 ('b','batch_dialog',(),False,'Stapelverarbeitung'),('o','open_dialog',(),False,'Bild öffnen'),
 ('ctrl+o','open_dialog',(),False,'Bild öffnen'),('p','preferences_dialog',(),False,'Eigenschaften / Einstellungen'),
 ('s','save_dialog',(),True,'Speichern unter'),('ctrl+s','save_dialog',(),True,'Speicherdialog'),
 ('ctrl+shift+s','save_dialog',(),True,'Speichern unter'),('shift+e','external_editor',(),True,'Extern öffnen / bearbeiten'),
 ('ctrl+m','random_image',(),True,'Zufälliges Bild aus dem Ordner'),('ctrl+n','duplicate_window',(),False,'Aktuelles Bild in neuem Fenster'),
 ('ctrl+p','print_image',(),True,'Drucken'),('ctrl+alt+p','direct_print',(),True,'Direkt mit Druckvorgaben drucken'),
 ('d','clear_image',(),True,'Bild aus der Anzeige entfernen'),('shift+r','reopen',(),True,'Datei erneut laden'),
 ('shift+n','blank_dialog',(),False,'Neues Bild'),('Return','toggle_fullscreen',(),False,'Vollbild umschalten'),
 ('KP_Enter','toggle_fullscreen',(),False,'Vollbild umschalten'),('f','fit_toggle',(),True,'Desktop / Fenster; im Vollbild Ansichtsmodi wechseln'),
 ('F5','refresh_view',(),True,'Ansicht aktualisieren'),('1','number_view',(1,),True,'Ansicht aktualisieren; im Vollbild 1:1'),
 ('ctrl+h','actual_size',(),True,'Originalgröße 1:1'),('shift+w','set_view_mode',('all',),True,'Bild ins Fenster einpassen'),
 ('plus','zoom',(1.25,),True,'Vergrößern'),('equal','zoom',(1.25,),True,'Vergrößern'),('KP_Add','zoom',(1.25,),True,'Vergrößern'),
 ('minus','zoom',(.8,),True,'Verkleinern'),('KP_Subtract','zoom',(.8,),True,'Verkleinern'),
 ('shift+f','fit_desktop',(True,),True,'Nur große Bilder an Desktop anpassen'),
 ('shift+l','toggle_zoom_lock',(),True,'Zoom über Dateiwechsel hinweg sperren / lösen'),
 ('shift+o','window_to_image',(),True,'Fenster an dargestelltes Bild anpassen'),
 ('ctrl+shift+w','toggle_span',(),True,'Vollbild über alle Monitore umschalten'),
 ('h','image_effect',('mirror',),True,'Horizontal spiegeln'),('v','image_effect',('flip',),True,'Vertikal spiegeln'),
 ('i','show_info',(),True,'Bildinformationen'),('l','rotate',(False,),True,'90° links drehen'),('r','rotate',(True,),True,'90° rechts drehen'),
 ('ctrl+u','fine_rotation_dialog',(),True,'Freie Drehung'),('shift+g','adjust_dialog',(),True,'Farben / Gamma anpassen'),
 ('shift+s','image_effect',('sharpness',2),True,'Schärfen'),('shift+u','image_effect',('autocontrast',),True,'Automatische Farbkorrektur'),
 ('shift+y','red_eye_dialog',(),True,'Rote Augen in der Auswahl korrigieren'),
 ('Delete','file_action',('trash',),True,'Datei nach Bestätigung in den Papierkorb'),
 ('Insert','paste_image',(),False,'Bild aus Zwischenablage einfügen'),('ctrl+v','paste_image',(),False,'Bild einfügen'),
 ('ctrl+a','toggle_select_all',(),True,'Alles auswählen / Auswahl aufheben'),('ctrl+c','copy_image',(),True,'Bild / Auswahl kopieren'),
 ('shift+p','copy_filename',(),True,'Dateinamen kopieren'),('ctrl+x','cut_selection',(),True,'Auswahl ausschneiden'),
 ('ctrl+y','apply_crop',(),True,'Auf Auswahl zuschneiden'),('ctrl+z','undo',(),True,'Rückgängig'),
 ('ctrl+shift+y','auto_crop_dialog',(),True,'Einfarbige Bildränder entfernen'),('shift+c','selection_dialog',(),True,'Eigene Auswahl'),
 ('Escape','escape_view',(),False,'Vollbild verlassen / Fenster schließen'),('F1','shortcut_help',(),False,'Hilfe / Tastenkürzel'),
 ('a','about_dialog',(),False,'Über Bildblick'),('g','stop_slideshow',(),True,'Animation / Diashow stoppen'),
 ('t','toggle_sidebar',(),False,'Vorschaubilder öffnen / schließen'),('Tab','focus_thumbnails',(),False,'Zwischen Hauptfenster und Vorschaubildern wechseln'),
 ('ctrl+Tab','cycle_thumbnail_focus',(),False,'Fokus in Vorschaubildern wechseln'),('m','minimize',(),False,'Fenster minimieren'),
 ('alt+shift+s','toggle_chrome',('status',),False,'Statuszeile ein- / ausblenden'),
 ('alt+shift+t','toggle_chrome',('toolbar',),False,'Symbolleiste ein- / ausblenden'),
 ('alt+shift+m','toggle_chrome',('menu',),False,'Menüleiste ein- / ausblenden'),
 ('alt+shift+y','toggle_chrome',('border',),False,'Fensterrahmen ein- / ausblenden'),
 ('F11','fullscreen_cursor',(),False,'Vollbild öffnen / im Vollbild Mauszeiger umschalten'),
 ('n','toggle_fullscreen_text',(),False,'Bildtext im Vollbild ein- / ausblenden'),
 ('KP_5','center_view',(),True,'Bildausschnitt zentrieren'),('KP_Begin','center_view',(),True,'Bildausschnitt zentrieren'),
 # Existing non-conflicting Bildblick additions.
 ('ctrl+r','resize_dialog',(),True,'Größe ändern'),('ctrl+shift+z','redo',(),True,'Wiederholen'),
 ('ctrl+f','search_files',(),False,'Dateien suchen'),('ctrl+t','text_dialog',(),True,'Text einfügen'),
 ('F12','paint_dialog',(),True,'Zeichnen'),('F9','toggle_slideshow',(),True,'Diashow starten / stoppen'),
]
for n in range(1,10):
 BINDINGS.append((f'ctrl+{n}','navigate',(n,),True,f'{n} Bilder vorwärts'))
 BINDINGS.append((f'ctrl+shift+{n}','navigate',(-n,),True,f'{n} Bilder rückwärts'))
for n in range(2,7): BINDINGS.append((str(n),'number_view',(n,),True,'Vollbild-Ansichtsmodus '+str(n)))
for direction in ('Left','Right','Up','Down'):
 BINDINGS.append(('shift+'+direction,'move_selection_key',(direction.lower(),),True,'Auswahl um einen Pixel verschieben'))

LOOKUP = {row[0].lower():row for row in BINDINGS}
assert len(LOOKUP)==len(BINDINGS), 'Duplicate shortcut'


def normalized_key(key, modifiers):
    # Ignore lock/NumLock; do not let Super/Meta combinations trigger edits.
    if modifiers & (Gdk.ModifierType.SUPER_MASK | Gdk.ModifierType.META_MASK | Gdk.ModifierType.HYPER_MASK): return None
    parts=[]
    for name,flag in [('ctrl',Gdk.ModifierType.CONTROL_MASK),('alt',Gdk.ModifierType.ALT_MASK),('shift',Gdk.ModifierType.SHIFT_MASK)]:
        if modifiers & flag: parts.append(name)
    name=Gdk.keyval_name(Gdk.keyval_to_lower(key))
    if not name: return None
    # Plus often carries Shift on a keyboard; it is still the ordinary zoom key.
    if name in ('plus','equal','KP_Add','minus','KP_Subtract') and parts==['shift']: parts=[]
    return '+'.join(parts+[name.lower()])


def dispatch(window, key, modifiers):
    binding=LOOKUP.get(normalized_key(key,modifiers))
    if not binding: return False
    _keys,method,args,needs_image,_description=binding
    if method=='number_view' and args[0]!=1 and not window.full: return False
    if not needs_image or window.model.image is not None:
        getattr(window,method)(*args)
    return True


def display_scales(image, viewport, mode, upscale=False):
    iw,ih=image; vw,vh=viewport
    x,y=max(1,vw-8)/iw,max(1,vh-8)/ih
    if mode=='stretch': return x,y
    if mode=='width': return x,x
    if mode=='height': return y,y
    value=min(x,y)
    if mode=='small' or (mode=='window' and not upscale): value=min(1,value)
    return value,value


MENU_SHORTCUTS={
 'resize':'<Primary>r','save-as':'s','open':'o','new-window':'<Primary>n',
 'reopen':'<Shift>r','external':'<Shift>e','rename-file':'F2','move-file':'F7','copy-file':'F8',
 'trash-file':'Delete','print':'<Primary>p','direct-print':'<Primary><Alt>p','random':'<Primary>m',
 'clear':'d','undo':'<Primary>z','redo':'<Primary><Shift>z','paste':'Insert','copy':'<Primary>c',
 'copy-name':'<Shift>p','select-all':'<Primary>a','cut':'<Primary>x','auto-crop':'<Primary><Shift>y',
 'custom-selection':'<Shift>c','crop':'<Primary>y','blank':'<Shift>n','rotate-left':'l','rotate-right':'r',
 'fine-rotation':'<Primary>u','red-eye':'<Shift>y','mirror':'h','flip':'v','autocontrast':'<Shift>u',
 'adjust':'<Shift>g','info':'i','zoom-in':'plus','zoom-out':'minus','actual-size':'<Primary>h',
 'fullscreen':'Return','thumbnails':'t','slideshow':'F9','refresh-view':'F5','fit-desktop':'f',
 'fit-window':'<Shift>w','window-to-image':'<Shift>o','zoom-lock':'<Shift>l','tag':'x','untag':'<Shift>x',
 'tagged':'<Shift>q','span':'<Primary><Shift>w','toggle-menu':'<Alt><Shift>m',
 'toggle-toolbar':'<Alt><Shift>t','toggle-status':'<Alt><Shift>s','toggle-border':'<Alt><Shift>y',
 'preferences':'p','batch':'b','shortcuts':'F1','about':'a','paint':'F12','text':'<Primary>t','search-files':'<Primary>f'
}
