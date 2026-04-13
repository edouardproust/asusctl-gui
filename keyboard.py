import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run, is_aura_supported
from widgets import page_title, section_title, sep, status_label, make_row, expert_banner, show_status, StatusType

LEVELS = ["off", "low", "med", "high"]
LEVEL_LABELS = {"off": "Off", "low": "Low", "med": "Medium", "high": "High"}

AURA_SUPPORTED = is_aura_supported()


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
        self._expert_widgets = []
        self._build()

    def _build(self):
        self.append(page_title("Keyboard"))
        self.append(sep())
        self.append(section_title("Backlight brightness"))

        active = _get_brightness()
        group = None
        self._bright_btns = {}

        bright_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bright_box.set_tooltip_text("Controls keyboard backlight intensity.")
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

        # -- EXPERT --
        self._exp_sep = sep()
        self._exp_sep.set_visible(False)
        self.append(self._exp_sep)

        self._exp_banner = expert_banner()
        self._exp_banner.set_visible(False)
        self.append(self._exp_banner)

        self._exp_title = section_title("LED behavior")
        self._exp_title.set_visible(False)
        self.append(self._exp_title)

        self._aura_rows = []
        self._aura_switches = {}

        if not AURA_SUPPORTED:
            not_supported = status_label(StatusType.ERROR)
            not_supported.set_text("Not supported on this laptop model (aura power-tuf).")
            not_supported.set_visible(False)
            self.append(not_supported)
            self._aura_rows.append(not_supported)
        else:
            aura_options = [
                ("awake", "keyboard", "LEDs on while awake", "Turn keyboard backlight on during normal use."),
                ("boot", None, "Boot animation", "Show an LED animation during system startup."),
                ("sleep", None, "Sleep animation", "Show an LED animation while in suspend mode."),
            ]
            for key, sub_flag, label, tooltip in aura_options:
                sw = Gtk.Switch()
                sw.set_active(True)
                sw.connect("notify::active", self._on_aura, key, sub_flag)
                self._aura_switches[key] = sw
                row = make_row(label, tooltip, sw)
                row.set_visible(False)
                self.append(row)
                self._aura_rows.append(row)

        self.aura_status = status_label()
        self.aura_status.set_visible(False)
        self.append(self.aura_status)

        self._expert_widgets = (
            [self._exp_sep, self._exp_banner, self._exp_title, self.aura_status]
            + self._aura_rows
        )

    def set_expert(self, active):
        for w in self._expert_widgets:
            w.set_visible(active)

    def _on_brightness(self, btn, lvl):
        if btn.get_active():
            _, ok = run(f"asusctl leds set {lvl}")
            if ok:
                show_status(self.bright_status, f"Brightness set to {LEVEL_LABELS[lvl]}")
            else:
                show_status(self.bright_status, "Error setting brightness", StatusType.ERROR)

    def _on_aura(self, sw, param, key, sub_flag):
        val = "true" if sw.get_active() else "false"
        if sub_flag:
            cmd = f"asusctl aura power-tuf --{key.split('_')[0]} {val} --{sub_flag}"
        else:
            cmd = f"asusctl aura power-tuf --{key} {val}"
        _, ok = run(cmd)
        if ok:
            show_status(self.aura_status, "LED setting updated")
        else:
            show_status(self.aura_status, "Error updating LED setting", StatusType.ERROR)