from Crypto.Cipher import AES, Blowfish
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import ChaCha20
from cryptography.fernet import Fernet, InvalidToken
import base64
import hashlib
import os

BLOCK_SIZE_AES = 16
BLOCK_SIZE_BLOWFISH = 8
PBKDF2_ITER = 100_000
SALT_SIZE = 16 # For salts prepended to ciphertext)

# --- Helper function for Key Derivation ---
def _derive_key_material(password: str, salt: bytes, key_data: bytes = None, dkLen: int = 32) -> bytes:
    """
    Derives a cryptographic key using PBKDF2, combining password and optional key_data.
    """
    password_bytes = password.encode('utf-8')
    if key_data:
        # Combine password and key_data for a stronger seed for PBKDF2
        # Use a consistent, non-reversible combination if key_data is binary.
        # For simplicity here, we concatenate, then hash, then use as part of PBKDF2 input.
        # A more robust approach might be to use key_data as a secret salt if applicable
        # or use a different KDF combining multiple secrets.
        # Given PBKDF2 takes password and salt, we'll combine them to make a 'super-password'.
        combined_password_seed = hashlib.sha256(password_bytes + key_data).digest()
    else:
        combined_password_seed = password_bytes

    # PBKDF2 returns the derived key (dkLen bytes long)
    # The 'salt' here is the random salt *for PBKDF2 itself*, not the `SALT_SIZE` from `key_data`.
    # PBKDF2 handles its internal salt generation if not explicitly given, but here we pass ours.
    return PBKDF2(combined_password_seed, salt, dkLen=dkLen, count=PBKDF2_ITER)

# --------------------------- AES ----------------------------
def encrypt_aes(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = get_random_bytes(SALT_SIZE) # Salt for PBKDF2
    key = _derive_key_material(password, salt, key_data, dkLen=32) # AES key is 32 bytes for AES-256
    iv = get_random_bytes(BLOCK_SIZE_AES) # IV for CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # PKCS7 padding equivalent
    pad_len = BLOCK_SIZE_AES - len(data) % BLOCK_SIZE_AES
    data += bytes([pad_len]) * pad_len
    encrypted = cipher.encrypt(data)
    return salt + iv + encrypted # Prepend salt and IV to the ciphertext

def decrypt_aes(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = data[:SALT_SIZE]
    iv = data[SALT_SIZE:SALT_SIZE + BLOCK_SIZE_AES]
    encrypted = data[SALT_SIZE + BLOCK_SIZE_AES:]
    key = _derive_key_material(password, salt, key_data, dkLen=32)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    # Unpad
    pad_len = decrypted[-1]
    # Check for valid padding length (important for integrity check)
    if not (1 <= pad_len <= BLOCK_SIZE_AES and decrypted[-pad_len:] == bytes([pad_len]) * pad_len):
        raise ValueError("Invalid padding detected during AES decryption. Possible incorrect password/key or corrupted data.")
    return decrypted[:-pad_len]

# ------------------------- Blowfish --------------------------
def encrypt_blowfish(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = get_random_bytes(SALT_SIZE)
    # Blowfish key length can be variable (32-448 bits, i.e., 4-56 bytes)
    # derive 56 bytes to provide maximum strength for Blowfish
    key = _derive_key_material(password, salt, key_data, dkLen=56)
    iv = get_random_bytes(BLOCK_SIZE_BLOWFISH)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    # PKCS7 padding equivalent
    pad_len = BLOCK_SIZE_BLOWFISH - len(data) % BLOCK_SIZE_BLOWFISH
    data += bytes([pad_len]) * pad_len
    encrypted = cipher.encrypt(data)
    return salt + iv + encrypted

def decrypt_blowfish(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = data[:SALT_SIZE]
    iv = data[SALT_SIZE:SALT_SIZE + BLOCK_SIZE_BLOWFISH]
    encrypted = data[SALT_SIZE + BLOCK_SIZE_BLOWFISH:]
    key = _derive_key_material(password, salt, key_data, dkLen=56)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    # Unpad
    pad_len = decrypted[-1]
    # Check for valid padding length
    if not (1 <= pad_len <= BLOCK_SIZE_BLOWFISH and decrypted[-pad_len:] == bytes([pad_len]) * pad_len):
        raise ValueError("Invalid padding detected during Blowfish decryption. Possible incorrect password/key or corrupted data.")
    return decrypted[:-pad_len]

# -------------------------- Fernet ---------------------------
def encrypt_fernet(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = get_random_bytes(SALT_SIZE)
    # Fernet key needs to be 32 URL-safe base64-encoded bytes
    key_material = _derive_key_material(password, salt, key_data, dkLen=32)
    fernet_key = base64.urlsafe_b64encode(key_material)
    f = Fernet(fernet_key)
    encrypted = f.encrypt(data)
    return salt + encrypted # Prepend salt to the Fernet token

def decrypt_fernet(data: bytes, password: str, key_data: bytes = None) -> bytes:
    salt = data[:SALT_SIZE]
    encrypted = data[SALT_SIZE:]
    key_material = _derive_key_material(password, salt, key_data, dkLen=32)
    fernet_key = base64.urlsafe_b64encode(key_material)
    f = Fernet(fernet_key)
    return f.decrypt(encrypted) # Fernet handles its own integrity/padding internally

# ---------------------- Dispatcher ---------------------------
# These functions are the main entry points for your UI
def encrypt_file(data: bytes, algorithm: str, password: str, key_data: bytes = None) -> bytes:
    """
    Encrypts data using the specified algorithm, password, and optional key_data.
    """
    if not password: # Ensure password is not empty for encryption
        raise ValueError("Password cannot be empty for encryption.")

    if algorithm == "AES":
        return encrypt_aes(data, password, key_data)
    elif algorithm == "Fernet":
        return encrypt_fernet(data, password, key_data)
    elif algorithm == "Blowfish":
        return encrypt_blowfish(data, password, key_data)
    else:
        raise ValueError(f"Unsupported encryption algorithm: {algorithm}")

def decrypt_file(data: bytes, password: str, algorithm: str, key_data: bytes = None) -> bytes:
    """
    Decrypts data using the specified algorithm, password, and optional key_data.
    Raises ValueError for decryption failures (wrong password/key, corruption).
    """
    if not password: # Ensure password is not empty for decryption
        raise ValueError("Password cannot be empty for decryption.")

    try:
        if algorithm == "AES":
            return decrypt_aes(data, password, key_data)
        elif algorithm == "Fernet":
            return decrypt_fernet(data, password, key_data)
        elif algorithm == "Blowfish":
            return decrypt_blowfish(data, password, key_data)
        else:
            raise ValueError(f"Unsupported decryption algorithm: {algorithm}")
    except (ValueError, InvalidToken) as e:
        # Re-raise with a more generic message for UI, but preserve original for debugging
        raise ValueError(f"Decryption failed. Incorrect password/key or corrupted data. Original error: {e}")

# -------------------- Optional Masking ------------------------
def apply_masking(data: bytes, password: str) -> bytes:
    """
    Applies a secure obfuscation layer using the ChaCha20 stream cipher.
    A random nonce is generated and prepended to the output.
    """
    # Use PBKDF2 to derive a specific key for the masking layer from the password
    # static salt for nonce provides the uniqueness.
    masking_salt = b'rygelock_masking_salt'
    masking_key = PBKDF2(password.encode('utf-8'), masking_salt, dkLen=32, count=1000)  # Faster KDF for this layer

    # Create the ChaCha20 cipher
    cipher = ChaCha20.new(key=masking_key)
    masked_data = cipher.encrypt(data)

    # Prepend the nonce to the data. The nonce is required for decryption.
    # The nonce is public, not secret.
    return cipher.nonce + masked_data


def apply_demasking(data: bytes, password: str) -> bytes:
    """
    Reverses the ChaCha20 stream cipher obfuscation layer.
    """
    # The nonce is the first 8 bytes of the data
    nonce = data[:8]
    masked_data = data[8:]

    # Derive the same key that was used for masking
    masking_salt = b'rygelock_masking_salt'
    masking_key = PBKDF2(password.encode('utf-8'), masking_salt, dkLen=32, count=1000)

    # Create the cipher with the original key and nonce to decrypt
    cipher = ChaCha20.new(key=masking_key, nonce=nonce)
    original_data = cipher.decrypt(masked_data)

    return original_data