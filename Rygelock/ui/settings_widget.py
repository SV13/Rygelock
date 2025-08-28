
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, QGroupBox, QHBoxLayout,
    QPushButton, QDialogButtonBox, QLabel, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal # Import pyqtSignal for custom signals

class SettingsWidget(QWidget):
    settings_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Audio Settings Group Box
        audio_group = QGroupBox("Audio Feedback")
        audio_layout = QHBoxLayout()
        self.audio_enabled = QCheckBox("Enable audio cues")
        self.audio_enabled.setChecked(True) # Default to enabled
        audio_layout.addWidget(self.audio_enabled)
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)

        # Process Priority Settings Group Box
        priority_group = QGroupBox("System Resources")
        priority_layout = QHBoxLayout()

        priority_label = QLabel("Process Priority:")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Normal", "Low", "High"])
        self.priority_combo.setToolTip(
            "Set the CPU priority for Rygelock.\n"
            "- Normal: Default for all applications.\n"
            "- Low: Slower, but won't slow down your other apps.\n"
            "- High: Fastest, but may make other apps sluggish."
        )

        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_combo)
        priority_group.setLayout(priority_layout)
        layout.addWidget(priority_group)

        # Add a stretchable space to push the buttons to the bottom
        layout.addStretch(1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # Connect the accepted (OK) signal to custom accept_settings method
        self.button_box.accepted.connect(self.accept_settings)
        # Connect the rejected (Cancel) signal to custom reject_settings method
        self.button_box.rejected.connect(self.reject_settings)


        layout.addWidget(self.button_box)


        self.setLayout(layout)

    def get_settings(self):
        """
        Retrieves the current state of the settings from the UI elements.
        """
        return {
            "audio_enabled": self.audio_enabled.isChecked(),
            "priority": self.priority_combo.currentText()
        }

    def accept_settings(self):

        print("Settings Accepted:", self.get_settings())
        self.settings_closed.emit() # Signal to parent that settings interaction is done

    def reject_settings(self):

        print("Settings Rejected. Changes not applied.")
        self.settings_closed.emit() # Signal to parent that settings interaction is done