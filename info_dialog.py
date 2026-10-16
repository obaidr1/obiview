"""Image properties, independent DPI axes and readable source metadata."""
import threading
from gi.repository import Gtk
from dialog_layout import StandardDialog
from image_info import info_values, count_rgb_colors, metadata_text
from ui_theme import label, card, accessible


class ImageInfoDialog(StandardDialog):
    def __init__(self,parent):
        super().__init__(title='Bildinformationen',transient_for=parent,modal=True,
                         default_width=780,default_height=740)
        self.parent=parent; self.alive=True; self.cancel_count=threading.Event()
        self.children=[]; self.values={}; self.count_generation=0
        self.set_titlebar(Gtk.Box())
        close_button=self.add_button('Schließen',Gtk.ResponseType.CLOSE)
        close_button.add_css_class('primary')
        actions=close_button.get_parent()
        for side in ('start','end','bottom'): getattr(actions,'set_margin_'+side)(20)
        actions.set_margin_top(12)
        body=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,
                     margin_start=20,margin_end=20,margin_top=16,margin_bottom=16)
        body.append(label('Bildinformationen','dialog-title'))
        section=card(); grid=Gtk.Grid(column_spacing=18,row_spacing=8)
        section.append(grid); body.append(section)
        fields=[('filename','Dateiname'),('directory','Verzeichnis'),('path','Voller Pfad'),
                ('format','Format / Komprimierung'),('dpi','Auflösung (DPI)'),
                ('original_size','Originalgröße'),('current_size','Aktuelle Größe'),
                ('print_size','Druckgröße (aus DPI)'),('original_colors','Originalfarben'),
                ('current_colors','Aktuelle Farben'),('count','Gezählte RGB-Farben'),
                ('disk','Dateigröße auf Datenträger'),('memory','Bildspeicher'),
                ('index','Index im Ordner'),('modified','Datei geändert am'),
                ('load_time','Geladen in'),('page','Seite / Einzelbild')]
        for row,(key,title) in enumerate(fields):
            grid.attach(label(title,'muted'),0,row*2,1,1)
            if key=='dpi':
                widget=Gtk.Box(spacing=8)
                self.dpi_x=Gtk.SpinButton.new_with_range(1,9600,1)
                self.dpi_y=Gtk.SpinButton.new_with_range(1,9600,1)
                for spin,title in ((self.dpi_x,'Horizontale DPI'),(self.dpi_y,'Vertikale DPI')):
                    spin.set_digits(2); spin.set_width_chars(5); spin.set_max_width_chars(7); accessible(spin,title)
                widget.append(self.dpi_x); widget.append(label('×')); widget.append(self.dpi_y)
                self.dpi_button=Gtk.Button(label='Ändern')
                self.dpi_button.connect('clicked',self.change_dpi); widget.append(self.dpi_button)
            elif key=='count':
                widget=Gtk.Box(spacing=12)
                self.count_label=label('Berechnung …',hexpand=True)
                widget.append(self.count_label)
                self.count_active=Gtk.CheckButton(label='Zählen aktiv',active=True)
                self.count_active.connect('toggled',self.start_count); widget.append(self.count_active)
            else:
                widget=label('',selectable=True,wrap=True,max_width_chars=36,hexpand=True)
                self.values[key]=widget
            grid.attach(widget,0,row*2+1,1,1)
        self.note=label('DPI ändert die Druckgröße, nicht die Bildpixel. RGB-Farben werden ohne Alphakanal gezählt.','small muted',wrap=True)
        body.append(self.note)
        buttons=Gtk.Box(spacing=8,homogeneous=True)
        for name,title in (('exif','EXIF-Daten'),('iptc','IPTC-Daten'),('comment','Kommentar')):
            button=Gtk.Button(label=title)
            button.connect('clicked',lambda _b,n=name:self.show_metadata(n)); buttons.append(button)
        body.append(buttons)
        scroll=Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(body); self.get_content_area().append(scroll)
        self.connect('response',self.close_dialog)
        self.connect('close-request',lambda *_:(self.close_dialog(),True)[1])
        parent.dialogs.append(self); parent.set_scrim(True)
        self.refresh_values(); self.start_count(); self.present()

    def refresh_values(self):
        if not self.alive: return
        for key,value in info_values(self.parent.model,self.parent.folder_files).items():
            self.values[key].set_text(value)
        self.dpi_x.set_value(self.parent.model.dpi_pair[0])
        self.dpi_y.set_value(self.parent.model.dpi_pair[1])
        self.dpi_button.set_sensitive(True)
        fallback='dpi' not in self.parent.model.image.info
        self.note.set_text(('Keine DPI gespeichert: 96 DPI angenommen. ' if fallback else '')+
                           'DPI ändert die Druckgröße, nicht die Bildpixel. RGB-Farben werden ohne Alphakanal gezählt.')
        self.dpi_x.set_tooltip_text('Keine DPI gespeichert; 96 DPI angenommen.' if fallback else 'Horizontale Druckauflösung')
        self.dpi_y.set_tooltip_text('Keine DPI gespeichert; 96 DPI angenommen.' if fallback else 'Vertikale Druckauflösung')

    def change_dpi(self,*_):
        self.dpi_x.update(); self.dpi_y.update()
        x,y=self.dpi_x.get_value(),self.dpi_y.get_value()
        if (x,y)==self.parent.model.dpi_pair: return
        self.dpi_button.set_sensitive(False)
        self.parent.edit(lambda model:model.set_dpi(x,y),after=self.refresh_values)

    def start_count(self,*_):
        self.cancel_count.set(); self.cancel_count=threading.Event()
        self.count_generation+=1; generation=self.count_generation
        if not self.count_active.get_active():
            self.count_label.set_text('Deaktiviert'); return
        self.count_label.set_text('Berechnung …')
        image=self.parent.model.image; cancel=self.cancel_count
        def done(value):
            if self.alive and generation==self.count_generation and value is not None:
                self.count_label.set_text(f'{value:,}'.replace(',',' '))
        def failed(error):
            if self.alive and generation==self.count_generation: self.count_label.set_text(str(error))
        self.parent.submit(lambda:count_rgb_colors(image,cancel),done,failed)

    def show_metadata(self,kind):
        source=self.parent.model.source_info
        titles={'exif':'EXIF-Daten','iptc':'IPTC-Daten','comment':'Kommentar'}
        if kind=='comment': text=metadata_text(self.parent.model.comment) if self.parent.model.comment else 'Kein Kommentar vorhanden.'
        else:
            values=source.get(kind,{})
            text='\n\n'.join(f'{key}: {metadata_text(value)}' for key,value in values.items())
            if not text: text=f'Keine {titles[kind]} verfügbar.'
        dialog=StandardDialog(title=titles[kind],transient_for=self,modal=True,default_width=700,default_height=480)
        dialog.add_button('Schließen',Gtk.ResponseType.CLOSE)
        scroll=Gtk.ScrolledWindow(vexpand=True)
        view=Gtk.TextView(editable=False,wrap_mode=Gtk.WrapMode.WORD_CHAR,
                          left_margin=16,right_margin=16,top_margin=16,bottom_margin=16)
        view.get_buffer().set_text(text); scroll.set_child(view); dialog.get_content_area().append(scroll)
        dialog.text_view=view
        def close(*_):
            if dialog in self.children: self.children.remove(dialog)
            dialog.destroy()
            return True
        dialog.connect('response',close); dialog.connect('close-request',close)
        self.children.append(dialog); dialog.present(); return dialog

    def close_dialog(self,*_):
        if not self.alive: return
        self.alive=False; self.cancel_count.set(); self.count_generation+=1
        for child in list(self.children): child.destroy()
        self.children.clear()
        self.parent.dialogs.remove(self); self.parent.set_scrim(False); self.destroy()
