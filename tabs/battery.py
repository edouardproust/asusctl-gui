import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run
from widgets import page_title, section_title, sep, status_label, card, show_status, StatusType

PROFILES = [
    ("Quiet", "Low noise and power. Best for battery life and everyday tasks."),
    ("Balanced", "Standard performance. Good balance between speed and battery."),
    ("Performance", "Maximum CPU/GPU performance. Higher fan noise and power draw."),
]


def _get_limit():
    out, _ = run("asusctl battery info")
    for line in out.splitlines():
        if "limit" in line.lower():
            try:
                return int(line.split(":")[1].strip().replace("%", ""))
            except Exception:
                pass
    return 90


def _get_active_profile():
    out, _ = run("asusctl profile get")
    for line in out.splitlines():
        if "Active profile:" in line:
            return line.split(":")[1].strip()
    return "Balanced"


class BatteryTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._build()

    def _build(self):
        self.append(page_title("Battery & Performance"))
        self.append(sep())

        # -- Performance profile --
        self.append(section_title("Performance profile"))

        active = _get_active_profile()
        group = None
        self._profile_buttons = {}

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
            self._profile_buttons[name] = btn

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

        self.profile_status = status_label()
        self.append(self.profile_status)

        self.append(sep())

        # -- Charge limit --
        self.append(section_title("Charge limit"))

        desc_lbl = Gtk.Label(
            label="Limits how much the battery charges. "
                  "90% is ideal for daily use and extends long-term battery life."
        )
        desc_lbl.add_css_class("caption")
        desc_lbl.add_css_class("dim-label")
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.set_wrap(True)
        self.append(desc_lbl)

        current = _get_limit()
        limit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 20, 100, 1)
        self.scale.set_value(current)
        self.scale.set_hexpand(True)
        self.scale.add_mark(80, Gtk.PositionType.BOTTOM, "80%")
        self.scale.add_mark(90, Gtk.PositionType.BOTTOM, "90%")
        self.scale.add_mark(100, Gtk.PositionType.BOTTOM, "100%")
        self.scale.connect("value-changed", self._on_limit)

        self.limit_lbl = Gtk.Label(label=f"{current}%")
        self.limit_lbl.set_width_chars(4)

        limit_box.append(self.scale)
        limit_box.append(self.limit_lbl)
        self.append(limit_box)

        self.limit_status = status_label()
        self.append(self.limit_status)

        self.append(sep())

        # -- One-time full charge --
        self.append(section_title("One-time full charge"))

        oneshot_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        oneshot_desc = Gtk.Label(
            label="Temporarily charges to 100% regardless of your limit. "
                  "Useful before a trip. The limit is restored on the next charge cycle."
        )
        oneshot_desc.add_css_class("caption")
        oneshot_desc.add_css_class("dim-label")
        oneshot_desc.set_halign(Gtk.Align.START)
        oneshot_desc.set_wrap(True)
        oneshot_box.append(oneshot_desc)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.oneshot_btn = Gtk.Button(label="Charge to 100% once")
        self.oneshot_btn.connect("clicked", self._on_oneshot)

        self.oneshot_cancel_btn = Gtk.Button(label="Cancel")
        self.oneshot_cancel_btn.set_tooltip_text("Restores your normal charge limit immediately.")
        self.oneshot_cancel_btn.connect("clicked", self._on_oneshot_cancel)
        self.oneshot_cancel_btn.set_visible(False)

        btn_row.append(self.oneshot_btn)
        btn_row.append(self.oneshot_cancel_btn)
        oneshot_box.append(btn_row)

        self.oneshot_status = status_label()
        oneshot_box.append(self.oneshot_status)
        self.append(card(oneshot_box))

    def _on_profile(self, btn, name):
        if btn.get_active():
            _, ok = run(f"asusctl profile set {name}")
            if ok:
                show_status(self.profile_status, f"Profile set to {name}")
            else:
                show_status(self.profile_status, f"Error setting {name}", StatusType.ERROR)

    def _on_limit(self, scale):
        val = int(scale.get_value())
        self.limit_lbl.set_text(f"{val}%")
        _, ok = run(f"asusctl battery limit {val}")
        if ok:
            show_status(self.limit_status, f"Limit set to {val}%")
        else:
            show_status(self.limit_status, "Error setting limit", StatusType.ERROR)

    def _on_oneshot(self, btn):
        _, ok = run("asusctl battery oneshot")
        if ok:
            show_status(self.oneshot_status, "Charging to 100% for this cycle.")
            self.oneshot_btn.set_sensitive(False)
            self.oneshot_cancel_btn.set_visible(True)
        else:
            show_status(self.oneshot_status, "Error activating one-shot charge.", StatusType.ERROR)

    def _on_oneshot_cancel(self, btn):
        val = int(self.scale.get_value())
        _, ok = run(f"asusctl battery limit {val}")
        if ok:
            show_status(self.oneshot_status, f"One-shot cancelled. Limit restored to {val}%.")
            self.oneshot_btn.set_sensitive(True)
            self.oneshot_cancel_btn.set_visible(False)
