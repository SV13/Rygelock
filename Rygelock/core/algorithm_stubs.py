import os
import numpy as np
from PIL import Image
import pywt
import math
import hashlib
from datetime import datetime
import json
import shutil
from pydub import AudioSegment
import wave
import contextlib
import tempfile
from scipy.signal import wiener
from scipy.fftpack import dct , idct
from scipy.ndimage import uniform_filter, convolve
from scipy.fftpack import dct, idct
from utils.key_encoder import generate_dict_checksum
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, PRIV


HEADER_MARKER = b"RYGELHDR\0"

def run_stc(carrier_path, payload_path, output_path):
    """
    STC-like simulation Embedding payload bits into carrier using selective bit flipping with parity-style constraint
    """
    try:
        with open(carrier_path, 'rb') as f:
            carrier_bytes = bytearray(f.read())

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{byte:08b}' for byte in payload)
        payload_index = 0

        block_size = 8
        max_capacity = len(carrier_bytes) // block_size

        if len(payload_bits) > max_capacity * block_size:
            raise ValueError("Payload too large to embed in carrier.")

        for i in range(0, len(carrier_bytes), block_size):
            if payload_index >= len(payload_bits):
                break

            for j in range(block_size):
                bit_pos = i + j
                if bit_pos >= len(carrier_bytes) or payload_index >= len(payload_bits):
                    break
                target_bit = int(payload_bits[payload_index])
                carrier_bytes[bit_pos] = (carrier_bytes[bit_pos] & 0xFE) | target_bit
                payload_index += 1

        with open(output_path, 'wb') as f:
            f.write(carrier_bytes)

        return output_path

    except Exception as e:
        print(f"[run_stc ERROR] {e}")
        return None


def run_s_uniward(carrier_path, payload_path, output_path):
    """
    S-UNIWARD using wavelet-domain distortion modeling.
    Input: grayscale PNG/JPEG, payload file (binary), output file path.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.float32)

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        coeffs = pywt.wavedec2(img_np, 'db8', level=2)
        _, (LH, HL, HH) = coeffs[1]
        cost_map = np.abs(LH) + np.abs(HL) + np.abs(HH)
        cost_map = 1 / (1 + cost_map)
        cost_map = np.clip(cost_map, 0.001, 1.0)

        flat_img = img_np.flatten()
        flat_costs = np.repeat(cost_map.flatten(), 1)
        modifiable_indices = np.argsort(flat_costs)

        if total_bits > len(modifiable_indices):
            raise ValueError("Payload too large to embed with distortion constraints.")

        for i in range(total_bits):
            idx = modifiable_indices[i]
            bit = int(payload_bits[i])
            current_pixel = int(flat_img[idx])
            if (current_pixel % 2) != bit:
                flat_img[idx] = np.clip(current_pixel ^ 1, 0, 255)

        stego_img = Image.fromarray(flat_img.reshape(img_np.shape).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_s_uniward ERROR] {e}")
        return None


def run_hugo(carrier_path, payload_path, output_path, gamma=1.0, sigma=1.0):
    """
    HUGO-inspired embedding: calculates pixel-wise costs using directional differences and embeds data minimizing distortion.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.int32)
        padded = np.pad(img_np, pad_width=3, mode='reflect')

        rows, cols = img_np.shape
        costs = np.zeros((rows, cols, 3), dtype=np.float32)  # [decrease, unchanged, increase]

        def eval_cost(k, l, m):
            return (sigma + math.sqrt(k*k + l*l + m*m)) ** -gamma

        def eval_direction(r, c, dr, dc):
            p = [padded[r + dr*k, c + dc*k] for k in range(-3, 4)]
            d = [p[i+1] - p[i] for i in range(6)]
            pixel_costs = np.zeros(3)

            pixel_costs[0] += eval_cost(d[0], d[1], d[2]-1) + eval_cost(d[1], d[2]-1, d[3]+1)
            pixel_costs[2] += eval_cost(d[0], d[1], d[2]+1) + eval_cost(d[1], d[2]+1, d[3]-1)

            pixel_costs[0] += eval_cost(d[2]-1, d[3]+1, d[4]) + eval_cost(d[3]+1, d[4], d[5])
            pixel_costs[2] += eval_cost(d[2]+1, d[3]-1, d[4]) + eval_cost(d[3]-1, d[4], d[5])

            return pixel_costs

        for r in range(rows):
            for c in range(cols):
                r_p, c_p = r + 3, c + 3
                total = eval_direction(r_p, c_p, -1, 1) + eval_direction(r_p, c_p, 0, 1) + \
                        eval_direction(r_p, c_p, 1, 1) + eval_direction(r_p, c_p, 1, 0)
                if img_np[r, c] == 255:
                    total[2] = np.inf
                if img_np[r, c] == 0:
                    total[0] = np.inf
                costs[r, c] = [total[0], 0, total[2]]

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        flat_img = img_np.flatten()
        cost_scores = (costs[:, :, 0] + costs[:, :, 2]).flatten()
        modifiable_indices = np.argsort(cost_scores)

        if total_bits > len(modifiable_indices):
            raise ValueError("Payload too large to embed into carrier.")

        for i in range(total_bits):
            idx = modifiable_indices[i]
            bit = int(payload_bits[i])
            pixel_val = flat_img[idx]
            if (pixel_val % 2) != bit:
                flat_img[idx] = np.clip(pixel_val ^ 1, 0, 255)

        stego_img = Image.fromarray(flat_img.reshape(rows, cols).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_hugo ERROR] {e}")
        return None


def run_mvg(carrier_path, payload_path, output_path):
    """
    MVG-like steganography based on local Fisher information embedding simulation.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.float32)
        shape = img_np.shape

        # Read payload and convert to bits
        with open(payload_path, 'rb') as f:
            payload = f.read()
        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        # 1. Compute Wiener-filtered residuals
        residuals = img_np - wiener(img_np, (3, 3))

        # 2. Estimate local variance using blockwise DCT energy
        def local_variance(block):
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
            return np.var(dct_block)

        window_size = 8
        variances = np.zeros(shape)
        for i in range(0, shape[0] - window_size + 1):
            for j in range(0, shape[1] - window_size + 1):
                block = img_np[i:i+window_size, j:j+window_size]
                var = local_variance(block)
                variances[i:i+window_size, j:j+window_size] += var
        variances /= (window_size * window_size)

        # 3. Compute Fisher Information (1/variance^2)
        with np.errstate(divide='ignore'): # handle division by zero
            fisher_map = 1.0 / (variances**2)
            fisher_map = np.nan_to_num(fisher_map, nan=0.0, posinf=0.0, neginf=0.0)
        fisher_flat = fisher_map.flatten()

        # 4. Probabilistic ±1, ±2 pixel modifications
        beta = 2.0
        theta = 0.25
        rand_map = np.random.rand(fisher_flat.shape[0])
        flat_img = img_np.flatten()
        payload_index = 0

        for idx in np.argsort(-fisher_flat): # descending FI importance
            if payload_index >= total_bits:
                break

            bit = int(payload_bits[payload_index])
            current_pixel = flat_img[idx]
            modified_pixel = current_pixel

            # Decide modification based on cost and bit
            cost_plus_1 = fisher_flat[idx]
            cost_minus_1 = fisher_flat[idx]

            if (current_pixel % 2) != bit:
                if rand_map[idx] < (cost_plus_1 / (cost_plus_1 + cost_minus_1)):
                    modified_pixel += 1
                else:
                    modified_pixel -= 1
            else:
                if rand_map[idx] < theta:
                    if rand_map[idx] < (theta * cost_plus_1 / (cost_plus_1 + cost_minus_1)):
                        modified_pixel += 2
                    else:
                        modified_pixel -= 2

            flat_img[idx] = np.clip(modified_pixel, 0, 255)
            payload_index += 1

        stego_img = Image.fromarray(flat_img.reshape(shape).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_mvg ERROR] {e}")
        return None


def image_steg(carrier_path, payload_path=None, output_path=None, extract=False, payload=None,
                        payload_size=None, **kwargs):
    """
    Append-based steganography for any image file type.
    This version is self-contained and uses a size-prefix to ensure correct extraction.
    """
    SIZE_HEADER_LENGTH = 8

    if extract:
        try:
            with open(carrier_path, 'rb') as f:
                # Go to the end of the file minus the size header
                f.seek(-SIZE_HEADER_LENGTH, os.SEEK_END)

                # Read the 8-byte size header
                size_header_bytes = f.read(SIZE_HEADER_LENGTH)
                payload_size_from_file = int.from_bytes(size_header_bytes, 'big')

                # seek to the beginning of the payload
                f.seek(-(SIZE_HEADER_LENGTH + payload_size_from_file), os.SEEK_END)

                # Read exactly the number of bytes for the payload
                payload_data = f.read(payload_size_from_file)

                return payload_data
        except Exception as e:
            print(f"[image_steg EXTRACT ERROR] {e}")
            return b""
    else:
        # --- EMBEDDING LOGIC ---
        try:
            if payload_path:
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()
            elif payload:
                payload_data = payload
            else:
                raise ValueError("A payload must be provided.")

            payload_size = len(payload_data)
            size_header = payload_size.to_bytes(SIZE_HEADER_LENGTH, 'big')
            data_to_append = payload_data + size_header

            shutil.copy(carrier_path, output_path)
            with open(output_path, "ab") as f_out:
                f_out.write(data_to_append)

            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)
            return output_path
        except Exception as e:
            print(f"[image_steg EMBED ERROR] {e}")
            return None


def mp3_steg(carrier_path, payload_path=None, output_path=None, extract=False, payload=None, **kwargs):
    """
    MP3 steganography using a private (PRIV) ID3 tag.
    - Embedding: Places the payload into a custom PRIV tag owned by 'Rygelock'.
    - Extraction: Searches for the 'Rygelock' PRIV tag and returns its data.
    """
    ANONYMOUS_OWNER_ID = 'com.apple.iTunes'

    if extract:
        try:
            audio = MP3(carrier_path, ID3=ID3)
            for frame in audio.tags.getall('PRIV'):
                if frame.owner == ANONYMOUS_OWNER_ID:
                    return frame.data
            return b""
        except Exception as e:
            print(f"[mp3_steg EXTRACT ERROR] {e}")
            return b""
    else:
        # --- EMBEDDING LOGIC ---
        try:
            if payload_path:
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()
            elif payload:
                payload_data = payload
            else:
                raise ValueError("A payload_path or payload bytes must be provided.")

            shutil.copy(carrier_path, output_path)


            # 2. Now, load the NEW file at the output path to modify it
            audio = MP3(output_path, ID3=ID3)

            audio.tags.delall(f'PRIV:{ANONYMOUS_OWNER_ID}')

            frame = PRIV(
                owner=ANONYMOUS_OWNER_ID,
                data=payload_data
            )

            audio.tags.add(frame)

            # 3. Save the modifications to the file (in-place)
            audio.save()

            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)

            return output_path
        except Exception as e:
            print(f"[mp3_steg EMBED ERROR] {e}")
            return None

# --- Steganography for mp4 ---
def mp4_steg(carrier_path, payload_path=None, output_path=None, extract=False, payload=None, **kwargs):
    """
    MP4 steganography by appending a custom top-level box.
    - Embedding: Appends a custom 'rygl' box to the end of the file.
    - Extraction: Searches for the 'rygl' box at the top level.
    """
    RYGELOCK_BOX_TYPE = b'rygl'

    if extract:
        try:
            with open(carrier_path, "rb") as f:
                while True:
                    header = f.read(8)
                    if not header: break
                    box_size = int.from_bytes(header[:4], 'big')
                    box_type = header[4:]

                    if box_type == RYGELOCK_BOX_TYPE:
                        return f.read(box_size - 8)

                    if box_size == 0:
                        break

                    f.seek(box_size - 8, 1)
            return b""
        except Exception as e:
            print(f"[mp4_steg EXTRACT ERROR] {e}")
            return b""
    else:
        try:
            print("\n--- MP4 Structure Analysis (Manual Parser) ---")
            with open(carrier_path, "rb") as f:
                while True:
                    header = f.read(8)
                    if not header:
                        break
                    box_size = int.from_bytes(header[:4], 'big')
                    box_type = header[4:]
                    try:
                        box_type_str = box_type.decode('ascii')
                    except UnicodeDecodeError:
                        box_type_str = str(box_type)
                    print(f"Found Box: '{box_type_str}', Size: {box_size}")
                    if box_size == 0:
                        break
                    f.seek(box_size - 8, 1)
            print("--- Analysis Complete ---")
            # --- END: ADDED ANALYSIS SECTION ---

            if payload_path:
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()
            elif payload:
                payload_data = payload
            else:
                raise ValueError("A payload_path or payload bytes must be provided.")

            rygl_box_size = 8 + len(payload_data)
            rygl_box_header = rygl_box_size.to_bytes(4, 'big') + RYGELOCK_BOX_TYPE
            rygl_box = rygl_box_header + payload_data

            shutil.copy(carrier_path, output_path)

            with open(output_path, "ab") as f_out:
                f_out.write(rygl_box)

            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)

            return output_path

        except Exception as e:
            print(f"[mp4_steg EMBED ERROR] An unhandled error occurred: {e}")
            return None


def run_mipod(carrier_path, payload_path, output_path):
    """
    MIPOD-like simulation: embeds data by modifying DCT coefficients in JPEG/image files.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img, dtype=np.float32)

        # Apply DCT
        dct_coeffs = dct(dct(img_np.T, norm='ortho').T, norm='ortho')

        with open(payload_path, 'rb') as f:
            payload = f.read()

        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)
        payload_idx = 0

        # Simple embedding: embed in low-frequency DCT coefficients
        # This is a highly simplified approach for demonstration
        flat_coeffs = dct_coeffs.flatten()

        if total_bits > len(flat_coeffs) // 2: # Can embed about half the coefficients
            raise ValueError("Payload too large for MIPOD embedding capacity.")

        for i in range(total_bits):
            if payload_idx >= len(flat_coeffs):
                break # No more space

            # Modify coefficient based on payload bit (LSB-like for DCT)
            # This is a conceptual modification, real MIPOD is more complex
            current_coeff = flat_coeffs[payload_idx]
            bit = int(payload_bits[i])

            # Simple LSB-like embedding on the integer part of the coefficient
            int_coeff = int(current_coeff)
            if (int_coeff % 2) != bit:
                if current_coeff >= 0:
                    flat_coeffs[payload_idx] = math.floor(current_coeff) + (1 if bit == 1 else 0) if (math.floor(current_coeff) % 2) != bit else current_coeff
                else:
                    flat_coeffs[payload_idx] = math.ceil(current_coeff) + (1 if bit == 1 else 0) if (math.ceil(current_coeff) % 2) != bit else current_coeff


            flat_coeffs[payload_idx] = (flat_coeffs[payload_idx] & 0xFE) | bit # Simple bit manipulation, conceptual for DCT
            payload_idx += 1


        # Inverse DCT
        modified_dct_coeffs = flat_coeffs.reshape(dct_coeffs.shape)
        stego_img_np = idct(idct(modified_dct_coeffs.T, norm='ortho').T, norm='ortho')

        # Clip and convert back to image
        stego_img_np = np.clip(stego_img_np, 0, 255).astype(np.uint8)
        stego_img = Image.fromarray(stego_img_np)
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_mipod ERROR] {e}")
        return None


def run_wow(carrier_path, payload_path, output_path):
    """
    WOW-like simulation: Embeds data by modifying pixel values in a way that minimizes changes based on local complexity.
    """
    try:
        img = Image.open(carrier_path).convert("L")
        img_np = np.array(img).astype(np.float32)

        with open(payload_path, 'rb') as f:
            payload = f.read()
        payload_bits = ''.join(f'{b:08b}' for b in payload)
        total_bits = len(payload_bits)

        # Calculate local complexity (e.g., using variance or gradient magnitude)
        # This is a very simple approximation; actual WOW uses more sophisticated cost functions
        complexity_map = uniform_filter(img_np, size=3) # Example: blur for smoothness, inverse for complexity
        complexity_map = np.abs(img_np - complexity_map) + 1 # Higher difference = higher complexity
        cost_map = 1 / complexity_map # Lower cost for higher complexity areas
        cost_map = np.clip(cost_map, 0.001, 1.0) # Avoid division by zero, ensure valid range

        flat_img = img_np.flatten()
        flat_costs = cost_map.flatten()
        modifiable_indices = np.argsort(flat_costs) # Sort by increasing cost (embed in cheapest first)

        if total_bits > len(modifiable_indices):
            raise ValueError("Payload too large to embed with WOW distortion constraints.")

        for i in range(total_bits):
            idx = modifiable_indices[i]
            bit = int(payload_bits[i])
            current_pixel = int(flat_img[idx])

            if (current_pixel % 2) != bit:
                # Modify pixel to match bit, with minimal change (+1 or -1)
                if current_pixel == 0: # Can only increase
                    flat_img[idx] = 1 if bit == 1 else 0 # Should ideally be 0 if bit is 0
                elif current_pixel == 255: # Can only decrease
                    flat_img[idx] = 254 if bit == 0 else 255 # Should ideally be 255 if bit is 1
                else:
                    # Choose direction that results in lower distortion if possible, or just flip
                    flat_img[idx] = current_pixel ^ 1 # Simple flip for demonstration

        stego_img = Image.fromarray(flat_img.reshape(img_np.shape).astype(np.uint8))
        stego_img.save(output_path)
        return output_path

    except Exception as e:
        print(f"[run_wow ERROR] {e}")
        return None


def synch_steg(carrier_path, payload_path, output_path):
    """
    SYNCH steganography for video (MP4, MKV, AVI).
    Embeds data by appending it to a 'free' box, similar to MP4 handling.
    """
    try:
        with open(carrier_path, 'rb') as f:
            video_data = f.read()

        with open(payload_path, 'rb') as f:
            payload_data = f.read()

        # Simple appending of the payload
        stego_data = video_data + payload_data + b"\0" # Add a null terminator for safety

        if output_path is None:
            name, ext = os.path.splitext(carrier_path)
            output_path = f"{name}_stego{ext}"

        with open(output_path, "wb") as f:
            f.write(stego_data)

        if payload_path and payload_path.endswith(".payload"):
            os.remove(payload_path)

        return output_path
    except Exception as e:
        print(f"[synch_steg ERROR] {e}")
        return None


def advanced_image_steg(carrier_path, payload_path=None, output_path=None, extract=False, payload=None, **kwargs):
    """
    LSB implementation for lossless images (PNG, BMP).
    Handles different image modes and uses a memory-efficient extraction method.
    """
    DELIMITER = b'---RYGELOCK_EOF---'
    DELIMITER_BITS = ''.join(f'{byte:08b}' for byte in DELIMITER)

    if extract:
        try:
            with Image.open(carrier_path) as img:
                # Handle images with transparency (Alpha channel) by ignoring it
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert('RGB')

                pixels = img.load()
                width, height = img.size

                bit_buffer = ""
                delimiter_len = len(DELIMITER_BITS)

                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        # Extract LSB from each channel
                        bit_buffer += str(r & 1)
                        bit_buffer += str(g & 1)
                        bit_buffer += str(b & 1)

                        # Check for delimiter efficiently without building a huge string
                        if len(bit_buffer) >= delimiter_len:
                            if bit_buffer.endswith(DELIMITER_BITS):
                                payload_bits = bit_buffer[:-delimiter_len]
                                num_bytes = len(payload_bits) // 8
                                payload_data = int(payload_bits, 2).to_bytes(num_bytes, byteorder='big')
                                return payload_data

                print("[advanced_image_steg EXTRACT WARNING] Reached end of image without finding delimiter.")
                return b""
        except Exception as e:
            print(f"[advanced_image_steg EXTRACT ERROR] {e}")
            return b""
    else:
        # --- LSB EMBEDDING LOGIC ---
        try:
            if payload_path:
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()
            elif payload:
                payload_data = payload
            else:
                raise ValueError("A payload must be provided.")

            with Image.open(carrier_path) as img:
                # Handle images with transparency by converting to a consistent RGB format
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert('RGB')
                    print(f"[INFO] Carrier image converted to RGB to handle transparency.")

                pixels = img.load()
                width, height = img.size

                payload_bits = ''.join(f'{byte:08b}' for byte in payload_data) + DELIMITER_BITS
                required_bits = len(payload_bits)
                available_bits = width * height * 3

                if required_bits > available_bits:
                    raise ValueError(f"Payload is too large. Required: {required_bits}, Available: {available_bits}")

                bit_index = 0
                for y in range(height):
                    for x in range(width):
                        if bit_index < required_bits:
                            r, g, b = pixels[x, y]

                            # Embed in R channel
                            if bit_index < required_bits:
                                r = (r & 0xFE) | int(payload_bits[bit_index])
                                bit_index += 1
                            # Embed in G channel
                            if bit_index < required_bits:
                                g = (g & 0xFE) | int(payload_bits[bit_index])
                                bit_index += 1
                            # Embed in B channel
                            if bit_index < required_bits:
                                b = (b & 0xFE) | int(payload_bits[bit_index])
                                bit_index += 1

                            pixels[x, y] = (r, g, b)
                        else:
                            break
                    if bit_index >= required_bits:
                        break

                img.save(output_path, "PNG")

            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)

            return output_path
        except Exception as e:
            print(f"[advanced_image_steg EMBED ERROR] {e}")
            return None


def new_jpeg_steg(carrier_path, payload_path=None, output_path=None, extract=False, payload=None, **kwargs):
    """
    Steganography for JPEG files using LSB of DCT coefficients.
    """
    DELIMITER = "1111111111111110"  # 16-bit delimiter

    def apply_dct(image_block):
        # Apply DCT to an 8x8 block
        return dct(dct(image_block.T, norm='ortho').T, norm='ortho')

    def apply_idct(dct_block):
        # Apply inverse DCT to an 8x8 block
        return idct(idct(dct_block.T, norm='ortho').T, norm='ortho')

    try:
        with Image.open(carrier_path) as img:
            # 1. Convert to YCbCr color space (Luminance, Chroma Blue, Chroma Red)
            # This is how JPEG separates brightness from color information.
            img_ycbcr = img.convert('YCbCr')
            y, cb, cr = img_ycbcr.split()

            # We will only modify the luminance (Y) channel
            y_array = np.array(y, dtype=float)
            height, width = y_array.shape

        if extract:
            all_coeffs = []
            # Process the image in 8x8 blocks
            for i in range(0, height, 8):
                for j in range(0, width, 8):
                    block = y_array[i:i + 8, j:j + 8]
                    dct_block = apply_dct(block)
                    all_coeffs.extend(dct_block.flatten().astype(int))

            extracted_bits = ""
            for coeff in all_coeffs:
                if coeff != 0 and coeff != 1:  # JSteg rule
                    extracted_bits += str(abs(coeff) & 1)
                    if extracted_bits.endswith(DELIMITER):
                        payload_bits = extracted_bits[:-len(DELIMITER)]
                        num_bytes = len(payload_bits) // 8
                        payload_data = int(payload_bits, 2).to_bytes(num_bytes, byteorder='big')
                        return payload_data
            return b""
        else:
            # --- EMBEDDING LOGIC ---
            if payload_path:
                with open(payload_path, 'rb') as f:
                    payload_data = f.read()
            elif payload:
                payload_data = payload
            else:
                raise ValueError("A payload must be provided.")

            payload_bits = ''.join(f'{byte:08b}' for byte in payload_data) + DELIMITER

            # 2. Break the luminance channel into 8x8 blocks and apply DCT
            dct_blocks = []
            all_coeffs = []
            for i in range(0, height, 8):
                for j in range(0, width, 8):
                    block = y_array[i:i + 8, j:j + 8]
                    dct_block = apply_dct(block)
                    dct_blocks.append(dct_block)
                    all_coeffs.extend(dct_block.flatten().astype(int))

            # 3. Check Capacity
            available_bits = len([c for c in all_coeffs if c != 0 and c != 1])
            if len(payload_bits) > available_bits:
                raise ValueError(f"Payload too large. Required: {len(payload_bits)}, Available: {available_bits}")

            # 4. Embed Data into coefficients
            bit_index = 0
            new_coeffs = []
            for coeff in all_coeffs:
                if bit_index < len(payload_bits) and coeff != 0 and coeff != 1:
                    bit_to_hide = int(payload_bits[bit_index])
                    current_lsb = abs(coeff) & 1
                    if current_lsb != bit_to_hide:
                        if coeff > 0:
                            coeff -= 1
                        else:
                            coeff += 1
                    bit_index += 1
                new_coeffs.append(coeff)

            # 5. Reconstruct the image
            new_y_array = np.zeros_like(y_array)
            coeff_index = 0
            for i in range(0, height, 8):
                for j in range(0, width, 8):
                    # Take 64 coefficients for the block
                    block_coeffs_flat = new_coeffs[coeff_index: coeff_index + 64]
                    block_coeffs = np.array(block_coeffs_flat).reshape(8, 8)

                    # Apply inverse DCT to get the pixel block
                    pixel_block = apply_idct(block_coeffs)
                    new_y_array[i:i + 8, j:j + 8] = pixel_block
                    coeff_index += 64

            # Clip values to be in the valid 0-255 range for images
            new_y_array = np.clip(new_y_array, 0, 255)

            # Convert the modified luminance array back to an image
            new_y_image = Image.fromarray(new_y_array.astype('uint8'))

            # Merge the new luminance channel with the original color channels
            stego_image = Image.merge('YCbCr', (new_y_image, cb, cr))

            # Convert back to RGB and save
            stego_image.convert('RGB').save(output_path, 'jpeg', quality=100)

            if payload_path and payload_path.endswith(".payload"):
                os.remove(payload_path)

            return output_path

    except Exception as e:
        print(f"[jpeg_steg ERROR] {e}")
        return None


class LSBImageHandler:
    def __init__(self, carrier_path):
        try:
            self.image = Image.open(carrier_path)
            # Convert to a standard format to ensure consistency and handle palettes
            if self.image.mode != 'RGB':
                self.image = self.image.convert('RGB')
            self.pixels = self.image.load()
            self.width, self.height = self.image.size
            # Capacity is 3 bits per pixel (1 for each R, G, B channel)
            self.capacity = self.width * self.height * 3
            print(f"[LSB Handler] Image loaded. Capacity: {self.capacity} bits.")
        except Exception as e:
            raise IOError(f"Failed to load or process image carrier: {e}")

    def get_capacity_in_bits(self):
        """Returns the total number of bits that can be hidden."""
        return self.capacity

    def embed_bit(self, bit: int, index: int):
        """Hides a single bit at the Nth available LSB location."""
        if index >= self.capacity:
            raise ValueError("Index out of bounds for embedding.")

        pixel_index = index // 3
        channel_index = index % 3

        x = pixel_index % self.width
        y = pixel_index // self.width

        r, g, b = self.pixels[x, y]
        pixel_list = [r, g, b]

        # Modify the LSB of the chosen channel
        pixel_list[channel_index] = (pixel_list[channel_index] & 0xFE) | bit
        self.pixels[x, y] = tuple(pixel_list)

    def extract_bit(self, index: int) -> int:
        """Extracts a single bit from the Nth available LSB location."""
        if index >= self.capacity:
            raise ValueError("Index out of bounds for extraction.")

        pixel_index = index // 3
        channel_index = index % 3

        x = pixel_index % self.width
        y = pixel_index // self.width

        # Return the LSB from the chosen channel
        return self.pixels[x, y][channel_index] & 1

    def save(self, output_path):
        """Saves the modified image to the output path, always as PNG for data integrity."""
        self.image.save(output_path, "PNG")
        print(f"[LSB Handler] Saved stego image to {output_path}")

