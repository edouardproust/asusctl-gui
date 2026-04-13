import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run
from widgets import page_title, section_title, sep, status_label, card, make_row, expert_banner

GPU_MODES = [
    (
        "Integrated",
        "Only the Intel GPU is active. Best battery life.\nThe NVIDIA GPU is completely off.",
        "Best for battery — use when you don't need 3D graphics or gaming."
    ),
    (
        "Hybrid",
        "Intel GPU drives the screen. NVIDIA available on demand.\nRecommended for everyday use.",
        "Recommended — balances battery and performance. Games and 3D apps use NVIDIA automatically."
    ),
    (
        "AsusMuxDgpu",
        "NVIDIA GPU drives the screen directly.\nHighest performance, highest power draw.",
        "Use for gaming sessions or GPU-intensive tasks. Significantly reduces battery life."
    ),
]


def _get_mode():
    out, _ = run("supergfxctl --get")
    return out.strip() if out else "Hybrid"


class GpuTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._expert_widgets = []
        self._build()

    def _build(self):
        self.append(page_title("GPU"))

        notice = Gtk.Label(label="Changing GPU mode requires logging out to take effect.")
        notice.add_css_class("caption")
        notice.add_css_class("dim-label")
        notice.set_halign(Gtk.Align.START)
        notice.set_wrap(True)
        self.append(notice)
        self.append(sep())
        self.append(section_title("GPU mode"))

        active = _get_mode()
        group = None
        self._buttons = {}

        for name, desc, tooltip in GPU_MODES:
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
            btn.connect("toggled", self._on_mode, name)
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

            info = Gtk.Button(label="ℹ")
            info.set_has_frame(False)
            info.set_tooltip_text(tooltip)
            info.set_valign(Gtk.Align.CENTER)

            row.append(btn)
            row.append(text)
            row.append(info)
            self.append(card(row))

        self.status = status_label()
        self.append(self.status)

        # -- EXPERT --
        self._exp_sep = sep()
        self._exp_sep.set_visible(False)
        self.append(self._exp_sep)

        self._exp_banner = expert_banner()
        self._exp_banner.set_visible(False)
        self.append(self._exp_banner)

        dgpu_sw = Gtk.Switch()
        dgpu_sw.connect("notify::active", self._on_dgpu_disable)
        self._dgpu_row = make_row(
            "Disable NVIDIA GPU entirely",
            "Completely powers off the NVIDIA GPU at the BIOS level.\n"
            "Maximum battery savings. Requires a reboot to take effect.\n"
            "Only use if you never need NVIDIA — reverts the GPU mode setting.",
            dgpu_sw,
            subtitle="Requires reboot. Cannot be used with Hybrid or AsusMuxDgpu modes."
        )
        self._dgpu_row.set_visible(False)
        self.append(self._dgpu_row)

        panel_sw = Gtk.Switch()
        panel_sw.connect("notify::active", self._on_panel_overdrive)
        self._panel_row = make_row(
            "Panel overdrive",
            "Reduces display motion blur by overdriving pixel transitions.\n"
            "Makes fast motion cleaner on screen. Slightly increases display power draw.\n"
            "No visual downside for normal use.",
            panel_sw,
            subtitle="Cosmetic display improvement. Safe to enable."
        )
        self._panel_row.set_visible(False)
        self.append(self._panel_row)

        self.exp_status = status_label()
        self.exp_status.set_visible(False)
        self.append(self.exp_status)

        self._expert_widgets = [
            self._exp_sep, self._exp_banner,
            self._dgpu_row, self._panel_row, self.exp_status
        ]

    def set_expert(self, active):
        for w in self._expert_widgets:
            w.set_visible(active)

    def _on_mode(self, btn, name):
        if btn.get_active():
            _, ok = run(f"supergfxctl --mode {name}")
            self.status.set_text(
                f"GPU mode set to {name}. Log out to apply." if ok else "Error setting GPU mode"
            )

    def _on_dgpu_disable(self, sw, param):
        val = "1" if sw.get_active() else "0"
        _, ok = run(f"asusctl armoury set dgpu_disable {val}")
        state = "disabled" if sw.get_active() else "enabled"
        self.exp_status.set_text(
            f"NVIDIA GPU {state}. Reboot to apply." if ok else "Error updating dGPU setting"
        )

    def _on_panel_overdrive(self, sw, param):
        val = "1" if sw.get_active() else "0"
        _, ok = run(f"asusctl armoury set panel_overdrive {val}")
        state = "enabled" if sw.get_active() else "disabled"
        self.exp_status.set_text(
            f"Panel overdrive {state}." if ok else "Error updating panel overdrive"
        )
