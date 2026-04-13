import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk
import sys
import os

from dashboard import DashboardTab
from battery import BatteryTab
from performance import PerformanceTab
from keyboard import KeyboardTab
from gpu import GpuTab
from fan import FanTab

TABS = [
    ("Dashboard", DashboardTab),
    ("Battery", BatteryTab),
    ("Performance", PerformanceTab),
    ("Keyboard", KeyboardTab),
    ("GPU", GpuTab),
    ("Fan", FanTab),
]


class AsusCtlApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.asus.asusctlgui")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_title("AsusCtl GUI")
        self.win.set_default_size(860, 620)

        # styles
        CSS = open("/opt/asusctl-gui/style.css", "rb").read()
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.win.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._expert = False
        self._pages = {}
        self._tab_btns = {}

        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        sidebar.set_size_request(160, -1)
        sidebar.set_hexpand(False)
        sidebar.add_css_class("sidebar")
        sidebar.set_margin_top(8)
        sidebar.set_margin_bottom(12)
        sidebar.set_margin_start(8)
        sidebar.set_margin_end(8)

        self.stack = Gtk.Stack()
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        scroll_content = Gtk.ScrolledWindow()
        scroll_content.set_hexpand(True)
        scroll_content.set_vexpand(True)
        scroll_content.set_child(self.stack)

        for name, TabClass in TABS:
            page = TabClass()
            self.stack.add_named(page, name.lower())
            self._pages[name] = page

            btn = Gtk.Button(label=name)
            btn.set_has_frame(False)
            btn.add_css_class("sidebar-btn")
            btn.set_halign(Gtk.Align.FILL)
            btn.connect("clicked", self._on_tab, name)
            self._tab_btns[name] = btn
            sidebar.append(btn)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        sidebar.append(spacer)

        sep_bottom = Gtk.Separator()
        sep_bottom.set_margin_top(8)
        sep_bottom.set_margin_bottom(8)
        sidebar.append(sep_bottom)

        exp_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        exp_lbl = Gtk.Label(label="Expert mode")
        exp_lbl.add_css_class("caption")
        exp_lbl.set_hexpand(True)
        exp_lbl.set_halign(Gtk.Align.START)
        exp_lbl.set_tooltip_text(
            "Reveals advanced options in each tab.\n"
            "Only use if you know what you're doing."
        )
        self.exp_sw = Gtk.Switch()
        self.exp_sw.set_valign(Gtk.Align.CENTER)
        self.exp_sw.connect("notify::active", self._on_expert)
        for margin in [exp_row.set_margin_start, exp_row.set_margin_end, exp_row.set_margin_bottom]:
            margin(12)
        exp_row.append(exp_lbl)
        exp_row.append(self.exp_sw)
        sidebar.append(exp_row)

        outer.append(sidebar)
        outer.append(scroll_content)

        toolbar_view.set_content(outer)
        self.win.set_content(toolbar_view)
        self.win.present()

        self._select_tab("Dashboard")

    def _select_tab(self, name):
        self.stack.set_visible_child_name(name.lower())
        for tab_name, btn in self._tab_btns.items():
            if tab_name == name:
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")

    def _on_tab(self, btn, name):
        self._select_tab(name)

    def _on_expert(self, sw, param):
        self._expert = sw.get_active()
        for page in self._pages.values():
            if hasattr(page, "set_expert"):
                page.set_expert(self._expert)


def main():
    app = AsusCtlApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()