import subprocess
import threading


def run(cmd, capture=True):
    if cmd.strip().startswith(("asusctl", "supergfxctl")):
        cmd = "sudo " + cmd
    timeout = 60 if "fan-curve" in cmd else 5
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "timeout", False
    except Exception as e:
        return str(e), False


def run_async(cmd, callback=None):
    from gi.repository import GLib
    if cmd.strip().startswith(("asusctl", "supergfxctl")):
        cmd = "sudo " + cmd

    def target():
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            out = result.stdout.strip()
            ok = result.returncode == 0
        except subprocess.TimeoutExpired:
            out, ok = "timeout", False
        except Exception as e:
            out, ok = str(e), False
        if callback:
            GLib.idle_add(lambda: callback(out, ok) or False)

    threading.Thread(target=target, daemon=True).start()


def is_aura_supported():
    model, ok = run("cat /sys/class/dmi/id/board_name 2>/dev/null")
    if not ok or not model.strip():
        return False
    out, _ = run(f"grep '{model.strip()}' /usr/share/asusd/aura_support.ron")
    return bool(out.strip())
