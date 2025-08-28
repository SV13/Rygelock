import os
import uuid
from datetime import datetime
from utils.key_encoder import encode_key_metadata


def prepare_fake_output(config):
    """
    Handles creation of fake payload files and a fake key, based on user deception settings.

    Args:
        config (dict): Configuration dictionary from embed_widget containing:
            - fake_payloads (List[bytes])
            - generate_fake_key (bool)
            - fake_password (str)
            - output_dir (str)

    Updates config with:
        - fake_output_paths (List[str])
        - fake_key_path (str), if applicable
    """
    output_dir = config.get("output_dir", os.getcwd())
    os.makedirs(output_dir, exist_ok=True)

    fake_output_paths = []
    fake_payloads = config.get("fake_payloads", [])

    for i, data in enumerate(fake_payloads):
        if not isinstance(data, bytes):
            continue  # skip invalid data

        filename = f"fake_payload_{i+1}_{uuid.uuid4().hex[:5]}.bin"
        filepath = os.path.join(output_dir, filename)

        try:
            with open(filepath, "wb") as f:
                f.write(data)
            fake_output_paths.append(filepath)
        except Exception as e:
            print(f"[!] Failed to write fake payload: {filepath} - {e}")

    config["fake_output_paths"] = fake_output_paths

    # Secure fake key generation
    if config.get("generate_fake_key", False):
        key_filename = f"fake_key_{uuid.uuid4().hex[:6]}.key"
        key_path = os.path.join(output_dir, key_filename)

        try:
            carrier_names = "_".join([os.path.basename(c["file"]) for c in config["carriers"]])
            timestamp = datetime.now().isoformat()

            metadata = {
                "type": "fake",
                "version": "RYG-1.0",
                "binding": carrier_names,
                "timestamp": timestamp,
                "fake_password": config.get("fake_password", "None")
            }

            encoded = encode_key_metadata(metadata)

            with open(key_path, "w") as f:
                f.write(encoded)

            config["fake_key_path"] = key_path

        except Exception as e:
            print(f"[!] Failed to write fake key: {key_path} - {e}")
