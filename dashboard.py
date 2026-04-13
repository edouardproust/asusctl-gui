import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk
from runner import run
from widgets import page_title, sep, section_title


def _get_sensors():
    out, _ = run("sensors")
    data = {"CPU": "?", "CPU Fan": "?", "GPU Fan": "?", "NVMe": "?"}
    in_nvme = False
    for line in out.splitlines():
        if "nvme" in line.lower():
            in_nvme = True
        if "asus-isa" in line.lower():
            in_nvme = False
        if "Package id 0:" in line:
            try:
                data["CPU"] = "+" + line.split("+")[1].split("°")[0] + "°C"
            except Exception:
                pass
        if "cpu_fan:" in line:
            try:
                data["CPU Fan"] = line.split(":")[1].strip()
            except Exception:
                pass
        if "gpu_fan:" in line:
            try:
                data["GPU Fan"] = line.split(":")[1].strip()
            except Exception:
                pass
        if in_nvme and "Composite:" in line:
            try:
                data["NVMe"] = "+" + line.split("+")[1].split("°")[0] + "°C"
            except Exception:
                pass
    return data


def _get_battery():
    cap, _ = run("cat /sys/class/power_supply/BAT0/capacity")
    status, _ = run("cat /sys/class/power_supply/BAT0/status")
    power, _ = run("cat /sys/class/power_supply/BAT0/power_now")
    limit_out, _ = run("asusctl battery info")
    limit = "?"
    for line in limit_out.splitlines():
        if "limit" in line.lower():
            try:
                limit = line.split(":")[1].strip()
            except Exception:
                pass
    try:
        watts = f"{round(int(power.strip()) / 1_000_000, 1)}W"
    except Exception:
        watts = "?"
    return {
        "Charge": f"{cap.strip()}%" if cap else "?",
        "Status": status.strip() if status else "?",
        "Power draw": watts,
        "Charge limit": limit,
    }


def _get_gpu():
    mode, _ = run("supergfxctl --get")
    status, _ = run("supergfxctl --status")
    nv, _ = run("nvidia-smi --query-gpu=temperature.gpu,power.draw --format=csv,noheader,nounits 2>/dev/null")
    gpu_temp, gpu_pwr = "?", "?"
    if nv:
        parts = nv.split(",")
        if len(parts) >= 2:
            try:
                gpu_temp = parts[0].strip() + "°C"
                gpu_pwr = parts[1].strip() + "W"
            except Exception:
                pass
    return {
        "Mode": mode.strip() if mode else "?",
        "dGPU status": status.strip() if status else "?",
        "GPU temp": gpu_temp,
        "GPU power": gpu_pwr,
    }


def _get_profile():
    out, _ = run("asusctl profile get")
    for line in out.splitlines():
        if "Active profile:" in line:
            return line.split(":")[1].strip()
    return "?"


def _get_system_info():
    os_name, _ = run("grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"'")
    kernel, _ = run("uname -r")
    laptop, _ = run("cat /sys/class/dmi/id/product_name 2>/dev/null")
    laptop_ver, _ = run("cat /sys/class/dmi/id/product_version 2>/dev/null")
    cpu, _ = run("grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2")
    ram_kb, _ = run("grep MemTotal /proc/meminfo | awk '{print $2}'")
    gpu_model, _ = run("lspci | grep -i nvidia | grep VGA | sed 's/.*: //'")
    nvidia_driver, _ = run("nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null")
    asusctl_ver, _ = run("rpm -q asusctl --queryformat '%{VERSION}'")
    supergfx_ver, _ = run("supergfxctl --version 2>/dev/null")

    try:
        ram_gb = str(round(int(ram_kb.strip()) / 1_048_576, 1)) + " GB"
    except Exception:
        ram_gb = "?"

    laptop_full = laptop.strip() if laptop else "?"

    return {
        "OS": os_name.strip() if os_name else "?",
        "Kernel": kernel.strip() if kernel else "?",
        "Laptop": laptop_full,
        "CPU": cpu.strip() if cpu else "?",
        "RAM": ram_gb,
        "GPU": gpu_model.strip() if gpu_model else "?",
        "NVIDIA driver": nvidia_driver.strip() if nvidia_driver else "?",
        "asusctl / asusd": asusctl_ver.strip() if asusctl_ver else "?",
        "supergfxctl": supergfx_ver.strip() if supergfx_ver else "?",
    }


def _stat_card(label, value):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    box.set_margin_top(10)
    box.set_margin_bottom(10)
    box.set_margin_start(14)
    box.set_margin_end(14)

    lbl = Gtk.Label(label=label)
    lbl.add_css_class("caption")
    lbl.add_css_class("dim-label")
    lbl.set_halign(Gtk.Align.START)

    val = Gtk.Label(label=value)
    val.add_css_class("title-3")
    val.set_halign(Gtk.Align.START)
    val.set_wrap(True)
    val.set_max_width_chars(20)

    box.append(lbl)
    box.append(val)

    frame = Gtk.Frame()
    frame.set_child(box)
    frame.set_hexpand(True)
    return frame, val


def _info_row(label, value):
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    row.set_margin_top(3)
    row.set_margin_bottom(3)

    lbl = Gtk.Label(label=label)
    lbl.add_css_class("dim-label")
    lbl.add_css_class("caption")
    lbl.set_size_request(120, -1)
    lbl.set_halign(Gtk.Align.START)

    val = Gtk.Label(label=value)
    val.set_halign(Gtk.Align.START)
    val.set_wrap(True)
    val.set_hexpand(True)
    val.add_css_class("caption")

    row.append(lbl)
    row.append(val)
    return row, val


class DashboardTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self._cards = {}
        self._info_vals = {}
        self._current_data = {}
        self._build()
        GLib.timeout_add_seconds(3, self._refresh)

    def _grid_section(self, title_text, keys):
        self.append(section_title(title_text))
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(8)
        grid.set_column_homogeneous(True)
        for i, key in enumerate(keys):
            frame, val = _stat_card(key, "…")
            grid.attach(frame, i, 0, 1, 1)
            self._cards[key] = val
        self.append(grid)

    def _build(self):
        # Title row with copy button
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_row.set_hexpand(True)

        title = page_title("Dashboard")
        title.set_hexpand(True)
        title_row.append(title)

        copy_btn = Gtk.Button(label="Copy system info")
        copy_btn.set_tooltip_text(
            "Copies all system information to clipboard as structured text.\n"
            "Useful for sharing with support or forums."
        )
        copy_btn.set_valign(Gtk.Align.CENTER)
        copy_btn.connect("clicked", self._on_copy)
        title_row.append(copy_btn)

        self.append(title_row)

        self.profile_lbl = Gtk.Label(label="")
        self.profile_lbl.add_css_class("dim-label")
        self.profile_lbl.set_halign(Gtk.Align.START)
        self.append(self.profile_lbl)

        self.copy_status = Gtk.Label(label="")
        self.copy_status.add_css_class("caption")
        self.copy_status.add_css_class("dim-label")
        self.copy_status.set_halign(Gtk.Align.START)
        self.append(self.copy_status)

        self.append(sep())

        # System info section - collapsed by default
        expander = Gtk.Expander(label="  System info")
        expander.set_expanded(False)
        expander.add_css_class("heading")

        sysinfo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sysinfo_box.set_margin_top(8)
        sysinfo_box.set_margin_bottom(8)
        sysinfo_box.set_margin_start(12)
        sysinfo_box.set_margin_end(12)

        sysinfo_keys = [
            ("OS", "Operating system"),
            ("Kernel", "Linux kernel version"),
            ("Laptop", "Laptop model"),
            ("CPU", "Processor"),
            ("RAM", "Total RAM"),
            ("GPU", "NVIDIA GPU model"),
            ("NVIDIA driver", "NVIDIA driver version"),
            ("asusctl / asusd", "asusctl and asusd version"),
            ("supergfxctl", "supergfxctl version"),
        ]

        for key, _ in sysinfo_keys:
            row, val = _info_row(key, "…")
            sysinfo_box.append(row)
            self._info_vals[key] = val

        expander.set_child(sysinfo_box)
        self.append(expander)

        self.append(sep())
        self._grid_section("Temperatures & fans", ["CPU", "CPU Fan", "GPU Fan", "NVMe"])
        self.append(sep())
        self._grid_section("Battery", ["Charge", "Status", "Power draw", "Charge limit"])
        self.append(sep())
        self._grid_section("GPU", ["Mode", "dGPU status", "GPU temp", "GPU power"])
        self._refresh()

    def _refresh(self):
        sensors = _get_sensors()
        bat = _get_battery()
        gpu = _get_gpu()
        sysinfo = _get_system_info()
        profile = _get_profile()

        self._current_data = {
            "sensors": sensors,
            "battery": bat,
            "gpu": gpu,
            "sysinfo": sysinfo,
            "profile": profile,
        }

        all_data = {**sensors, **bat, **gpu}
        for key, val_lbl in self._cards.items():
            val_lbl.set_text(all_data.get(key, "?"))

        for key, val_lbl in self._info_vals.items():
            val_lbl.set_text(sysinfo.get(key, "?"))

        self.profile_lbl.set_text(f"Active profile: {profile}")
        return True

    def _on_copy(self, btn):
        d = self._current_data
        if not d:
            return

        si = d.get("sysinfo", {})
        lines = [
            "=== AsusCtl GUI - System Info ===",
            "",
            "[ System ]",
            f"  OS            : {si.get('OS', '?')}",
            f"  Kernel        : {si.get('Kernel', '?')}",
            f"  Laptop        : {si.get('Laptop', '?')}",
            f"  CPU           : {si.get('CPU', '?')}",
            f"  RAM           : {si.get('RAM', '?')}",
            f"  GPU           : {si.get('GPU', '?')}",
            f"  NVIDIA driver : {si.get('NVIDIA driver', '?')}",
            f"  asusctl/asusd : {si.get('asusctl / asusd', '?')}",
            f"  supergfxctl   : {si.get('supergfxctl', '?')}",
            f"  Profile       : {d.get('profile', '?')}",
            "",
            "[ Temperatures & Fans ]",
            f"  CPU temp : {d['sensors'].get('CPU', '?')}",
            f"  NVMe     : {d['sensors'].get('NVMe', '?')}",
            f"  CPU fan  : {d['sensors'].get('CPU Fan', '?')}",
            f"  GPU fan  : {d['sensors'].get('GPU Fan', '?')}",
            "",
            "[ Battery ]",
            f"  Charge       : {d['battery'].get('Charge', '?')}",
            f"  Status       : {d['battery'].get('Status', '?')}",
            f"  Power draw   : {d['battery'].get('Power draw', '?')}",
            f"  Charge limit : {d['battery'].get('Charge limit', '?')}",
            "",
            "[ GPU ]",
            f"  Mode        : {d['gpu'].get('Mode', '?')}",
            f"  dGPU status : {d['gpu'].get('dGPU status', '?')}",
            f"  GPU temp    : {d['gpu'].get('GPU temp', '?')}",
            f"  GPU power   : {d['gpu'].get('GPU power', '?')}",
            "",
            "==================================",
        ]

        text = "\n".join(lines)
        clipboard = self.get_clipboard()
        clipboard.set(text)
        self.copy_status.set_text("System info copied to clipboard.")
        GLib.timeout_add_seconds(3, lambda: self.copy_status.set_text("") or False)