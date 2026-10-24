import ctypes
import os
import sys
import threading


def resource_path(filename):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "assets", filename)


def play_mp3(path):
    if not os.path.isfile(path):
        return
    if sys.platform == "win32":
        try:
            mci = ctypes.windll.winmm.mciSendStringW
            mci('close bombgame_sound', None, 0, 0)
            escaped = os.path.abspath(path).replace('"', '\"')
            if mci(f'open "{escaped}" type mpegvideo alias bombgame_sound', None, 0, 0) == 0:
                mci('play bombgame_sound from 0', None, 0, 0)
        except Exception:
            pass
    else:
        import shutil, subprocess
        player = shutil.which("ffplay")
        if player:
            try:
                subprocess.Popen([player, "-nodisp", "-autoexit", path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass

def play_mp3_sequence(paths):
    paths = [os.path.abspath(path) for path in paths if os.path.isfile(path)]
    if not paths:
        return

    def worker():
        if sys.platform == "win32":
            try:
                mci = ctypes.windll.winmm.mciSendStringW
                for index, path in enumerate(paths):
                    alias = f"bombgame_sequence_{index}"
                    escaped = path.replace('"', '\\"')
                    mci(f"close {alias}", None, 0, 0)
                    if mci(f'open "{escaped}" type mpegvideo alias {alias}', None, 0, 0) == 0:
                        mci(f"play {alias} wait", None, 0, 0)
                        mci(f"close {alias}", None, 0, 0)
            except Exception:
                pass
        else:
            import shutil, subprocess
            player = shutil.which("ffplay")
            if player:
                for path in paths:
                    try:
                        subprocess.run([player, "-nodisp", "-autoexit", path],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       check=False)
                    except OSError:
                        pass
    threading.Thread(target=worker, daemon=True).start()
