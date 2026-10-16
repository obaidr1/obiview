"""Shared direct choices and sliders with optional exact numeric entry."""
from gi.repository import Gtk, GObject
from ui_theme import accessible


class ChoiceButtons(Gtk.Grid):
    __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, columns=2, **kwargs):
        super().__init__(column_spacing=6, row_spacing=6, column_homogeneous=True, **kwargs)
        self.columns = columns
        self.buttons = {}
        self.active_id = None

    def append(self, ident, title):
        ident = str(ident)
        button = Gtk.ToggleButton(hexpand=True)
        text = Gtk.Label(label=title, wrap=True, max_width_chars=24)
        button.set_child(text)
        button.add_css_class('effect-choice')
        accessible(button, title)
        if self.buttons:
            button.set_group(next(iter(self.buttons.values())))
        index = len(self.buttons)
        self.buttons[ident] = button
        self.attach(button, index % self.columns, index // self.columns, 1, 1)
        button.connect('toggled', self.changed, ident)

    def changed(self, button, ident):
        if button.get_active():
            self.active_id = ident
            self.emit('changed')

    def get_active_id(self):
        return self.active_id

    def set_active_id(self, ident):
        if str(ident) not in self.buttons:
            return False
        self.buttons[str(ident)].set_active(True)
        return True


class SliderField(Gtk.Box):
    __gsignals__ = {'value-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, lower, upper, step, value=0, title='Wert'):
        super().__init__(spacing=10, hexpand=True)
        self.syncing = False
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lower, upper, step)
        self.scale.set_hexpand(True)
        self.scale.set_size_request(140, -1)
        self.scale.set_draw_value(False)
        self.number = Gtk.SpinButton.new_with_range(lower, upper, step)
        self.number.set_digits(2 if step < 1 else 0)
        self.number.set_numeric(True)
        self.number.set_width_chars(5)
        accessible(self.scale, title)
        accessible(self.number, title + ' – genauer Wert')
        self.append(self.scale)
        self.append(self.number)
        self.scale.connect('value-changed', self.changed, self.number)
        self.number.connect('value-changed', self.changed, self.scale)
        self.set_value(value)

    def changed(self, widget, other):
        if self.syncing:
            return
        self.syncing = True
        other.set_value(widget.get_value())
        self.syncing = False
        self.emit('value-changed')

    def set_value(self, value):
        self.number.set_value(value)
        self.scale.set_value(self.number.get_value())

    def get_value(self):
        return self.number.get_value()

    def get_value_as_int(self):
        return self.number.get_value_as_int()

    def update(self):
        self.number.update()
