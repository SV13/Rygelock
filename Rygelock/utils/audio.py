# utils/audio.py — patch
import os
import threading
from pygame import mixer
from utils.resource_path import resource_path

# Initialize mixer once
def init_audio():
    try:
        if not mixer.get_init():
            mixer.init()  # you can add freq/size/channels if needed
    except Exception as e:
        print("[Audio] Initialization failed:", e)

AUDIO_DIR = "assets/audio"

SOUNDS = {
    "success": "success.mp3",
    "fail":    "error.mp3",
    "progress":"progress.mp3",
    "chime":   "chime.mp3",
}

def play_sound(tag, app_config):
    def worker():
        try:
            if not app_config.get("audio_enabled", True):
                return
            if tag not in SOUNDS:
                return

            sound_path = resource_path(os.path.join(AUDIO_DIR, SOUNDS[tag]))
            if not os.path.exists(sound_path):
                print(f"[Audio] Missing file: {sound_path}")
                return

            if not mixer.get_init():
                mixer.init()

            mixer.music.load(sound_path)
            mixer.music.play()
        except Exception as e:
            print(f"[Audio] Failed to play '{tag}': {e}")
    threading.Thread(target=worker, daemon=True).start()

def stop_audio():
    try:
        mixer.music.stop()
    except Exception:
        pass
