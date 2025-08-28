# Rygelock — Advanced Steganography Toolkit

Rygelock is an educational, multi‑layer steganography toolkit that supports **genuine vs. decoy payloads**, **AES‑GCM encryption**, **key/password gating**, **Matryoshka (multi‑layer) embedding**, optional **masking**, and **format‑aware carriers** (e.g., JPG/PNG/MP3/MP4).

> **Use responsibly.** Rygelock is provided for education and research. Do not use it to hide or transmit illegal content. Always comply with local laws and institutional policies.

## ✨ Features
- Dual‑payload **genuine + decoy** flow with independent security (password/key/encryption).
- **AES‑GCM** encryption of envelopes prior to embedding.
- **Matryoshka** multi‑layer embedding (optional).
- **Format-aware** stego algorithms (image/audio/video).
- Clear **extraction** workflow with metadata parsing and safeguards.

## 📦 Repository Structure
```
Rygelock/
├─ core/                 # algorithms, encryption, engine
├─ ui/                   # Tkinter/CustomTkinter UI
├─ utils/                # helpers (audio, config, validation, etc.)
├─ assets/               # icons, logos, sample media
├─ docs/
│  ├─ user_guide.md      # step-by-step guide with images
│  └─ images/            # screenshots for the guide
├─ requirements.txt      # python dependencies (edit to match your project)
├─ README.md             # this file
├─ LICENSE               # license (MIT by default; edit author/name)
├─ .gitignore
└─ .github/
   └─ workflows/
      └─ build-windows.yml  # GitHub Actions to build a Windows .exe
```

> The folders above reflect a typical layout. If your code already has a different structure (e.g., `core/`, `utils/`, `ui/`, `assets/`, and `rygel.py` as the app entry point), keep your structure and just drop the missing files in.

## 🧰 Getting Started (Developers)
### 1) Clone and set up a virtual environment
```bash
# Clone your new repo after you create it on GitHub
git clone https://github.com/<your-username>/Rygelock.git
cd Rygelock

# Create & activate a virtual environment (Windows)
python -m venv .venv
.venv\Scripts\activate

# Or on Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Install deps
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Run the app (example)
```bash
python rygel.py
```

> Update the command above if your entry file has a different name.

## 🏗️ Building a Windows .exe (local)
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed rygel.py
# Your exe will appear in the ./dist folder
```

You can also let **GitHub Actions** build a Windows executable when you push a version tag (see `.github/workflows/build-windows.yml`).

## 🚀 Download Binaries (Releases)
Publish pre-built `.exe` files for users under **GitHub → Releases**. Steps:
1. Click **Releases** → **Draft a new release**.
2. Tag it like `v1.0.0` (Semantic Versioning).
3. Upload your built `.exe`, add notes/changelog, and **Publish**.

## 🧪 Verifying Checksums (optional)
For integrity, upload checksums (e.g., `SHA-256`) alongside the `.exe`:
```bash
# Example on Windows (PowerShell)
Get-FileHash .\dist\Rygelock.exe -Algorithm SHA256
```

## 📝 Documentation
See **`docs/user_guide.md`** for a step‑by‑step guide with screenshots (place images in `docs/images/` and link in the guide). You can publish docs via **GitHub Pages** (Settings → Pages → Source: `main` branch, folder `/docs`).

## 🤝 Contributing
- Open an issue for bugs/requests.
- For PRs, follow a short branch style: `feature/...`, `fix/...`, `docs/...`.
- Keep commits focused and meaningful; include a short rationale in the message body.

## 📄 License
This project is licensed under the **MIT License** — see **LICENSE** for details.

---

### Quick Start: First-time GitHub (Zero to Repo)

**A. Create a GitHub account** at https://github.com and set your display name & email.

**B. Install a Git client**  
- Easiest: **GitHub Desktop** → *File → New Repository…* (pick a folder) → *Publish repository*  
- Or CLI (Windows): install Git from https://git-scm.com, then:

```bash
mkdir Rygelock && cd Rygelock
git init
# Copy your project files into this folder, then:
git add .
git commit -m "Initial commit: Rygelock source"
git branch -M main
git remote add origin https://github.com/<your-username>/Rygelock.git
git push -u origin main
```

**C. Add your .exe via Releases** (recommended) instead of committing binaries directly.

**D. Add screenshots to `docs/images/` and link them from `docs/user_guide.md`.**

**E. Keep going:** open Issues for tasks, use Projects for planning, and publish docs via GitHub Pages.
