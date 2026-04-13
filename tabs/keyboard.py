import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run
from widgets import page_title, section_title, sep, status_label, show_status, StatusType

LEVELS = ["off", "low", "med", "high"]
LEVEL_LABELS = {"off": "Off", "low": "Low", "med": "Medium", "high": "High"}


def _get_brightness():
    out, _ = run("asusctl leds get")
    for lvl in LEVELS:
        if lvl in out.lower():
            return lvl
    return "med"


class KeyboardTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._build()

    def _build(self):
        self.append(page_title("Keyboard"))
        self.append(sep())
        self.append(section_title("Backlight brightness"))

        desc = Gtk.Label(label="Controls how bright the keyboard backlight is. 'Off' saves battery.")
        desc.add_css_class("caption")
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        self.append(desc)

        active = _get_brightness()
        group = None
        self._bright_btns = {}

        bright_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bright_box.set_margin_top(6)
        for lvl in LEVELS:
            if group is None:
                btn = Gtk.CheckButton(label=LEVEL_LABELS[lvl])
                group = btn
            else:
                btn = Gtk.CheckButton(label=LEVEL_LABELS[lvl])
                btn.set_group(group)
            btn.set_active(lvl == active)
            btn.connect("toggled", self._on_brightness, lvl)
            self._bright_btns[lvl] = btn
            bright_box.append(btn)

        self.append(bright_box)

        self.bright_status = status_label()
        self.append(self.bright_status)

    def _on_brightness(self, btn, lvl):
        if btn.get_active():
            _, ok = run(f"asusctl leds set {lvl}")
            if ok:
                show_status(self.bright_status, f"Brightness set to {LEVEL_LABELS[lvl]}")
            else:
                show_status(self.bright_status, "Error setting brightness", StatusType.ERROR)
