import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run
from widgets import page_title, section_title, sep, status_label, card, expert_banner, make_row, show_status, StatusType

PROFILES = [
    ("Quiet", "Low noise and power. Best for battery life and everyday tasks."),
    ("Balanced", "Standard performance. Good balance between speed and battery."),
    ("Performance", "Maximum CPU/GPU performance. Higher fan noise and power draw."),
]
FANS = ["cpu", "gpu"]


def _get_active():
    out, _ = run("asusctl profile get")
    for line in out.splitlines():
        if "Active profile:" in line:
            return line.split(":")[1].strip()
    return "Balanced"


class PerformanceTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._expert_widgets = []
        self._build()

    def _build(self):
        self.append(page_title("Performance"))
        self.append(sep())
        self.append(section_title("Profile"))

        active = _get_active()
        group = None
        self._buttons = {}

        for name, desc in PROFILES:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.set_margin_top(2)
            row.set_margin_bottom(2)

            if group is None:
                btn = Gtk.CheckButton()
                group = btn
            else:
                btn = Gtk.CheckButton()
                btn.set_group(group)

            btn.set_active(name == active)
            btn.connect("toggled", self._on_profile, name)
            self._buttons[name] = btn

            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text.set_hexpand(True)
            n = Gtk.Label(label=name)
            n.set_halign(Gtk.Align.START)
            d = Gtk.Label(label=desc)
            d.add_css_class("caption")
            d.add_css_class("dim-label")
            d.set_halign(Gtk.Align.START)
            d.set_wrap(True)
            text.append(n)
            text.append(d)

            row.append(btn)
            row.append(text)
            self.append(card(row))

        self.status = status_label()
        self.append(self.status)

        self._exp_sep = sep()
        self._exp_sep.set_visible(False)
        self.append(self._exp_sep)

        self._exp_banner = expert_banner()
        self._exp_banner.set_visible(False)
        self.append(self._exp_banner)

        self._exp_fan_title = section_title("Fan curves per profile")
        self._exp_fan_title.set_visible(False)
        self.append(self._exp_fan_title)

        self._exp_fan_desc = Gtk.Label(
            label="Enable or disable custom fan curves for each profile and fan."
        )
        self._exp_fan_desc.add_css_class("caption")
        self._exp_fan_desc.add_css_class("dim-label")
        self._exp_fan_desc.set_halign(Gtk.Align.START)
        self._exp_fan_desc.set_wrap(True)
        self._exp_fan_desc.set_visible(False)
        self.append(self._exp_fan_desc)

        self._fan_rows = []
        for profile_name, _ in PROFILES:
            for fan in FANS:
                sw = Gtk.Switch()
                sw.connect("notify::active", self._on_fan_toggle, profile_name, fan)
                row = make_row(
                    f"{profile_name} — {fan.upper()} fan curve",
                    f"Enable a custom fan curve for the {fan.upper()} fan in {profile_name} mode.",
                    sw,
                )
                row.set_visible(False)
                self.append(row)
                self._fan_rows.append(row)

        self._exp_reset_title = section_title("Reset fan curves")
        self._exp_reset_title.set_visible(False)
        self.append(self._exp_reset_title)

        self._reset_rows = []
        for profile_name, _ in PROFILES:
            btn = Gtk.Button(label=f"Reset {profile_name} to ASUS default")
            btn.set_halign(Gtk.Align.START)
            btn.set_tooltip_text(f"Restores the original ASUS fan curve for the {profile_name} profile.")
            btn.connect("clicked", self._on_reset, profile_name)
            btn.set_visible(False)
            self.append(btn)
            self._reset_rows.append(btn)

        self.fan_status = status_label()
        self.fan_status.set_visible(False)
        self.append(self.fan_status)

        self._expert_widgets = (
            [self._exp_sep, self._exp_banner, self._exp_fan_title, self._exp_fan_desc,
             self._exp_reset_title, self.fan_status]
            + self._fan_rows + self._reset_rows
        )

    def set_expert(self, active):
        for w in self._expert_widgets:
            w.set_visible(active)

    def _on_profile(self, btn, name):
        if btn.get_active():
            _, ok = run(f"asusctl profile set {name}")
            if ok:
                show_status(self.status, f"Profile set to {name}")
            else:
                show_status(self.status, f"Error setting {name}", StatusType.ERROR)

    def _on_fan_toggle(self, sw, param, profile, fan):
        val = "true" if sw.get_active() else "false"
        cmd = f"asusctl fan-curve --mod-profile {profile} --enable-fan-curve {val} --fan {fan}"
        _, ok = run(cmd)
        state = "enabled" if sw.get_active() else "disabled"
        if ok:
            show_status(self.fan_status, f"{profile} {fan.upper()} curve {state}")
        else:
            show_status(self.fan_status, "Error updating fan curve", StatusType.ERROR)

    def _on_reset(self, btn, profile):
        _, ok = run(f"asusctl fan-curve --mod-profile {profile} --default")
        if ok:
            show_status(self.fan_status, f"{profile} fan curves reset to default")
        else:
            show_status(self.fan_status, "Error resetting fan curves", StatusType.ERROR)