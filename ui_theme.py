"""Shared native GTK design tokens and accessible components."""
from gi.repository import Gtk, Gdk

CSS = '''
@define-color ink #242424;
@define-color muted #626262;
@define-color surface #f5f5f3;
@define-color card #fafaf9;
@define-color line #dededb;
@define-color accent_color #242424;
@define-color theme_selected_bg_color #242424;
@define-color accent_bg_color #242424;
@define-color accent_fg_color #ffffff;
@define-color window_bg_color #f5f5f3;
@define-color window_fg_color #242424;
window { border-radius: 24px; background: @surface; color: @ink; font-family: Inter, "Cantarell", sans-serif; font-size: 14px; }
headerbar { background: @surface; border: none; box-shadow: none; padding: 10px 16px; }
headerbar .title { font-weight: 600; }
button { background: transparent; background-image: none; color: @ink; border: 1px solid transparent; border-radius: 24px; min-height: 34px; padding: 4px 14px; box-shadow: none; text-shadow: none; }
button:hover { background: #e7e7e4; }
button:active { background: #d9d9d5; }
button:checked, button.primary, button.suggested-action { background: @ink; color: white; }
button.primary:hover, button.suggested-action:hover { background: #404040; }
button:disabled { opacity: .42; }
button:focus-visible, entry:focus-within, spinbutton:focus-within, scale:focus-visible, switch:focus-visible, checkbutton:focus-visible { outline: 2px solid @ink; outline-offset: 3px; }
.muted, .dim-label { color: @muted; opacity: 1; }
.small { font-size: 12px; }
.section-title { font-weight: 600; }
.dialog-title { font-size: 22px; font-weight: 600; }
.brand { font-size: 17px; font-weight: 600; letter-spacing: -.5px; }
.card { background: @card; border: 1px solid white; border-radius: 20px; padding: 16px; }
.inspector button { padding: 2px 8px; min-height: 28px; }
.inspector { padding: 8px 16px 16px 8px; }
.tool-strip { padding: 4px 16px; }
.workspace { background: @surface; }
.zoom-dock { background: #ffffff; border: 1px solid @line; border-radius: 28px; padding: 4px; box-shadow: 0 3px 12px alpha(black,.04); }
.zoom-dock button { min-width: 24px; padding: 4px 8px; }
.sidebar { background: #eeefeb; border-radius: 18px; padding: 12px; }
scale { padding: 10px 0; }
scale trough { min-height: 3px; background: @line; border-radius: 8px; }
scale highlight { min-height: 3px; background: #8c8c87; border: none; box-shadow: none; background-image: none; }
.inspector .card { padding: 12px; }
.inspector scale { padding: 2px 0; min-height: 0; }
window .titlebar:not(headerbar) { min-height: 0; padding: 0; margin: 0; border: none; background: @surface; box-shadow: none; }
.scrim { background: alpha(black,.35); }
scale slider { min-width: 14px; min-height: 14px; background: white; border: 1px solid #b6b6b0; border-radius: 100%; box-shadow: 0 2px 5px alpha(black,.1); }
scale:disabled { opacity: .4; }
entry, spinbutton, dropdown, combobox button { background: white; color: @ink; border: 1px solid @line; border-radius: 12px; min-height: 34px; box-shadow: none; }
entry { padding: 3px 10px; }
spinbutton entry { border: none; background: transparent; }
spinbutton button { border-radius: 8px; min-height: 30px; padding: 2px 8px; }
switch { background: #d8d8d3; border: 1px solid #aaa; border-radius: 20px; min-height: 24px; }
switch:checked { background: @ink; }
switch slider { border: 1px solid #a0a09a; box-shadow: none; background: white; border-radius: 50%; min-width: 22px; min-height: 22px; }
checkbutton check, checkbutton radio { border: 1px solid #95958f; background: white; color: white; }
checkbutton check:checked, checkbutton radio:checked { background: @ink; }
.choice { border: 1px solid transparent; border-radius: 14px; padding: 10px; min-height: 48px; }
.choice:checked { background: white; border-color: #c6c6c0; }
.choice:hover { background: #eeeeeb; }
window.dialog { background: #f2f2f0; border-radius: 22px; }
window.dialog headerbar { background: transparent; padding: 4px 12px; }
window.dialog .dialog-action-area { padding: 12px 24px 20px; }
popover contents { background: @card; color: @ink; border: 1px solid @line; border-radius: 16px; padding: 8px; }
popover modelbutton { border-radius: 8px; min-height: 30px; }
popover modelbutton:hover { background: #e7e7e4; }
separator { background: @line; min-height: 1px; }
.error { color: #a02020; }
.status-bar { color: @muted; font-size: 12px; }
textview text { background: @card; color: @ink; }
'''


def install_theme():
    display = Gdk.Display.get_default()
    if not display:
        return
    settings = Gtk.Settings.get_for_display(display)
    settings.set_property('gtk-application-prefer-dark-theme', False)
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode())
    Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    return provider


def label(text, css=None, **kwargs):
    widget = Gtk.Label(label=text, xalign=0, **kwargs)
    if css:
        for name in css.split():
            widget.add_css_class(name)
    return widget


def card(title=None):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    box.add_css_class('card')
    if title:
        box.append(label(title, 'section-title'))
    return box


def accessible(widget, name):
    widget.update_property([Gtk.AccessibleProperty.LABEL], [name])
    return widget


def icon_button(icon, title, callback):
    button = Gtk.Button(icon_name=icon, tooltip_text=title)
    accessible(button, title)
    button.connect('clicked', lambda *_: callback())
    return button
