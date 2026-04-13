import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from runner import run
from widgets import page_title, section_title, sep, status_label, card, show_status, StatusType, confirm_dialog

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
        self._current_mode = _get_mode()
        self._build()

    def _build(self):
        self.append(page_title("GPU"))
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

        self.append(sep())

        dgpu_lbl = Gtk.Label(label="Current dGPU power status")
        dgpu_lbl.add_css_class("heading")
        dgpu_lbl.set_halign(Gtk.Align.START)
        self.append(dgpu_lbl)

        dgpu_status, _ = run("supergfxctl --status")
        self.dgpu_status_lbl = Gtk.Label(label=dgpu_status.strip() if dgpu_status else "?")
        self.dgpu_status_lbl.add_css_class("dim-label")
        self.dgpu_status_lbl.set_halign(Gtk.Align.START)
        self.append(self.dgpu_status_lbl)

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
