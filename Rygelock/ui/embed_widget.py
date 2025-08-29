import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QTextEdit, QLineEdit, QFileDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QMessageBox, QRadioButton, QButtonGroup, QSizePolicy, QGroupBox, QComboBox
)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.algorithm import detect_algorithm
from core.steg_engine import embed_files
from core.deception_mech import prepare_fake_output
from utils.config import get_output_dir
from utils.file_validator import apply_data_whitening
from ui.embed_progress_popup import EmbedProgressPopup
from ui.result_viewer import ResultViewer
from utils.audio import play_sound
from ui.custom_dialog import CustomDialog
from utils.resource_path import resource_path

SUPPORTED_CARRIER_EXTENSIONS = [".png", ".jpg", ".jpeg", "JPG", ".bmp", ".tiff", ".mp4", ".mp3"]


class EmbedWidget(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.back_btn = QPushButton("🔙 Back")
        self.back_btn.setFixedWidth(150)
        self.back_btn.setToolTip("Return to the main menu")
        self.back_btn.clicked.connect(self.handle_back)
        header_layout.addWidget(self.back_btn)

        supported_label = QLabel("Supported: PNG, JPG, jpg, jpeg, bmp, tiff, MP4, MP3")
        supported_label.setStyleSheet("color: orange; font-style: italic;")
        header_layout.addWidget(supported_label)

        header_layout.addStretch()
        reset_btn = QPushButton()
        reset_btn.setIcon(QIcon(QPixmap(resource_path("assets/reset.png"))))
        reset_btn.setToolTip("Reset all fields")
        reset_btn.clicked.connect(self.reset_all_fields)
        header_layout.addWidget(reset_btn)

        layout.addLayout(header_layout)

        grid = QGridLayout()
        carrier_label = QLabel("Carrier File")
        carrier_label.setToolTip("Files that will carry your hidden data")
        self.carrier_table = QTableWidget(0, 1)
        self.carrier_table.setHorizontalHeaderLabels(["File Path"])
        self.carrier_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.carrier_table.horizontalHeader().setStretchLastSection(True)
        self.carrier_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        add_carrier_btn = QPushButton("Add Carrier File")
        add_carrier_btn.setToolTip("Upload a file to hide data into")
        add_carrier_btn.clicked.connect(self.add_carrier_file)

        grid.addWidget(carrier_label, 0, 0)
        grid.addWidget(self.carrier_table, 1, 0)
        grid.addWidget(add_carrier_btn, 2, 0)

        payload_label = QLabel("Payload File")
        payload_label.setToolTip("Files you want to hide inside the carrier")
        self.payload_display = QTextEdit()
        self.payload_display.setReadOnly(True)
        self.payload_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        add_payload_btn = QPushButton("Add Payload File")
        add_payload_btn.setToolTip("Browse and add one or more payload files")
        add_payload_btn.clicked.connect(self.add_payload_file)

        grid.addWidget(payload_label, 0, 1)
        grid.addWidget(self.payload_display, 1, 1)
        grid.addWidget(add_payload_btn, 2, 1)

        layout.addLayout(grid)

        form_grid = QGridLayout()

        encryption_groupbox = QGroupBox("Encryption & Layers")
        encryption_col = QVBoxLayout(spacing=3)
        encryption_label = QLabel("Encryption Selection")
        encryption_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

        self.encryption_aes = QRadioButton("AES")
        self.encryption_des = QRadioButton("Blowfish")
        self.encryption_fernet = QRadioButton("Fernet")
        self.encryption_aes.setChecked(True)
        self.encryption_group = QButtonGroup()
        for btn in [self.encryption_aes, self.encryption_des, self.encryption_fernet]:
            self.encryption_group.addButton(btn)
        self.encryption_group.buttonClicked.connect(self.toggle_encryption_password)

        self.enc_password_input = QLineEdit()
        self.enc_password_input.setPlaceholderText("Encryption password (optional)")
        self.enc_password_input.setEchoMode(QLineEdit.Password)  # Mask password input
        self.enc_password_input.setEnabled(False)  # Initially disabled
        self.enc_password_input.setToolTip("Used to decrypt payloads if encryption is selected")
        # Connect textChanged signal to validation
        self.enc_password_input.textChanged.connect(self.validate_embedding_inputs)

        # --- Password Warning Label ---
        self.password_warning_label = QLabel("A password is required for selected encryption.")
        self.password_warning_label.setStyleSheet("color: #FF6347; font-weight: bold;")  # Tomato red for warning
        self.password_warning_label.setWordWrap(True)
        self.password_warning_label.hide()  # Hidden by default

        self.generate_key_checkbox = QCheckBox("Generate Key")
        self.generate_key_checkbox.setToolTip("Generate a unique key file for unlocking")
        self.masking_checkbox = QCheckBox("Enable Masking")
        self.masking_checkbox.setToolTip("Enable obfuscation to disguise payload content")

        matryoshka_label = QLabel("Matryoshka Layer")
        self.matryoshka_combo = QComboBox()
        self.matryoshka_combo.addItems([
            "None (1 Layer Total)",
            "1x (2 Layers Total)",
            "2x (3 Layers Total)",
            "3x (4 Layers Total)",
            "4x (5 Layers Total)"
        ])
        self.matryoshka_combo.setToolTip("Encrypts payload with unique derived keys. More layer more time for hiding & extraction.")

        for w in [encryption_label, self.encryption_aes, self.encryption_des,
                  self.encryption_fernet,
                  self.enc_password_input, self.password_warning_label,  # Add warning label here
                  self.generate_key_checkbox, self.masking_checkbox, self.matryoshka_combo]:
            encryption_col.addWidget(w)
        encryption_groupbox.setLayout(encryption_col)

        deception_groupbox = QGroupBox("Deception Mechanism")
        deception_col = QVBoxLayout(spacing=4)

        deception_label = QLabel("Decoy File")
        self.fake_payload_display = QTextEdit()
        self.fake_payload_display.setReadOnly(True)
        self.fake_payload_display.setToolTip("Optional decoy files to mislead attackers")
        add_fake_payload_btn = QPushButton("Add Decoy Payload")
        add_fake_payload_btn.setToolTip("Browse and select a fake file")
        add_fake_payload_btn.clicked.connect(self.add_fake_payload)
        self.fake_password_input = QLineEdit()
        self.fake_password_input.setPlaceholderText("Fake password")
        self.fake_password_input.setEchoMode(QLineEdit.Password)  # Mask fake password input
        self.fake_password_input.textChanged.connect(self.validate_embedding_inputs)
        self.fake_password_input.setToolTip("Password used to reveal fake data")
        self.generate_fake_key_checkbox = QCheckBox("Generate Fake Key")
        self.generate_fake_key_checkbox.setToolTip("Create a fake key file for decoy reveal")

        for w in [deception_label, self.fake_payload_display, add_fake_payload_btn,
                  self.fake_password_input]:
            deception_col.addWidget(w)
        deception_groupbox.setLayout(deception_col)

        form_grid.addWidget(encryption_groupbox, 0, 0)
        form_grid.addWidget(deception_groupbox, 0, 1)
        layout.addLayout(form_grid)

        self.start_btn = QPushButton("Start Hiding")  # Store reference to the button
        self.start_btn.setToolTip("Start the steganography process with selected options")
        self.start_btn.clicked.connect(self.start_embedding)
        layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)

        self.back_btn.setFocus()

        # Initialize the password field state based on default selection ("None")
        self.toggle_encryption_password()
        # Initial validation when the widget is created
        self.validate_embedding_inputs()

    def handle_back(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'setCurrentIndex'):
                parent.setCurrentIndex(0)
                return
            parent = parent.parent()

    def toggle_encryption_password(self):
        """
        With password now mandatory, this function just updates the warning label text.
        The password input is always enabled.
        """
        selected = self.encryption_group.checkedButton().text()
        # The password field is now ALWAYS enabled.
        self.enc_password_input.setEnabled(True)
        self.enc_password_input.setPlaceholderText("Password (Required)")
        self.password_warning_label.setText(f"A password is required for {selected} encryption.")
        self.password_warning_label.show()
        self.validate_embedding_inputs()

        # Also, update the state of the start button based on validation
        self.validate_embedding_inputs()

    def reset_all_fields(self):
        self.carrier_table.setRowCount(0)
        self.payload_display.clear()
        self.fake_payload_display.clear()
        self.fake_password_input.clear()
        self.enc_password_input.clear()
        self.encryption_aes.setChecked(True)
        self.generate_key_checkbox.setChecked(False)
        self.generate_fake_key_checkbox.setChecked(False)
        self.masking_checkbox.setChecked(False)
        self.matryoshka_combo.setCurrentIndex(0)
        self.back_btn.setFocus()
        self.toggle_encryption_password()  # Reset password field state
        self.validate_embedding_inputs()  # Ensure button state is updated on reset

    def add_carrier_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Carrier File")
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in SUPPORTED_CARRIER_EXTENSIONS:
                QMessageBox.warning(self, "Unsupported File", "This file type is not supported as a carrier file.")
                return
            for row in range(self.carrier_table.rowCount()):
                if self.carrier_table.item(row, 0).text() == file_path:
                    QMessageBox.warning(self, "Duplicate File", "This carrier file is already added.")
                    return
            row = self.carrier_table.rowCount()
            self.carrier_table.insertRow(row)
            self.carrier_table.setRowCount(1)  # Ensure there is exactly one row
            self.carrier_table.setItem(0, 0, QTableWidgetItem(file_path))
            self.validate_embedding_inputs()  # Validate after adding carrier

    def add_payload_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Payload File")
        if file:
            self.payload_display.setText(file)
            self.validate_embedding_inputs()  # Validate after adding payload

    def add_fake_payload(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Fake Payload File")
        if file:
            self.fake_payload_display.setText(file)
            self.validate_embedding_inputs()  # Validate after adding fake payload

    def validate_embedding_inputs(self):
        """
        Validates all user inputs. Instead of disabling a button, this now returns
        a boolean for success and a specific error message for failure.
        """
        # 1. Check for presence of essential files
        if self.carrier_table.rowCount() == 0:
            return False, "Please add a carrier file."
        if not self.payload_display.toPlainText().strip():
            return False, "Please add a genuine payload file."

        # 2. Check password requirements for encryption
        selected_encryption = self.encryption_group.checkedButton().text()
        if selected_encryption != "None" and not self.enc_password_input.text().strip():
            return False, f"Encryption is set to '{selected_encryption}', but no password was provided."

        # 3. Check password requirements for deception mechanism
        fake_payloads_exist = bool(self.fake_payload_display.toPlainText().strip())
        if fake_payloads_exist and not self.fake_password_input.text().strip():
            return False, "A fake payload has been added, but no fake password was provided."
        if self.fake_password_input.text().strip() and not fake_payloads_exist:
            return False, "You entered a Fake password but no decoy payload was added. Please add a decoy payload or clear the fake password."

        # 4. Check that passwords are not identical
        real_password = self.enc_password_input.text().strip()
        fake_password = self.fake_password_input.text().strip()
        if fake_payloads_exist and real_password and fake_password and real_password == fake_password:
            return False, "The genuine password and the fake password cannot be the same."

        # 5. --- CAPACITY CHECK (Using a 50% "Stealth" Limit) ---
        try:
            total_payload_size = 0
            for path in self.payload_display.toPlainText().splitlines():
                if path.strip(): total_payload_size += os.path.getsize(path.strip())
            for path in self.fake_payload_display.toPlainText().splitlines():
                if path.strip(): total_payload_size += os.path.getsize(path.strip())

            if self.carrier_table.rowCount() > 0:
                carrier_path = self.carrier_table.item(0, 0).text()
                carrier_size = os.path.getsize(carrier_path)

                if total_payload_size > (carrier_size * 0.50):
                    carrier_name = os.path.basename(carrier_path)
                    error_msg = (f"Payload size is too large for the carrier file.\n\n"
                                 f"Total payload size: {total_payload_size / 1024:.1f} KB\n"
                                 f"Carrier '{carrier_name}' size: {carrier_size / 1024:.1f} KB\n\n"
                                 "Please use a larger carrier file or smaller payloads.")
                    return False, error_msg

        except FileNotFoundError as e:
            return False, f"A file could not be found during validation: {e.filename}"
        except Exception as e:
            return False, f"An error occurred during validation: {e}"

        # If all checks pass
        return True, "Validation successful."

    def start_embedding(self):
        # This function now calls the validator first.
        is_valid, message = self.validate_embedding_inputs()

        # If validation fails, show the user-friendly popup and stop.
        if not is_valid:
            play_sound("fail", self.config)
            dialog = CustomDialog("Validation Error", message, self)
            dialog.exec_()
            return

        # If validation succeeds, proceed with the steganography operation.
        carriers = []
        for row in range(self.carrier_table.rowCount()):
            filepath = self.carrier_table.item(row, 0).text()
            algorithm = detect_algorithm(filepath) or "default"
            carriers.append({"file": filepath, "algorithm": algorithm})

        payloads = [line.strip() for line in self.payload_display.toPlainText().splitlines() if line.strip()]
        fake_payloads = [line.strip() for line in self.fake_payload_display.toPlainText().splitlines() if line.strip()]

        password = self.enc_password_input.text().strip() or None
        fake_password = self.fake_password_input.text().strip() or None

        config = {
            "carriers": carriers,
            "payloads": payloads,
            "encryption": self.encryption_group.checkedButton().text(),
            "password": password,
            "fake_password": fake_password,
            "generate_key": self.generate_key_checkbox.isChecked(),
            "masking": self.masking_checkbox.isChecked(),
            "matryoshka_layers": self.matryoshka_combo.currentIndex(),
            "fake_payloads": fake_payloads,
            "generate_fake_key": self.generate_fake_key_checkbox.isChecked(),
            "output_dir": get_output_dir()
        }

        if config["fake_payloads"] or config["generate_fake_key"]:
            prepare_fake_output(config)

        self.progress_popup = EmbedProgressPopup(self.config)
        self.progress_popup.show()

        class WorkerThread(QThread):
            progress = pyqtSignal(int)
            done = pyqtSignal(dict)

            def run(self_):
                try:
                    # The 'config' dictionary is already fully prepared here
                    result = embed_files(config, self_.progress.emit)
                except Exception as e:
                    result = {"status": "error", "message": str(e)}
                self_.done.emit(result)

        self.worker = WorkerThread()
        self.worker.progress.connect(self.progress_popup.update_progress)
        self.worker.done.connect(self.progress_popup.close_and_show_result)
        self.worker.start()