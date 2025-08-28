import os
import json

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QFileDialog, QLineEdit, QTextEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt
from core.steg_engine import extract_payload
from utils.resource_path import resource_path


class ExtractWidget(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.analysis_metadata = {}
        self.key_data_from_file = None  # <<< NEW: To store key file content as bytes

    def init_ui(self):
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.back_btn = QPushButton("\u2b05\ufe0f Back")
        self.back_btn.setFixedWidth(150)
        self.back_btn.setToolTip("Return to the main menu")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #202020;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 2px solid #ffcc00;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(self.back_btn)

        header_layout.addStretch()

        self.reset_btn = QPushButton()
        self.reset_btn.setIcon(QIcon(QPixmap(resource_path("assets/reset.png"))))
        self.reset_btn.setToolTip("Reset all fields")
        self.reset_btn.setFixedSize(40, 40)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #ffaa0022;
                border-radius: 6px;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_all)
        header_layout.addWidget(self.reset_btn)

        layout.addLayout(header_layout)

        grid = QGridLayout()

        carrier_label = QLabel("Carrier File(s)")
        carrier_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.carrier_btn = QPushButton("Browse Stego File")
        self.carrier_btn.clicked.connect(self.select_carrier_file)
        self.carrier_btn.setStyleSheet("""
            QPushButton {
                background-color: #202020;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 2px solid #ffcc00;
            }
        """)
        self.carrier_display = QLineEdit()
        self.carrier_display.setReadOnly(True)
        self.carrier_display.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 5px;
                padding: 6px;
            }
        """)

        grid.addWidget(carrier_label, 0, 0)
        grid.addWidget(self.carrier_display, 1, 0)
        grid.addWidget(self.carrier_btn, 2, 0)

        key_label = QLabel("Key File (Optional)")
        key_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.key_btn = QPushButton("Upload .key file")
        self.key_btn.clicked.connect(self.select_key_file)  # Connect to the updated method
        self.key_btn.setStyleSheet("""
            QPushButton {
                background-color: #202020;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 2px solid #ffcc00;
            }
        """)
        self.key_display = QLineEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 5px;
                padding: 6px;
            }
        """)

        grid.addWidget(key_label, 0, 1)
        grid.addWidget(self.key_display, 1, 1)
        grid.addWidget(self.key_btn, 2, 1)

        layout.addLayout(grid)

        password_layout = QVBoxLayout()
        self.password_label = QLabel("Password (Optional)")
        self.password_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        password_layout.addWidget(self.password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        button_row = QHBoxLayout()
        self.extract_btn = QPushButton("Extract")
        self.extract_btn.clicked.connect(self.handle_extract)  # Connect to the updated method
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #202020;
                color: white;
                border: 2px solid #ffaa00;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border: 2px solid #ffcc00;
            }
        """)
        button_row.addWidget(self.extract_btn)
        layout.addLayout(button_row)

        self.status_label = QLabel("Status:")
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFixedHeight(80)
        self.status_box.setStyleSheet(
            "background-color: #1e1e1e; color: white; border: 2px solid #ffaa00; border-radius: 5px; padding: 6px;")
        layout.addWidget(self.status_label)
        layout.addWidget(self.status_box)

        self.setLayout(layout)

    def select_carrier_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Stego File")
        if file_path:
            self.carrier_display.setText(file_path)

    def select_key_file(self):
        """
        Handles selecting and loading the key file, reading its content as bytes.
        """
        key_path, _ = QFileDialog.getOpenFileName(self, "Select Key File", filter="Key Files (*.key);;All Files (*)")
        if key_path:
            try:
                with open(key_path, 'rb') as f:  # <<< CRITICAL FIX: Read in BINARY mode
                    self.key_data_from_file = f.read()  # Store content as bytes
                self.key_display.setText(key_path)  # Display the path in the QLineEdit
                self.status_box.setText("Key file loaded successfully.")  # Update status
            except Exception as e:
                self.key_data_from_file = None  # Clear data on error
                self.key_display.clear()  # Clear path on error
                self.status_box.setText(f"Error loading key file: {e}")  # Update status

    def go_back(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'setCurrentIndex'):
                parent.setCurrentIndex(0)
                return
            parent = parent.parent()

    def reset_all(self):
        self.carrier_display.clear()
        self.key_display.clear()
        self.password_input.clear()
        self.status_box.clear()
        self.analysis_metadata = {}
        self.key_data_from_file = None  # <<< Reset the stored key data


    def handle_extract(self):
        path = self.carrier_display.text().strip()
        if not path or not os.path.exists(path):
            self.status_box.setText("Invalid stego file.")
            return

        password = self.password_input.text().strip()

        # We now pass the key_data_from_file (which is already bytes or None)
        key_data = self.key_data_from_file

        # Call the extract_payload from core.steg_engine
        result = extract_payload(path, password=password, key_data=key_data)

        if result["status"] == "success":
            self.status_box.setText("Extraction complete.\nSaved: " + result["output_file"])
        else:
            # Display a more user-friendly message, potentially linking to analysis
            error_message = result.get("message", "Unknown error during extraction.")
            # Add a hint if key file was required based on analysis
            if self.analysis_metadata.get('generate_key_used', False) and key_data is None:
                error_message += "\nHint: A key file was required but not provided."
            elif self.analysis_metadata.get('encryption') and self.analysis_metadata[
                'encryption'] != "None" and not password:
                error_message += "\nHint: This payload is encrypted and requires a password."

            self.status_box.setText(f"Extraction failed.\nReason: {error_message}")