"""Shared direct choices and sliders with optional exact numeric entry."""
from gi.repository import Gtk, GObject
from ui_theme import accessible, selection_content


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
        selection_content(button, title)
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

    def __init__(self, lower, upper, step, value=0, title='Wert', exact=False):
        super().__init__(spacing=10, hexpand=True)
        self.syncing = False
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lower, upper, step)
        self.scale.set_hexpand(True)
        self.scale.set_size_request(140, -1)
        self.scale.set_draw_value(not exact)
        self.scale.set_digits(2 if step < 1 else 0)
        self.scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.number = Gtk.SpinButton.new_with_range(lower, upper, step) if exact else None
        accessible(self.scale, title)
        self.append(self.scale)
        if self.number is not None:
            self.number.set_digits(2 if step < 1 else 0)
            self.number.set_numeric(True)
            self.number.set_width_chars(4)
            accessible(self.number, title + ' – genauer Wert')
            self.append(self.number)
            self.number.connect('value-changed', self.changed, self.scale)
        self.scale.connect('value-changed', self.changed, self.number)
        self.set_value(value)

    def changed(self, widget, other):
        if self.syncing:
            return
        self.syncing = True
        if other is not None: other.set_value(widget.get_value())
        self.syncing = False
        self.emit('value-changed')

    def set_value(self, value):
        self.scale.set_value(value)

    def get_value(self):
        return self.scale.get_value()

    def get_value_as_int(self):
        return round(self.scale.get_value())

    def update(self):
        if self.number is not None: self.number.update()
