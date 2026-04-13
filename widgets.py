import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from enum import Enum
from typing import Optional

class StatusType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    INFO = "dim-label"

def status_label(status_type: Optional[StatusType] = None) -> Gtk.Label:
    lbl = Gtk.Label(label="")
    lbl.add_css_class("caption")
    lbl.set_halign(Gtk.Align.START)
    if status_type:
        lbl.add_css_class(status_type.value)
    return lbl

def show_status(lbl: Gtk.Label, message: str, status: StatusType = StatusType.SUCCESS) -> None:
    lbl.set_text(message)
    for s in StatusType:
        lbl.remove_css_class(s.value)
    lbl.add_css_class(status.value)

def section_title(text):
    lbl = Gtk.Label(label=text)
    lbl.add_css_class("heading")
    lbl.set_halign(Gtk.Align.START)
    lbl.set_margin_top(8)
    return lbl


def page_title(text):
    lbl = Gtk.Label(label=text)
    lbl.add_css_class("title-1")
    lbl.set_halign(Gtk.Align.START)
    return lbl


def dim_label(text):
    lbl = Gtk.Label(label=text)
    lbl.add_css_class("dim-label")
    lbl.add_css_class("caption")
    lbl.set_halign(Gtk.Align.START)
    lbl.set_wrap(True)
    return lbl


def make_row(label_text, tooltip, control, subtitle=None):
    """A settings row with label, optional subtitle, tooltip icon, and a control widget."""
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    outer.set_margin_top(2)
    outer.set_margin_bottom(2)
    outer.set_margin_start(4)
    outer.set_margin_end(4)

    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

    text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    text_box.set_hexpand(True)

    lbl_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    lbl = Gtk.Label(label=label_text)
    lbl.set_halign(Gtk.Align.START)
    lbl_row.append(lbl)

    if tooltip:
        info = Gtk.Button(label="ℹ")
        info.set_has_frame(False)
        info.set_tooltip_text(tooltip)
        info.set_size_request(20, 20)
        info.add_css_class("flat")
        lbl_row.append(info)

    text_box.append(lbl_row)

    if subtitle:
        sub = Gtk.Label(label=subtitle)
        sub.add_css_class("caption")
        sub.add_css_class("dim-label")
        sub.set_halign(Gtk.Align.START)
        sub.set_wrap(True)
        text_box.append(sub)

    row.append(text_box)
    if control:
        control.set_valign(Gtk.Align.CENTER)
        row.append(control)

    outer.append(row)
    return outer


def card(child):
    frame = Gtk.Frame()
    frame.set_margin_top(4)
    frame.set_margin_bottom(4)
    inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    inner.set_margin_top(8)
    inner.set_margin_bottom(8)
    inner.set_margin_start(12)
    inner.set_margin_end(12)
    inner.append(child)
    frame.set_child(inner)
    return frame


def sep():
    s = Gtk.Separator()
    s.set_margin_top(8)
    s.set_margin_bottom(8)
    return s


def expert_banner():
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    box.set_margin_top(4)
    box.set_margin_bottom(4)
    box.set_margin_start(4)
    box.set_margin_end(4)
    lbl = Gtk.Label(label="⚙  Expert options")
    lbl.add_css_class("heading")
    lbl.set_halign(Gtk.Align.START)
    box.append(lbl)
    return box
