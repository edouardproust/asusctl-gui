import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run
from widgets import page_title, section_title, sep, status_label, card

PROFILES = ["Quiet", "Balanced", "Performance"]


class FanTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._expert_widgets = []
        self._build()

    def _build(self):
        self.append(page_title("Fan"))
        self.append(sep())

        desc = Gtk.Label(
            label="Reset all fan curves to ASUS factory defaults. "
                  "Use this if the fans behave unexpectedly."
        )
        desc.add_css_class("dim-label")
        desc.add_css_class("caption")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        self.append(desc)

        self.append(section_title("Reset fan curves"))

        for profile in PROFILES:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text.set_hexpand(True)
            n = Gtk.Label(label=f"{profile} profile")
            n.set_halign(Gtk.Align.START)
            d = Gtk.Label(label=f"Restores the ASUS default fan curve for the {profile} profile.")
            d.add_css_class("caption")
            d.add_css_class("dim-label")
            d.set_halign(Gtk.Align.START)
            text.append(n)
            text.append(d)

            btn = Gtk.Button(label="Reset")
            btn.set_tooltip_text(
                f"Restores ASUS factory fan curve for {profile}.\n"
                "Safe to use — won't affect other profiles."
            )
            btn.connect("clicked", self._on_reset, profile)

            row.append(text)
            row.append(btn)
            self.append(card(row))

        self.status = status_label()
        self.append(self.status)

    def set_expert(self, active):
        pass

    def _on_reset(self, btn, profile):
        _, ok = run(f"asusctl fan-curve --mod-profile {profile} --default")
        self.status.set_text(
            f"{profile} fan curves reset to ASUS default." if ok else "Error resetting fan curves."
        )
