import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from runner import run
from widgets import (
    page_title, section_title, sep, status_label, card,
    make_row, expert_banner, show_status, StatusType, confirm_dialog
)

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

NEEDS_LOGOUT = {
    ("Hybrid", "Integrated"),
    ("AsusMuxDgpu", "Integrated"),
    ("Integrated", "Hybrid"),
    ("Integrated", "AsusMuxDgpu"),
}


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
        self._current_mode = _get_mode()
        self._build()

    def _build(self):
        self.append(page_title("GPU"))

        self.notice = Gtk.Label(label="")
        self.notice.add_css_class("caption")
        self.notice.add_css_class("dim-label")
        self.notice.set_halign(Gtk.Align.START)
        self.notice.set_wrap(True)
        self.append(self.notice)

        self.append(sep())
        self.append(section_title("GPU mode"))

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

            btn.set_active(name == self._current_mode)
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

        self._dgpu_sw = Gtk.Switch()
        self._dgpu_sw.connect("notify::active", self._on_dgpu_disable)
        self._dgpu_row = make_row(
            "Disable NVIDIA GPU entirely",
            "Completely powers off the NVIDIA GPU at the BIOS level.\n"
            "Maximum battery savings. Requires a reboot to take effect.\n"
            "Cannot be used with Hybrid or AsusMuxDgpu modes.",
            self._dgpu_sw,
            subtitle="Requires reboot."
        )
        self._dgpu_row.set_visible(False)
        self.append(self._dgpu_row)

        panel_sw = Gtk.Switch()
        panel_sw.connect("notify::active", self._on_panel_overdrive)
        self._panel_row = make_row(
            "Panel overdrive",
            "Reduces display motion blur. Slightly increases display power draw.",
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
        if not btn.get_active() or name == self._current_mode:
            return

        if (self._current_mode, name) in NEEDS_LOGOUT:
            confirm_dialog(
                self,
                heading=f"Switch to {name} mode?",
                body=f"Switching from {self._current_mode} to {name} requires a logout.\n\nUnsaved work will be lost.",
                confirm_label="Log out now",
                on_confirm=lambda: self._apply_mode(name, logout=True),
                on_cancel=lambda: self._revert_mode(),
            )
        else:
            self._apply_mode(name, logout=False)

    def _revert_mode(self):
        for n, b in self._buttons.items():
            b.set_active(n == self._current_mode)

    def _apply_mode(self, name, logout=False):
        _, ok = run(f"supergfxctl --mode {name}")
        if ok:
            self._current_mode = name
            show_status(self.status, f"GPU mode set to {name}.")
            if logout:
                run("gnome-session-quit --logout --no-prompt")
        else:
            show_status(self.status, "Error setting GPU mode.", StatusType.ERROR)
            self._revert_mode()

    def _on_dgpu_disable(self, sw, param):
        val = sw.get_active()

        def apply():
            _, ok = run(f"asusctl armoury set dgpu_disable {'1' if val else '0'}")
            state = "disabled" if val else "enabled"
            if ok:
                show_status(self.exp_status, f"NVIDIA GPU {state}. Reboot to apply.")
            else:
                show_status(self.exp_status, "Error updating dGPU setting.", StatusType.ERROR)
                sw.set_active(not val)

        def revert():
            sw.set_active(not val)

        if val:
            confirm_dialog(
                self,
                heading="Disable NVIDIA GPU?",
                body="This will completely power off the NVIDIA GPU at BIOS level.\n\nA reboot is required. You can apply now and reboot later.",
                confirm_label="Reboot now",
                show_later=True,
                later_label="Apply, reboot later",
                on_confirm=lambda: (apply(), run("systemctl reboot")),
                on_later=apply,
                on_cancel=revert,
            )
        else:
            apply()

    def _on_panel_overdrive(self, sw, param):
        val = "1" if sw.get_active() else "0"
        _, ok = run(f"asusctl armoury set panel_overdrive {val}")
        state = "enabled" if sw.get_active() else "disabled"
        if ok:
            show_status(self.exp_status, f"Panel overdrive {state}.")
        else:
            show_status(self.exp_status, "Error updating panel overdrive.", StatusType.ERROR)