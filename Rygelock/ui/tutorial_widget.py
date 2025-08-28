
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QScrollArea, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# --- Technical Manual ---
TUTORIAL_CONTENT = """
Rygelock Technical Manual & User Guide

--- CORE CONCEPT: THE SECURE ENVELOPE ---
Rygelock does not simply hide your data. It seals it inside a secure, authenticated digital "envelope" using AES-GCM encryption. This process ensures:
1.  Confidentiality: The content of your payload and its metadata are fully encrypted.
2.  Integrity & Authenticity: If the hidden data is ever corrupted or if the wrong password is used during extraction, a "MAC check failed" error will occur, guaranteeing that you will never extract a corrupted or incorrect file.

--- EMBEDDING PANEL: OPTIONS ---

[Encryption Algorithm]
Selects the primary encryption algorithm for your payload (AES, Blowfish, or Fernet). This choice is recorded in the encrypted metadata and used for decryption. A strong password is required for all operations.

[Generate Key]
-   What it does: Creates a `real_key.key` file that is cryptographically tied to your specific payload.
-   Technical Detail: Before any encryption, Rygelock calculates a SHA-256 hash of your raw payload data. This hash is stored inside the key file. During extraction, the system will not succeed unless the provided key file contains the correct hash for the decrypted payload.
-   Result: This makes the key file a mandatory second factor for extraction, proving ownership of the original secret data.

[Enable Masking]
-   What it does: Adds an extra layer of obfuscation on top of the encrypted payload.
-   Technical Detail: After the payload is encrypted, this option applies a high-speed ChaCha20 stream cipher to scramble the ciphertext. The key for this layer is derived from your password but uses a unique salt, making it independent of the primary encryption keys.
-   Result: Makes the encrypted data even harder to analyze for cryptographic patterns.

[Matryoshka Layer (Dropdown)]
-   What it does: Applies multiple, independent layers of encryption.
-   Technical Detail: For each extra layer selected (1x to 4x), Rygelock uses HKDF to derive a new, unique encryption key from your master password and a unique salt for that layer. It then re-encrypts the ciphertext from the previous layer with this new key.
-   Result: Creates a nested-doll style of encryption where an attacker would need to break multiple, distinct cryptographic layers.

[Deception Mechanism (Decoy File)]
-   What it does: Hides both a genuine payload and a harmless decoy payload in the same carrier file.
-   Technical Detail: Rygelock creates two completely separate "Secure Envelopes," one for the genuine data (using the primary password/key) and one for the decoy data (using the fake password). It then hides both inside the carrier, separated by static tags (`:::RYGELOCK::FAKE_ENVELOPE:::`).
-   Result: Allows for "Deniable Steganography." If forced to reveal a password, you can provide the fake password, which will successfully extract the harmless decoy file, protecting your genuine secret.

--- EMBEDDING PANEL: BUTTONS ---

[Add Carrier File]
Selects the image, audio, or video file that will act as the container for your hidden data.

[Add Payload File]
Selects the secret file you wish to protect and hide.

[Add Decoy Payload]
Selects a harmless file to be used as a decoy for the Deception Mechanism. Requires a separate, unique fake password.

[Start Hiding]
Initiates the steganography process. It will:
1.  Validate all inputs (e.g., check for required passwords, ensure payload size is reasonable).
2.  Create the Secure Envelope(s) with all selected security layers.
3.  Call the appropriate steganography algorithm (e.g., `run_simple_jpg_steg`) to hide the final data block inside the carrier.
4.  Save the final stego file to the "Rygelock_Output" folder on your Desktop.

--- EXTRACTION PANEL ---

[Extract]
Initiates the extraction process. It will:
1.  Retrieve the hidden data block from the stego file.
2.  Attempt to open the Secure Envelope(s) using the provided password and key file.
3.  If successful, it reads the encrypted metadata, reverses all security layers (Masking, Matryoshka, etc.), and saves the original payload.
"""



class TutorialWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rygelock User Guide")
        self.setMinimumSize(700, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        main_layout = QVBoxLayout(self)

        title_label = QLabel("Rygelock Technical Manual & User Guide")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("margin-bottom: 10px;")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        tutorial_text_display = QTextEdit()
        tutorial_text_display.setReadOnly(True)
        tutorial_text_display.setFont(QFont("Segoe UI", 11))
        tutorial_text_display.setStyleSheet("border: 1px solid #444; padding: 10px;")

        tutorial_text_display.setPlainText(TUTORIAL_CONTENT)

        content_layout.addWidget(tutorial_text_display)
        scroll_area.setWidget(content_widget)

        close_button = QPushButton("Close")
        close_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        close_button.setMinimumHeight(40)
        close_button.clicked.connect(self.close)

        main_layout.addWidget(title_label)
        main_layout.addWidget(scroll_area)
        main_layout.addWidget(close_button)