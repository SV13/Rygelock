# utils/audio_helper.py
import logging
from .resource_path import resource_path

try:
    import simpleaudio as sa
    _AUDIO_BACKEND = "simpleaudio"
except Exception:
    _AUDIO_BACKEND = None

def play_wav(rel_path: str) -> bool:
    try:
        full = resource_path(rel_path)
        if _AUDIO_BACKEND == "simpleaudio":
            wave_obj = sa.WaveObject.from_wave_file(full)
            wave_obj.play()
            return True
        # fallback to winsound on Windows if needed
        try:
            import winsound
            winsound.PlaySound(full, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except Exception:
            pass
    except Exception as e:
        logging.exception("Audio play failed: %s", e)
    return False
