import subprocess
import threading


def run(cmd, capture=True):
    if cmd.strip().startswith(("asusctl", "supergfxctl")):
        cmd = "sudo " + cmd
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, text=True, timeout=5
        )
        return result.stdout.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "timeout", False
    except Exception as e:
        return str(e), False


def run_async(cmd, callback=None):
    def target():
        out, ok = run(cmd)
        if callback:
            callback(out, ok)
    threading.Thread(target=target, daemon=True).start()