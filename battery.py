import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run
from widgets import page_title, section_title, sep, status_label, make_row, card, expert_banner, show_status, StatusType


def _get_limit():
    out, _ = run("asusctl battery info")
    for line in out.splitlines():
        if "limit" in line.lower():
            try:
                return int(line.split(":")[1].strip().replace("%", ""))
            except Exception:
                pass
    return 90


class BatteryTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._expert_widgets = []
        self._build()

    def _build(self):
        self.append(page_title("Battery"))
        self.append(sep())

        self.append(section_title("Charge limit"))

        current = _get_limit()
        self._limit_val = current

        limit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 20, 100, 1)
        self.scale.set_value(current)
        self.scale.set_hexpand(True)
        self.scale.add_mark(80, Gtk.PositionType.BOTTOM, "80%")
        self.scale.add_mark(90, Gtk.PositionType.BOTTOM, "90%")
        self.scale.add_mark(100, Gtk.PositionType.BOTTOM, "100%")
        self.scale.set_tooltip_text(
            "Limits how much the battery charges.\n"
            "90% is ideal for daily use — reduces long-term battery wear.\n"
            "100% only for long trips where you need full autonomy."
        )
        self.scale.connect("value-changed", self._on_limit)

        self.limit_lbl = Gtk.Label(label=f"{current}%")
        self.limit_lbl.set_width_chars(4)

        limit_box.append(self.scale)
        limit_box.append(self.limit_lbl)
        self.append(limit_box)

        self.limit_status = status_label()
        self.append(self.limit_status)

        self.append(sep())

        self.append(section_title("One-time full charge"))

        oneshot_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        desc = Gtk.Label(
            label="Temporarily charges to 100% regardless of your limit. "
                  "Useful before a trip. The limit is restored on the next charge cycle."
        )
        desc.add_css_class("caption")
        desc.add_css_class("dim-label")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        oneshot_row.append(desc)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.oneshot_btn = Gtk.Button(label="Charge to 100% once")
        self.oneshot_btn.set_tooltip_text("Overrides the charge limit for one full charge cycle only.")
        self.oneshot_btn.connect("clicked", self._on_oneshot)

        self.oneshot_cancel_btn = Gtk.Button(label="Cancel")
        self.oneshot_cancel_btn.set_tooltip_text("Restores your normal charge limit immediately.")
        self.oneshot_cancel_btn.connect("clicked", self._on_oneshot_cancel)
        self.oneshot_cancel_btn.set_visible(False)

        btn_row.append(self.oneshot_btn)
        btn_row.append(self.oneshot_cancel_btn)
        oneshot_row.append(btn_row)

        self.oneshot_status = status_label()
        oneshot_row.append(self.oneshot_status)
        self.append(card(oneshot_row))

        self._expert_sep = sep()
        self._expert_sep.set_visible(False)
        self.append(self._expert_sep)

        self._expert_banner = expert_banner()
        self._expert_banner.set_visible(False)
        self.append(self._expert_banner)

        charge_mode_desc = (
            "Controls the BIOS-level charging strategy.\n"
            "Full capacity = charges to your set limit.\n"
            "Balanced = BIOS targets ~80% automatically.\n"
            "Best mobility = BIOS targets ~60% (very conservative)."
        )
        combo = Gtk.DropDown.new_from_strings(["Full capacity", "Balanced (~80%)", "Best mobility (~60%)"])
        combo.set_tooltip_text(charge_mode_desc)
        combo.connect("notify::selected", self._on_charge_mode)
        self._charge_mode_combo = combo

        self._expert_row = make_row(
            "BIOS charge mode",
            charge_mode_desc,
            combo,
            subtitle="Advanced BIOS-level battery strategy."
        )
        self._expert_row.set_visible(False)
        self.append(self._expert_row)

        self._expert_status = status_label()
        self._expert_status.set_visible(False)
        self.append(self._expert_status)

        self._expert_widgets = [
            self._expert_sep, self._expert_banner,
            self._expert_row, self._expert_status,
        ]

    def set_expert(self, active):
        for w in self._expert_widgets:
            w.set_visible(active)

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

    def _on_charge_mode(self, combo, param):
        vals = ["0", "1", "2"]
        val = vals[combo.get_selected()]
        _, ok = run(f"asusctl armoury set charge_mode {val}")
        if ok:
            show_status(self._expert_status, "Charge mode updated.")
        else:
            show_status(self._expert_status, "Error setting charge mode.", StatusType.ERROR)