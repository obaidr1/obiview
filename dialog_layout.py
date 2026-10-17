"""One geometry and scroll/action layout for every app-owned secondary surface."""
import json
import math
from pathlib import Path
from gi.repository import Gtk, Gdk, Pango
from ui_theme import label

_TOKENS = json.loads((Path(__file__).parent / 'design-system' / 'tokens.json').read_text())
MIN_DIALOG_WIDTH = int(_TOKENS['dialog-width-base'].removesuffix('px'))
DIALOG_WIDTH_CURVE = int(_TOKENS['dialog-width-per-complexity'].removesuffix('px'))
SCREEN_MARGIN = int(_TOKENS['dialog-screen-margin'].removesuffix('px'))


def _screen_limits(parent):
    display = parent.get_display() if parent else Gdk.Display.get_default()
    surface = parent.get_surface() if parent else None
    monitor = display.get_monitor_at_surface(surface) if surface else None
    if monitor is None:
        monitors = display.get_monitors() if display else None
        monitor = monitors.get_item(0) if monitors and monitors.get_n_items() else None
    if monitor:
        geometry = monitor.get_geometry()
        return max(1, geometry.width-SCREEN_MARGIN), max(1, geometry.height-SCREEN_MARGIN)
    return 1200, 900


def dialog_size(parent, element_count=0):
    """Return the content-count width target and the physical screen ceiling."""
    max_width, max_height = _screen_limits(parent)
    # Width grows with complexity, while the square-root curve avoids making
    # long forms span the whole display just because they contain many labels.
    target = MIN_DIALOG_WIDTH + math.sqrt(max(0, element_count-4))*DIALOG_WIDTH_CURVE
    return min(target, max_width), max_height


def control_count(widget):
    """Count visible controls and semantic display items; ignore widget internals."""
    control_types = (Gtk.Button, Gtk.CheckButton, Gtk.Entry, Gtk.Scale,
                     Gtk.DropDown, Gtk.Switch, Gtk.TextView, Gtk.ColorButton)
    def visit(node):
        if isinstance(node, control_types):
            return 1
        total = 1 if isinstance(node, (Gtk.Label, Gtk.Picture)) else 0
        nested = list(children(node))
        if isinstance(node, Gtk.Expander):
            child = node.get_child()
            if child is not None and child not in nested:
                nested.append(child)
        return total + sum(visit(child) for child in nested)
    return visit(widget)


def _natural_size(body, parent, element_count):
    width, screen_height = dialog_size(parent, element_count)
    minimum_width = body.measure(Gtk.Orientation.HORIZONTAL, -1)[0]
    width = min(max(width, minimum_width), _screen_limits(parent)[0])
    body_width = max(240, width)
    natural_height = body.measure(Gtk.Orientation.VERTICAL, body_width)[1]
    # Include the title, shell padding and persistent action row around the body.
    height = natural_height + 112
    return width, min(max(1, height), screen_height), natural_height


def children(widget):
    child = widget.get_first_child()
    while child:
        yield child
        child = child.get_next_sibling()


def normalize(widget):
    """Wrap content at the fixed width; one outer scroll owns vertical overflow."""
    if isinstance(widget, Gtk.Label):
        if widget.get_ellipsize() == Pango.EllipsizeMode.NONE:
            # Short action labels keep their words intact; prose and paths may wrap.
            widget.set_wrap(widget.get_wrap() or len(widget.get_text()) > 24)
            widget.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            widget.set_max_width_chars(36)
    if isinstance(widget, Gtk.SpinButton):
        # Keep values readable at the start of the field; GTK keeps its stepper
        # controls grouped at the trailing edge.
        widget.set_alignment(0.0)
        widget.set_width_chars(5)
        widget.set_max_width_chars(8)
    if isinstance(widget, Gtk.ScrolledWindow):
        widget.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        widget.set_propagate_natural_height(True)
        widget.set_min_content_height(-1)
        widget.set_size_request(-1, -1)
    nested = list(children(widget))
    # Collapsed expanders keep their child unparented. Style it before the first
    # expansion too, so advanced fields obey the same layout as visible ones.
    if isinstance(widget, Gtk.Expander):
        child = widget.get_child()
        if child is not None and child not in nested:
            nested.append(child)
    for child in nested:
        normalize(child)


class StandardDialog(Gtk.Dialog):
    """Content-sized shell with a screen-limited body and persistent action row."""
    def __init__(self, compact=False, **kwargs):
        kwargs.pop('default_width', None)
        kwargs.pop('default_height', None)
        parent = kwargs.get('transient_for')
        width, height = dialog_size(parent)
        self.compact = compact
        super().__init__(**kwargs, default_width=width, default_height=1 if compact else height, resizable=True)
        self.add_css_class('dialog')
        self.set_titlebar(Gtk.Box())
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                            margin_start=24, margin_end=24, margin_top=24, margin_bottom=16)
        self.body_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        self.body_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.body_scroll.set_child(self.body)
        if compact:
            self.body_scroll.set_propagate_natural_height(True)
            self.body_scroll.set_max_content_height(max(100, height-120))
        super().get_content_area().append(self.body_scroll)
        self.action_buttons = []
        self.prepared = False
        keys = Gtk.EventControllerKey()
        keys.connect('key-pressed', self._key)
        self.add_controller(keys)

    def _key(self, _controller, key, _code, modifiers):
        if key == Gdk.KEY_Escape and not modifiers:
            self.response(Gtk.ResponseType.CANCEL)
            return True
        return False

    def get_content_area(self):
        return self.body

    def add_button(self, text, response):
        button = super().add_button(text, response)
        self.action_buttons.append(button)
        actions = button.get_parent()
        for side, amount in [('start',24),('end',24),('top',12),('bottom',24)]:
            getattr(actions, 'set_margin_'+side)(amount)
        if response in (Gtk.ResponseType.ACCEPT, Gtk.ResponseType.OK, Gtk.ResponseType.CLOSE):
            button.add_css_class('primary')
        return button

    def present(self):
        if not self.prepared:
            # Existing dialog content may have its own padding; shell owns the outer inset.
            for child in children(self.body):
                for side in ('start','end','top','bottom'):
                    getattr(child,'set_margin_'+side)(0)
                if isinstance(child, Gtk.ScrolledWindow):
                    inner = child.get_child()
                    if isinstance(inner, Gtk.Viewport): inner = inner.get_child()
                    if inner:
                        for side in ('start','end','top','bottom'):
                            getattr(inner,'set_margin_'+side)(0)
            normalize(self.body)
            def has_title(widget):
                return (isinstance(widget,Gtk.Label) and widget.has_css_class('dialog-title')) or any(has_title(c) for c in children(widget))
            if not has_title(self.body): self.body.prepend(label(self.get_title(), 'dialog-title', wrap=True))
            for button in self.action_buttons:
                actions=button.get_parent()
                for side, amount in [('start',24),('end',24),('top',12),('bottom',24)]:
                    getattr(actions,'set_margin_'+side)(amount)
            self.prepared = True
        if self.compact:
            # GtkScrolledWindow may shrink below its propagated natural height.
            # Reserve the wrapped body's actual height, capped for long messages.
            width, height, natural = _natural_size(
                self.body, self.get_transient_for(), control_count(self.body))
            _screen_width, screen_height = _screen_limits(self.get_transient_for())
            body_limit = max(100, screen_height-120)
            self.body_scroll.set_min_content_height(min(natural, body_limit))
            self.body_scroll.set_max_content_height(body_limit)
        else:
            width, height, _natural = _natural_size(
                self.body, self.get_transient_for(), control_count(self.body))
        self.set_default_size(width, height)
        super().present()


class ModuleWindow(Gtk.Window):
    """Non-modal modules share the dialog footprint and a persistent close action."""
    def __init__(self, parent, title):
        width,height=dialog_size(parent)
        super().__init__(title=title, transient_for=parent, destroy_with_parent=True,
                         default_width=width, default_height=height, resizable=True)
        self.add_css_class('dialog'); self.set_titlebar(Gtk.Box())
        root=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16,
                     margin_start=24,margin_end=24,margin_top=24,margin_bottom=24)
        heading=label(title,'dialog-title',wrap=True,max_width_chars=36)
        heading.set_wrap_mode(Pango.WrapMode.WORD_CHAR); root.append(heading)
        self.module_content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,vexpand=True)
        root.append(self.module_content)
        close=Gtk.Button(label='Schließen',halign=Gtk.Align.END); close.add_css_class('primary')
        close.connect('clicked',lambda *_:self.close()); root.append(close)
        super().set_child(root)
        keys=Gtk.EventControllerKey()
        keys.connect('key-pressed',lambda _c,key,_code,_mods:(self.close(),True)[1] if key==Gdk.KEY_Escape else False)
        self.add_controller(keys)

    def present(self):
        width, height, _natural = _natural_size(
            self.module_content, self.get_transient_for(), control_count(self.module_content))
        self.set_default_size(width, height)
        super().present()

    def set_child(self, child):
        previous=self.module_content.get_first_child()
        if previous: self.module_content.remove(previous)
        if child:
            child.set_hexpand(True); child.set_vexpand(True)
            self.module_content.append(child)


def module_window(parent, title):
    return ModuleWindow(parent, title)
