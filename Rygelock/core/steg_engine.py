import os
import time
import hashlib
import json
import uuid
from datetime import datetime
from core.encryption import encrypt_file, decrypt_file, apply_masking, apply_demasking  # Assuming apply_masking is here
from core.algorithm import stego_apply, stego_extract, route_extraction_algorithm  # Assuming these handle file I/O or direct bytes
from core.deception_mech import prepare_fake_output  # Assuming this is correctly implemented elsewhere
from core.algorithm_stubs import LSBImageHandler
from utils.config import get_output_dir  # Assuming this returns a valid directory
from utils.file_validator import apply_data_whitening, apply_data_dewhitening  # Assuming these handle bytes
from utils.key_encoder import encode_key_metadata, decode_key_metadata, \
    generate_dict_checksum  # Assuming these are used for key file content
from cryptography.fernet import InvalidToken  # Import InvalidToken for clearer error handling
from Crypto.Protocol.KDF import HKDF, PBKDF2
from Crypto.Hash import SHA256, HMAC
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# --- Constants for Metadata/Tags ---
FAKE_TAG = b"d_dlm_!@#$&*"
REAL_TAG = b"g_dlm_!@#$&*"
METADATA_PAYLOAD_DELIMITER = b'::RYG_META_END::'

MATRYOSHKA_SALTS = [
    b'Nyck__L!M~~Ch33__Sh3n9##Dr@g0n!!',
    b'R!ckY__B0$C0~~R0dr!9u3z##Dr@g0n!!',
    b'@M5Y@R__F!qR!3--B!N__AdaM$!M_J0rmUng@ndr!!',
    b'Chr!$T!N3~~L30n9__J!@--Y3@n%%HydrA!!'
]

# --- Helper for Multi-Layer Encryption/Masking ---
def apply_multilayer_encryption(data: bytes, encryption: str, password: str, layers: int, masking: bool = False,
                                key_data: bytes = None) -> bytes:
    """
    Splits the encryption and masking processes into multiple layers for enhanced security.
    """
    data = encrypt_file(data, encryption, password, key_data=key_data)
    if masking:
        # --- Pass the password to the masking function ---
        data = apply_masking(data, password)
    return data

def get_dynamic_header(password: str) -> bytes:
    """Generates a unique 8-byte header from a password."""
    if not password:
        raise ValueError("A password is required to generate the secure dynamic header.")
    # Use a static salt to ensure the same password always produces the same header
    salt = b'rygelock_dynamic_header_salt_v1'
    return PBKDF2(password.encode('utf-8'), salt, dkLen=8, count=1000)

# --- Embedding Function ---
def embed_files(config: dict, progress_callback) -> dict:
    result = {"status": "Success", "embedded_files": [], "key_generated": False, "errors": []}
    output_dir = get_output_dir()
    try:
        # Helper function to create a secure envelope
        def create_envelope(payload_data, password, key_data, metadata_dict, is_fake=False):
            encryption_algo = "AES" if is_fake else config["encryption"]

            # 1. Primary Encryption of the payload data
            encrypted_payload = encrypt_file(payload_data, encryption_algo, password, key_data=key_data)

            # 2. Apply optional extra layers sequentially
            if not is_fake:
                extra_layers = config.get("matryoshka_layers", 0)
                if extra_layers > 0:
                    print(f"[INFO] Matryoshka enabled. Applying {extra_layers} additional encryption layers.")
                    master_key = password.encode('utf-8')
                    for i in range(extra_layers):
                        layer_salt = MATRYOSHKA_SALTS[i]
                        layer_key = HKDF(master_key, 32, salt=layer_salt, hashmod=SHA256)
                        encrypted_payload = encrypt_file(encrypted_payload, encryption_algo, "J0$hu@!ncr3m3nt@l",
                                                         key_data=layer_key)

                if config.get("masking"):
                    print("[INFO] Masking enabled.")
                    encrypted_payload = apply_masking(encrypted_payload, password)

            # 3. Create the pre-encryption block using the final, multi-layered data
            pre_encryption_block = json.dumps(metadata_dict).encode(
                'utf-8') + METADATA_PAYLOAD_DELIMITER + encrypted_payload

            # 4. Encrypt the entire block with AES-GCM to create the envelope
            envelope_master_key = password.encode('utf-8')
            envelope_salt = key_data if key_data and not is_fake else b'rygelock_default_salt'
            envelope_key = HKDF(envelope_master_key, 32, salt=envelope_salt, hashmod=SHA256)

            cipher = AES.new(envelope_key, AES.MODE_GCM)
            encrypted_envelope_data, auth_tag = cipher.encrypt_and_digest(pre_encryption_block)

            return cipher.nonce + auth_tag + encrypted_envelope_data

        # --- Main Embedding Logic ---
        real_payload_path = config["payloads"][0]
        with open(real_payload_path, "rb") as f:
            real_payload_data = f.read()

        real_key_data = None
        if config.get("generate_key"):
            payload_hash = hashlib.sha256(real_payload_data).hexdigest()
            key_meta = {"type": "genuine_key", "payload_hash": payload_hash}
            real_key_data = encode_key_metadata(key_meta)

        real_metadata = {
            "original_filename": os.path.basename(real_payload_path),
            "encryption_algorithm": config["encryption"],  # Store the user's choice
            "generate_key_used": config.get("generate_key", False),
            "matryoshka_layers": config.get("matryoshka_layers", 0),
            "masking_used": config.get("masking", False)
        }

        real_envelope = create_envelope(real_payload_data, config["password"], real_key_data, real_metadata)
        final_payload_to_embed = real_envelope

        # Prepare fake payload if needed
        if config.get("fake_payloads") and config.get("fake_password"):
            fake_payload_path = config["fake_payloads"][0]
            with open(fake_payload_path, "rb") as f:
                fake_payload_data = f.read()

            fake_metadata = {
                "original_filename": os.path.basename(fake_payload_path),
                "encryption_algorithm": "AES"  # Fakes always use AES
            }
            fake_envelope = create_envelope(fake_payload_data, config["fake_password"], None, fake_metadata,
                                            is_fake=True)
            final_payload_to_embed = FAKE_TAG + fake_envelope + REAL_TAG + real_envelope

        # 3. EMBED AND SAVE
        carrier_path = config["carriers"][0]["file"]
        algorithm = config["carriers"][0]["algorithm"]
        temp_output_name = f"stego_temp_{uuid.uuid4().hex[:6]}.tmp"
        temp_output_path = os.path.join(output_dir, temp_output_name)

        hash_before = hashlib.sha256(final_payload_to_embed).hexdigest()
        print(f"\n[DEBUG EMBED] Size of data to embed: {len(final_payload_to_embed)} bytes")
        print(f"[DEBUG EMBED] Hash of data BEFORE embedding: {hash_before}\n")

        stego_apply(carrier_path, final_payload_to_embed, algorithm, output_path=temp_output_path)

        if not os.path.exists(temp_output_path):
            raise FileNotFoundError("Stego file not created by the algorithm.")

        final_output_name = os.path.join(output_dir, os.path.basename(carrier_path))
        if os.path.exists(final_output_name):
            base, ext = os.path.splitext(final_output_name)
            final_output_name = f"{base}_embedded_{uuid.uuid4().hex[:4]}{ext}"

        os.rename(temp_output_path, final_output_name)
        result["embedded_files"].append(os.path.basename(final_output_name))

        if config.get("generate_key") and real_key_data:
            key_path = os.path.join(output_dir, "real_key.key")
            with open(key_path, "wb") as f:
                f.write(real_key_data)
            result["key_generated"] = True

        progress_callback(100)

    except Exception as e:
        result["status"] = "Failed"
        result["errors"].append(str(e))
    return result

# --- Extraction Function ---
def extract_payload(file_path: str, password: str = None, key_data: bytes = None) -> dict:
    try:
        if not password:
            raise ValueError("A password is required for extraction.")

        extraction_fn = route_extraction_algorithm(file_path)
        hidden_blob = extraction_fn(file_path, extract=True)
        if not hidden_blob:
            return {"status": "error", "message": "No hidden Rygelock data found."}

        hash_after = hashlib.sha256(hidden_blob).hexdigest()
        print(f"\n[DEBUG EXTRACT] Size of data extracted: {len(hidden_blob)} bytes")
        print(f"[DEBUG EXTRACT] Hash of data AFTER extraction: {hash_after}\n")

        # Helper function to open a secure envelope
        def open_envelope(envelope_data, pwd, key):
            # 1. Decrypt the outer envelope (AES-GCM)
            nonce, auth_tag, encrypted_data = envelope_data[:16], envelope_data[16:32], envelope_data[32:]

            master_key = pwd.encode('utf-8')
            salt = key if key else b'rygelock_default_salt'
            decryption_key = HKDF(master_key, 32, salt=salt, hashmod=SHA256)

            cipher = AES.new(decryption_key, AES.MODE_GCM, nonce=nonce)
            decrypted_block = cipher.decrypt_and_verify(encrypted_data, auth_tag)

            # 2. Split the decrypted block into metadata and the inner payload
            metadata_json, inner_payload = decrypted_block.split(METADATA_PAYLOAD_DELIMITER, 1)
            metadata = json.loads(metadata_json.decode('utf-8'))

            encryption_algo = metadata.get("encryption_algorithm", "AES")  # Get the user's original choice

            # 3. Peel back the optional security layers from the inner payload

            # Layer 3: Demasking
            if metadata.get("masking_used"):
                inner_payload = apply_demasking(inner_payload, pwd)

            # Layer 2: Matryoshka
            extra_layers = metadata.get("matryoshka_layers", 0)
            if extra_layers > 0:
                master_key_matryoshka = pwd.encode('utf-8')
                # Decrypt in the exact REVERSE order
                for i in reversed(range(extra_layers)):
                    layer_salt = MATRYOSHKA_SALTS[i]
                    layer_key = HKDF(master_key_matryoshka, 32, salt=layer_salt, hashmod=SHA256)
                    #Use the correct algorithm variable
                    inner_payload = decrypt_file(inner_payload, "J0$hu@!ncr3m3nt@l", encryption_algo,
                                                 key_data=layer_key)


            # Layer 1: Final, Primary Decryption
            final_payload = decrypt_file(inner_payload, pwd, encryption_algo, key_data=key)

            # 4. Authenticate the key against the final plaintext payload
            if metadata.get("generate_key_used"):
                if not key: raise ValueError("Key file required but not provided.")
                key_meta = decode_key_metadata(key)
                stored_hash = key_meta.get("payload_hash")
                current_hash = hashlib.sha256(final_payload).hexdigest()
                if stored_hash != current_hash: raise ValueError("Key does not match payload.")

            return final_payload, metadata

        # --- Main Extraction Logic ---
        is_combined = FAKE_TAG in hidden_blob and REAL_TAG in hidden_blob
        if is_combined:
            _, parts = hidden_blob.split(FAKE_TAG, 1)
            fake_envelope, real_envelope = parts.split(REAL_TAG, 1)

            # Attempt 1: Try to open the FAKE envelope
            try:
                decrypted_data, metadata = open_envelope(fake_envelope, password, None)
                print("[INFO] Fake password accepted. Extracting decoy payload.")
                output_dir = get_output_dir()
                out_path = os.path.join(output_dir, metadata["original_filename"])
                with open(out_path, "wb") as f:
                    f.write(decrypted_data)
                return {"status": "success", "output_file": out_path, "metadata": metadata}
            except Exception:
                pass

            # Attempt 2: Try to open the REAL envelope
            try:
                decrypted_data, metadata = open_envelope(real_envelope, password, key_data)
                print("[INFO] Real password/key accepted. Extracting genuine payload.")
                output_dir = get_output_dir()
                out_path = os.path.join(output_dir, metadata["original_filename"])
                with open(out_path, "wb") as f:
                    f.write(decrypted_data)
                return {"status": "success", "output_file": out_path, "metadata": metadata}
            except Exception as e:
                return {"status": "error", "message": f"Incorrect password or key. Details: {e}"}

        else:  # It's a single, real payload
            try:
                decrypted_data, metadata = open_envelope(hidden_blob, password, key_data)
                output_dir = get_output_dir()
                out_path = os.path.join(output_dir, metadata["original_filename"])
                with open(out_path, "wb") as f:
                    f.write(decrypted_data)
                return {"status": "success", "output_file": out_path, "metadata": metadata}
            except Exception as e:
                return {"status": "error", "message": f"Incorrect password or key. Details: {e}"}

        return {"status": "error", "message": "Incorrect password or corrupted data."}

    except Exception as e:
        return {"status": "error", "message": f"Extraction failed. Incorrect password or key. Details: {e}"}

