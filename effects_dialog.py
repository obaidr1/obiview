"""Direct effect selection with isolated, cancellable asynchronous previews."""
from PIL import Image
from gi.repository import Gtk, GLib
from dialog_layout import StandardDialog
from editor_ui import preview_pixbuf
from image_tools import EFFECTS, EFFECT_PARAMETERS, mixed_effect
from ui_theme import accessible, card, label


class EffectsDialog(StandardDialog):
    def __init__(self, parent):
        super().__init__(title='Effekte', transient_for=parent, modal=True,
                         default_width=860, default_height=700)
        self.parent = parent
        self.source = parent.model.image.copy()
        self.source.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        self.original = preview_pixbuf(self.source)
        self.preview = None
        self.name = 'sepia'
        self.settings = {name: [5, 100] for name in EFFECTS}
        self.generation = 0
        self.timer = 0
        self.running = False
        self.closed = False
        self.syncing = False
        self.ready = False
        self.set_titlebar(Gtk.Box())
        self.add_button('Abbrechen', Gtk.ResponseType.CANCEL)
        self.accept = self.add_button('Anwenden', Gtk.ResponseType.ACCEPT)
        self.accept.add_css_class('primary')
        actions = self.accept.get_parent()
        for side in ('start', 'end', 'bottom'):
            getattr(actions, 'set_margin_' + side)(20)
        actions.set_margin_top(12)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       margin_start=20, margin_end=20, margin_top=20)
        body.append(label('Effekte', 'dialog-title'))
        body.append(label('Effekt auswählen, einstellen und am Bild vergleichen.', 'muted',wrap=True))
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=20, vexpand=True)
        preview_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, hexpand=True)
        self.picture = Gtk.Picture(hexpand=True, vexpand=True, can_shrink=True)
        self.picture.set_size_request(-1, 160); self.picture.set_vexpand(False)
        self.picture.set_pixbuf(self.original)
        accessible(self.picture, 'Live-Vorschau des ausgewählten Effekts')
        preview_area.append(self.picture)
        self.compare = Gtk.ToggleButton(label='Original vergleichen')
        self.compare.connect('toggled', self.show_preview)
        preview_area.append(self.compare)
        self.note = label('', 'small muted', wrap=True)
        preview_area.append(self.note)
        content.append(preview_area)

        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        choices = card('Effekt auswählen')
        grid = Gtk.Grid(column_spacing=6, row_spacing=6, column_homogeneous=True)
        self.buttons = {}
        group = None
        for i, (name, title) in enumerate(EFFECTS.items()):
            button = Gtk.ToggleButton(label=title)
            button.add_css_class('effect-choice')
            accessible(button, title)
            if group is not None:
                button.set_group(group)
            else:
                group = button
            button.set_active(name == self.name)
            button.connect('toggled', self.select_effect, name)
            grid.attach(button, i % 2, i // 2, 1, 1)
            self.buttons[name] = button
        choices.append(grid)
        controls.append(choices)
        settings = card()
        self.effect_title = label(EFFECTS[self.name], 'section-title')
        settings.append(self.effect_title)
        self.strength, self.strength_value, strength_row = self.slider('Intensität', 0, 100)
        settings.append(strength_row)
        self.amount, self.amount_value, self.amount_row = self.slider('Radius', 1, 100)
        self.amount_title = self.amount_row.get_first_child().get_first_child()
        settings.append(self.amount_row)
        reset = Gtk.Button(label='Effekt zurücksetzen')
        reset.connect('clicked', self.reset)
        settings.append(reset)
        controls.append(settings)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_size_request(340, -1)
        scroll.set_child(controls)
        self.controls_scroll = scroll
        content.append(scroll)
        body.append(content)
        self.get_content_area().append(body)
        self.connect('response', self.respond)
        self.connect('close-request', self.close_requested)
        parent.dialogs.append(self)
        parent.set_scrim(True)
        self.load_settings()
        self.present()

    def slider(self, title, lower, upper):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        line = Gtk.Box()
        line.append(label(title, hexpand=True))
        value = label('', 'small muted')
        line.append(value)
        box.append(line)
        slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lower, upper, 1)
        slider.set_draw_value(False)
        accessible(slider, title)
        slider.connect('value-changed', self.changed)
        box.append(slider)
        return slider, value, box

    def select_effect(self, button, name):
        if button.get_active():
            self.name = name
            self.load_settings()

    def load_settings(self):
        self.syncing = True
        amount, strength = self.settings[self.name]
        self.effect_title.set_text(EFFECTS[self.name])
        parameter = EFFECT_PARAMETERS.get(self.name)
        self.amount_row.set_visible(parameter is not None)
        if parameter:
            title, lower, upper, _unit = parameter
            self.amount_title.set_text(title)
            accessible(self.amount, title)
            self.amount.set_range(lower, upper)
            self.amount.set_value(amount)
        self.strength.set_value(strength)
        self.syncing = False
        self.changed()

    def reset(self, *_args):
        self.settings[self.name] = [5, 100]
        self.compare.set_active(False)
        self.load_settings()

    def changed(self, *_args):
        if self.syncing or self.closed:
            return
        amount = round(self.amount.get_value()) if self.name in EFFECT_PARAMETERS else 5
        strength = round(self.strength.get_value())
        self.settings[self.name] = [amount, strength]
        self.strength_value.set_text(f'{strength} %')
        unit = EFFECT_PARAMETERS.get(self.name, ('', 0, 0, ''))[3]
        self.amount_value.set_text(f'{amount} {unit}'.strip())
        self.generation += 1
        self.ready = False
        self.accept.set_sensitive(False)
        self.note.set_text('Vorschau wird berechnet …')
        if self.timer:
            GLib.source_remove(self.timer)
        self.timer = GLib.timeout_add(120, self.render)

    def show_preview(self, *_args):
        if not self.closed:
            self.picture.set_pixbuf(self.original if self.compare.get_active() else self.preview or self.original)

    def render(self):
        self.timer = 0
        if self.closed:
            return False
        if self.running:
            self.timer = GLib.timeout_add(120, self.render)
            return False
        generation, name = self.generation, self.name
        amount, strength = self.settings[name]
        self.running = True

        def done(image):
            self.running = False
            if self.closed or generation != self.generation:
                return
            self.preview = preview_pixbuf(image)
            self.ready = True
            self.accept.set_sensitive(strength > 0)
            self.note.set_text('Verkleinerte Vorschau · Anwenden in Originalauflösung'
                               if self.source.size != self.parent.model.image.size
                               else 'Vorschau · noch nicht angewendet')
            self.show_preview()

        def failed(error):
            self.running = False
            if not self.closed and generation == self.generation:
                self.note.set_text(f'Vorschau fehlgeschlagen: {error}')

        self.parent.submit(lambda: mixed_effect(self.source, name, amount, strength), done, failed)
        return False

    def close_requested(self, *_args):
        self.respond(self, Gtk.ResponseType.CANCEL)
        return True

    def respond(self, _dialog, response):
        if self.closed:
            return
        apply = response == Gtk.ResponseType.ACCEPT
        if apply and (not self.ready or not self.accept.get_sensitive()):
            return
        name = self.name
        amount, strength = self.settings[name]
        self.closed = True
        self.generation += 1
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = 0
        self.parent.dialogs.remove(self)
        self.parent.set_scrim(False)
        self.destroy()
        if apply:
            self.parent.edit(lambda model: model.replace(mixed_effect(model.image, name, amount, strength)))
