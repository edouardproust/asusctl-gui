import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from runner import run_async
from widgets import page_title, section_title, sep, status_label, card, show_status, StatusType

PROFILES = ["Quiet", "Balanced", "Performance"]
FANS = ["cpu", "gpu"]

# Default fan curve points used by the expert editor (disabled for now)
# Format: (temperature_celsius, fan_speed_percent)
# These match the ASUS defaults read from: asusctl fan-curve --get-enabled
# CPU: 30c:1%,40c:1%,50c:5%,60c:20%,70c:34%,80c:54%,90c:80%,99c:100%
# GPU: 60c:0%,64c:2%,65c:12%,65c:21%,65c:28%,65c:28%,65c:28%,97c:100%
DEFAULT_POINTS_CPU = [
    ("30", "1"), ("40", "1"), ("50", "5"), ("60", "20"),
    ("70", "34"), ("80", "54"), ("90", "80"), ("99", "100")
]
DEFAULT_POINTS_GPU = [
    ("60", "0"), ("64", "2"), ("65", "12"), ("65", "21"),
    ("65", "28"), ("65", "28"), ("65", "28"), ("97", "100")
]


class FanTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._profile_statuses = {}
        self._build()

    def _build(self):
        self.append(page_title("Fan"))
        self.append(sep())

        desc = Gtk.Label(label="Reset fan curves to ASUS factory defaults.")
        desc.add_css_class("dim-label")
        desc.add_css_class("caption")
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        self.append(desc)

        self.append(section_title("Reset fan curves"))

        for profile in PROFILES:
            profile_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text.set_hexpand(True)

            n = Gtk.Label(label=f"{profile} profile")
            n.set_halign(Gtk.Align.START)

            d = Gtk.Label(label=f"Restores the ASUS default fan curve for all fans in {profile} mode.")
            d.add_css_class("caption")
            d.add_css_class("dim-label")
            d.set_halign(Gtk.Align.START)
            d.set_wrap(True)

            text.append(n)
            text.append(d)

            btn = Gtk.Button(label="Reset")
            # Command: asusctl fan-curve --mod-profile {profile} --default
            btn.connect("clicked", self._on_reset, profile)

            row.append(text)
            row.append(btn)
            profile_box.append(row)

            status = status_label()
            profile_box.append(status)
            self._profile_statuses[profile] = status

            self.append(card(profile_box))

        # -----------------------------------------------------------------------
        # EXPERT SECTION - disabled due to apply command hanging indefinitely
        # To re-enable: implement set_expert() to show the widgets below,
        # and restore CurveEditor class from git history or backup.
        #
        # Commands used by the expert editor:
        #
        # Enable a custom curve for a specific fan in a profile:
        #   asusctl fan-curve --mod-profile {profile} --fan {cpu|gpu} \
        #     --data "30c:1%,40c:2%,50c:5%,60c:20%,70c:35%,80c:55%,90c:80%,99c:100%" \
        #     --enable-fan-curve true
        #
        # Disable custom curve (revert to default behavior):
        #   asusctl fan-curve --mod-profile {profile} --fan {cpu|gpu} \
        #     --enable-fan-curve false
        #
        # Get current enabled status and curve data:
        #   asusctl fan-curve --get-enabled
        #
        # Note: the --data apply command was observed to hang indefinitely
        # on FX608JMR. May work on other ASUS models. Test before re-enabling.
        # -----------------------------------------------------------------------

    def set_expert(self, active):
        # Expert UI is disabled - nothing to show/hide
        pass

    def _on_reset(self, btn, profile):
        status = self._profile_statuses[profile]
        show_status(status, "Resetting...", StatusType.INFO)

        def done(out, ok):
            if ok:
                show_status(status, f"{profile} curves reset to ASUS default.")
            else:
                show_status(status, "Not supported on this model.", StatusType.ERROR)

        # Command: asusctl fan-curve --mod-profile {profile} --default
        run_async(f"asusctl fan-curve --mod-profile {profile} --default", done)