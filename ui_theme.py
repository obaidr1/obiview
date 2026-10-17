"""Shared native GTK design tokens and accessible components."""
import json
import re
from pathlib import Path
from gi.repository import Gtk, Gdk

TOKENS = json.loads((Path(__file__).parent / "design-system/tokens.json").read_text())

CSS_TEMPLATE = '''
@define-color ink {{color-ink}};
@define-color muted {{color-muted}};
@define-color surface {{color-surface}};
@define-color card {{color-card}};
@define-color line {{color-line}};
@define-color accent_color {{color-ink}};
@define-color theme_selected_bg_color {{color-ink}};
@define-color accent_bg_color {{color-ink}};
@define-color accent_fg_color {{color-white}};
@define-color window_bg_color {{color-surface}};
@define-color window_fg_color {{color-ink}};
window { border-radius: {{radius-dialog}}; background: @surface; color: @ink; font-family: Inter, "Cantarell", sans-serif; font-size: {{text-body}}; }
headerbar { background: @surface; border: none; box-shadow: none; padding: 10px 16px; }
headerbar .title { font-weight: 600; }
button { background: transparent; background-image: none; color: @ink; border: 1px solid transparent; border-radius: {{radius-dialog}}; min-height: 34px; padding: 4px 14px; box-shadow: none; text-shadow: none; }
button:hover { background: {{color-hover}}; }
button:active { background: {{color-active}}; }
button.primary, button.suggested-action { background: @ink; color: white; }
button.primary:hover, button.suggested-action:hover { background: {{color-ink-hover}}; }
button:disabled { opacity: .42; }
button:focus-visible, entry:focus-within, spinbutton:focus-within, scale:focus-visible, switch:focus-visible, checkbutton:focus-visible { outline: 2px solid @ink; outline-offset: 3px; }
.muted, .dim-label { color: @muted; opacity: 1; }
.small { font-size: {{text-small}}; }
.section-title { font-weight: 600; }
.dialog-title { font-size: {{text-title}}; font-weight: 600; }
.brand { font-size: 17px; font-weight: 600; letter-spacing: -.5px; }
.card { background: @card; border: 1px solid transparent; border-radius: {{radius-card}}; padding: 16px; }
.inspector button { padding: 4px 10px; min-height: 34px; }
.inspector { padding: 8px 16px 16px 8px; }
.effect-choice { background: @card; border: 1px solid {{color-control-border}}; border-radius: {{radius-control}}; padding: 4px 10px; min-height: 40px; }
.effect-choice:hover { background: {{color-hover}}; }
.effect-choice:checked { background: {{color-selected}}; border-color: {{color-selected-border}}; }
.tool-strip { padding: 4px 16px; }
.workspace { background: @surface; }
.zoom-dock { background: {{color-white}}; border: 1px solid @line; border-radius: 28px; padding: 4px; box-shadow: 0 3px 12px alpha(black,.04); }
.zoom-dock button { min-width: 24px; padding: 4px 8px; }
.sidebar { background: #eeefeb; border-radius: 18px; padding: 12px; }
scale { padding: 10px 0; }
scale trough { min-height: 3px; background: @line; border-radius: 8px; }
scale highlight { min-height: 3px; background: {{color-track}}; border: none; box-shadow: none; background-image: none; }
.inspector .card { padding: 12px; }
.inspector scale { padding: 2px 0; min-height: 0; }
window .titlebar:not(headerbar) { min-height: 0; padding: 0; margin: 0; border: none; background: @surface; box-shadow: none; }
.scrim { background: alpha(black,.35); }
scale slider { min-width: 14px; min-height: 14px; background: white; border: 1px solid {{color-slider-border}}; border-radius: 100%; box-shadow: 0 2px 5px alpha(black,.1); }
scale:disabled { opacity: .4; }
entry, spinbutton, dropdown, combobox button { background: white; color: @ink; border: 1px solid {{color-control-border}}; border-radius: {{radius-control}}; min-height: 34px; box-shadow: none; }
entry { padding: 3px 10px; }
spinbutton entry { border: none; background: transparent; }
spinbutton button { border-radius: 8px; min-height: 30px; padding: 2px 8px; }
switch { background: #d8d8d3; border: 1px solid #aaa; border-radius: {{radius-card}}; min-height: 24px; }
switch:checked { background: @ink; }
switch slider { border: 1px solid #a0a09a; box-shadow: none; background: white; border-radius: 50%; min-width: 22px; min-height: 22px; }
checkbutton check, checkbutton radio { border: 1px solid #95958f; background: white; color: white; }
checkbutton check:checked, checkbutton radio:checked { background: @ink; }
.choice { border: 1px solid {{color-control-border}}; border-radius: 14px; padding: 10px; min-height: 48px; }
.choice:checked { background: {{color-selected}}; border-color: {{color-selected-border}}; }
.choice:hover { background: #eeeeeb; }
.segmented-choice button.effect-choice { background: white; border: 1px solid {{color-control-border}}; border-radius: 10px; min-height: 40px; }
.segmented-choice button.effect-choice:hover { background: {{color-hover}}; }
.segmented-choice button.effect-choice:checked { background: {{color-selected}}; border-color: {{color-selected-border}}; }
.segmented-choice .selection-mark { opacity: 0; min-width: 0; }
.ratio-link { min-width: 40px; min-height: 40px; border: 1px solid {{color-control-border}}; border-radius: 12px; background: white; }
.ratio-link:checked { background: {{color-selected}}; border-color: {{color-selected-border}}; }
.ratio-link-indicator { min-width: 36px; min-height: 36px; color: @ink; }
.unit-suffix { padding-inline: 4px; }
window.dialog { background: @surface; border-radius: {{radius-dialog}}; }
window.dialog headerbar { background: transparent; padding: 4px 12px; }
window.dialog .dialog-action-area { padding: 0; }
popover contents { background: @card; color: @ink; border: 1px solid @line; border-radius: 16px; padding: 8px; }
popover modelbutton { border-radius: 8px; min-height: 30px; }
popover modelbutton:hover { background: {{color-hover}}; }
separator { background: @line; min-height: 1px; }
.error { color: {{color-error}}; }
window.viewer { border-radius: 14px; }
window.viewer > headerbar, window.viewer headerbar { min-height: 30px; padding: 2px 8px; }
window.viewer headerbar button { min-height: 22px; min-width: 22px; padding: 0 4px; }
.viewer-toolbar button { min-width: 24px; min-height: 26px; padding: 2px; border-radius: 8px; }
.viewer-toolbar separator { min-width: 1px; min-height: 20px; margin-top: 4px; margin-bottom: 4px; }
.viewer-toolbar .file-counter { background: white; border: 1px solid @line; border-radius: 8px; padding: 2px 6px; font-size: {{text-small}}; }
window.viewer menubar { background: @surface; padding: 0 8px; border-bottom: 1px solid @line; }
window.viewer menubar > item { padding: 3px 8px; min-height: 18px; border-radius: 6px; }
window.viewer menubar > item:hover { background: {{color-hover}}; }
.fullscreen-info { color: white; background: alpha(black,.65); border-radius: {{radius-control}}; padding: 8px 12px; font-size: {{text-small}}; }
.status-bar { color: @muted; font-size: {{text-small}}; }
textview text { background: @card; color: @ink; }
button:checked { background: {{color-selected}}; color: @ink; }
button.effect-choice { background: @card; border-color: {{color-control-border}}; }
button.effect-choice:hover { background: {{color-hover}}; }
button.effect-choice:checked { background: {{color-selected}}; border-color: {{color-selected-border}}; }
.choice:checked { background: {{color-selected}}; border-color: {{color-selected-border}}; }
.preview-surface { background: {{color-preview}}; border-radius: {{radius-control}}; }
.numeric-value { font-size: {{text-body}}; font-weight: 600; font-feature-settings: "tnum"; }
.info-value { color: @ink; }
.inspector { padding: 0; }
.inspector .card { padding: 16px; }
.inspector scale { padding: 6px 0; }

'''

CSS = re.sub(r'\{\{([\w-]+)\}\}', lambda match: TOKENS[match[1]], CSS_TEMPLATE)


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


def selection_content(button, title, content=None):
    """Show selection through a clear control boundary and active surface."""
    row = Gtk.Box(spacing=8, hexpand=True)
    if content is None:
        content = Gtk.Label(label=title, wrap=True, max_width_chars=24, xalign=0, hexpand=True)
    row.append(content)
    button.set_child(row)
    button.add_css_class('effect-choice')
    accessible(button, title)
    return button


def ratio_link_state(button):
    """Keep the link icon and accessible tooltip aligned with its state."""
    linked = button.get_active()
    button.set_tooltip_text('Seitenverhältnis beibehalten' if linked else 'Seitenverhältnis frei ändern')
    child = button.get_child()
    if isinstance(child, Gtk.Image):
        child.set_from_icon_name('insert-link-symbolic' if linked else 'edit-unlink-symbolic')


def preview_surface(picture):
    picture.add_css_class('preview-surface')
    picture.set_content_fit(Gtk.ContentFit.CONTAIN)
    return picture
