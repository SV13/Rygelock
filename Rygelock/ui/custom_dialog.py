# ui/custom_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class CustomDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.setWindowModality(Qt.ApplicationModal)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Message Label
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)

        # Button Box
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton("OK")
        ok_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        ok_button.setMinimumHeight(35)
        ok_button.setFixedWidth(120)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #ffaa00;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        button_layout.addStretch()

        main_layout.addWidget(self.message_label)
        main_layout.addLayout(button_layout)