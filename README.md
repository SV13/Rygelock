# Rygelock: An Open-Source Steganographic Framework with Multi-Layered Encryption, Masking, and Deception
<img width="100" height="100" alt="logo" src="https://github.com/user-attachments/assets/4078aeff-e8e8-4ba0-87fb-c4f093041209" />

Rygelock was developed as part of my Final Year Project. It is a comprehensive steganography system that supports image, video, and audio-based steganography techniques, and is implemented entirely in Python. The system is designed to help users safeguard their sensitive information through steganography, while also serving as a resource for enthusiasts who wish to build or extend their own steganographic solutions with my code/scripts. Although Rygelock is not yet a magnum opus, future improvements will focus on enhancing usability and delivering the most effective deniable steganography possible.

> **Use responsibly.** Rygelock is provided for education and research. Do not use it to hide or transmit illegal content. Always comply with local laws and institutional policies.

## ✨ Features
- Dual‑payload **genuine + decoy** flow with independent security (password/key/encryption).
- **AES‑GCM** encryption of envelopes prior to embedding.
- **Multiple Encrytion Option** to choose.
- **Matryoshka** multi‑layer embedding (optional).
- **Format-aware** stego algorithms (image/audio/video).
- **Masking** obfuscation layer using ChaCha20, unique salt and random onetime use nonce
- Clear **extraction** workflow with metadata parsing and safeguards.

## 📦 Project Structure
```
Rygelock/
├─ assets/               # icons, logos, system audio
├─ core/                 # algorithms, encryption, engine scripts assets/
├─ ui/                   # UI-based scripts core/
├─ utils/                # helpers (audio, config, validation)
├─ rygel.py                # Main Script
```

## 🧰 Getting Started (Developers)
### 1) Clone and set up a virtual environment
```bash
# Clone your new repo after you create it on GitHub
git clone https://github.com/<your-username>/Rygelock.git
cd Rygelock

# Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install deps
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Run the project
```bash
python rygel.py
```


## 🧪 Verifying Standalone Checksums
- **MD5:**	027b37e23eff71bbb89afdfb8ccca2fe
- **SHA-1:**	7b182c654a400e5950d20289840dfe11adf7c5cf
- **SHA-256:**	bdd4f7b541dde8445a79e50f3d8ccdeac184fcaa05a8976f5a57bab5eef1df52


## 📝 Documentation
See **`Rygelock_User_Guide.pdf`** for a comprehensive guide with screenshots.

