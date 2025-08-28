# Configuration handler

import os

DEFAULT_CONFIG = {
    "audio_enabled": True,
    "priority": "Normal"
}

def get_output_dir():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    output_path = os.path.join(desktop, "Rygelock_Output")
    os.makedirs(output_path, exist_ok=True)
    return output_path