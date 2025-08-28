# ui/main_window.py — Central GUI container for Rygelock (Refined header and hover underline effects with image-based speaker icons)
import psutil
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt, QSize

from ui.embed_widget import EmbedWidget
from ui.extract_widget import ExtractWidget
from ui.settings_widget import SettingsWidget
from ui.tutorial_widget import TutorialWidget
from utils.config import DEFAULT_CONFIG
from utils.audio import init_audio, play_sound
from utils.resource_path import resource_path
from utils.image_cache import ImageCache

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rygelock Steganography - By Sharveenn Murthi")
        self.setGeometry(100, 100, 1100, 750)
        self.setWindowIcon(QIcon(resource_path("assets/logo.png")))
        self.setStyleSheet("background-color: #121212; color: white;")

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        self.is_muted = False  # Track mute state
        self.config = DEFAULT_CONFIG.copy()

        # Initialize all UI menus and widgets.
        self.init_main_menu()
        self.init_embed_menu()
        self.init_extract_menu()
        self.init_settings_menu()

        self.apply_settings()

        # initialize the audio system.
        init_audio()

    def init_main_menu(self):
        main_menu = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(20, 20, 20, 10)

        logo_button = QPushButton()
        logo_button.setIcon(QIcon(resource_path("assets/logo.png")))
        logo_button.setIconSize(QSize(96, 96))
        logo_button.setFixedSize(104, 104)
        logo_button.setStyleSheet("background-color: transparent; border: none;")
        logo_button.clicked.connect(lambda: self.central_stack.setCurrentIndex(0))

        nav_button_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                border-bottom: 2px solid #ffaa00;
            }
        """

        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(nav_button_style)
        # connects to show the settings page in the stacked widget
        settings_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(3))


        self.mute_button = QPushButton()
        self.mute_button.setIcon(QIcon(resource_path("assets/audio.png")))
        self.mute_button.setIconSize(QSize(48, 48))
        self.mute_button.setFixedSize(64, 64)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #ffaa0022;
                border-radius: 8px;
            }
        """
        )
        self.mute_button.setToolTip("Audio Enabled")
        self.mute_button.clicked.connect(self.toggle_mute)

        header.addWidget(logo_button)
        header.addStretch()
        header.addWidget(settings_btn)
        header.addSpacing(20)
        header.addStretch()
        header.addWidget(self.mute_button)

        layout.addLayout(header)

        # Main Action Buttons
        body_layout = QVBoxLayout()
        body_layout.setAlignment(Qt.AlignCenter)

        button_style = """
            QPushButton {
                background-color: #202020;
                color: #ffffff;
                border: 2px solid #ffaa00;
                border-radius: 10px;
                padding: 14px 40px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """

        hide_btn = QPushButton("Hide Data")
        hide_btn.setStyleSheet(button_style)
        hide_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(1))

        unhide_btn = QPushButton("Unhide Data")
        unhide_btn.setStyleSheet(button_style)
        unhide_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(2))

        body_layout.addWidget(hide_btn)
        body_layout.addSpacing(20)
        body_layout.addWidget(unhide_btn)

        layout.addLayout(body_layout)

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(20, 10, 20, 20)

        tutorial_btn = QPushButton()
        tutorial_btn.setIcon(QIcon(resource_path("assets/tutorial.png")))
        tutorial_btn.setIconSize(QSize(48, 48))
        tutorial_btn.setFixedSize(56, 56)
        tutorial_btn.setStyleSheet("background-color: transparent; border: none;")
        tutorial_btn.setToolTip("How to use Rygelock")
        tutorial_btn.clicked.connect(self.show_tutorial)

        footer.addWidget(tutorial_btn)
        footer.addStretch()

        layout.addLayout(footer)

        main_menu.setLayout(layout)
        # Add main_menu to the stack at index 0
        self.central_stack.addWidget(main_menu)

    def show_tutorial(self):
        tutorial_dialog = TutorialWidget(self)
        tutorial_dialog.exec_() # Use exec_() to show it as a modal dialog

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        icon_path = resource_path("assets/disable.png") if self.is_muted else resource_path("assets/audio.png")
        tooltip_text = "Audio Muted" if self.is_muted else "Audio Enabled"
        self.mute_button.setIcon(QIcon(icon_path))
        self.mute_button.setToolTip("Audio Muted" if self.is_muted else "Audio Enabled")
        self.config["audio_enabled"] = not self.config.get("audio_enabled", True)
        self.apply_settings()  # Re-apply settings to update the icon

    def init_embed_menu(self):
        self.embed_widget = EmbedWidget(config=self.config, parent=self)
        self.embed_widget.back_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(0))
        self.central_stack.addWidget(self.embed_widget)

    def init_extract_menu(self):
        self.extract_widget = ExtractWidget(config=self.config, parent=self)
        self.extract_widget.back_btn.clicked.connect(lambda: self.central_stack.setCurrentIndex(0))
        self.central_stack.addWidget(self.extract_widget)

    def init_settings_menu(self):
        self.settings_widget = SettingsWidget()
        # Connect the settings_closed signal to our new method
        self.settings_widget.settings_closed.connect(self.return_to_main_menu_from_settings)
        # Add settings_widget to the stack at index 3
        self.central_stack.addWidget(self.settings_widget)

        # Apply Process Priority
        try:
            p = psutil.Process(os.getpid())  # Get the current application's process
            priority_setting = self.config.get("priority", "Normal").lower()

            if priority_setting == "high":
                p.nice(psutil.HIGH_PRIORITY_CLASS)
                print("[Settings] Process priority set to High.")
            elif priority_setting == "low":
                p.nice(psutil.LOW_PRIORITY_CLASS)
                print("[Settings] Process priority set to Low.")
            else:  # Default to Normal
                p.nice(psutil.NORMAL_PRIORITY_CLASS)
                print("[Settings] Process priority set to Normal.")
        except Exception as e:
            print(f"[ERROR] Could not set process priority: {e}")

        if hasattr(self, 'settings_widget'):
            self.settings_widget.audio_enabled.setChecked(self.config.get("audio_enabled", True))

            # Set the dropdown to the currently saved priority
            priority_text = self.config.get("priority", "Normal")
            index = self.settings_widget.priority_combo.findText(priority_text, Qt.MatchFixedString)
            if index >= 0:
                self.settings_widget.priority_combo.setCurrentIndex(index)

    def apply_settings(self):
        #Applies the current settings from the self.config dictionary.
        # Apply Process Priority
        try:
            p = psutil.Process(os.getpid())
            priority_setting = self.config.get("priority", "Normal").lower()

            if priority_setting == "high":
                p.nice(psutil.HIGH_PRIORITY_CLASS)
                print("[Settings] Process priority set to High.")
            elif priority_setting == "low":
                p.nice(psutil.IDLE_PRIORITY_CLASS)
                print("[Settings] Process priority set to Low.")
            else:
                p.nice(psutil.NORMAL_PRIORITY_CLASS)
                print("[Settings] Process priority set to Normal.")
        except Exception as e:
            print(f"[ERROR] Could not set process priority: {e}")

        # Apply audio setting
        self.is_muted = not self.config.get("audio_enabled", True)
        icon_rel = "assets/disable.png" if self.is_muted else "assets/audio.png"
        icon_path = resource_path(icon_rel)
        tooltip_text = "Audio Muted" if self.is_muted else "Audio Enabled"
        if hasattr(self, 'mute_button'):
            self.mute_button.setIcon(QIcon(icon_path))
            self.mute_button.setToolTip(tooltip_text)

        # Update the checkboxes in the settings widget to reflect the loaded config
        if hasattr(self, 'settings_widget'):
            self.settings_widget.audio_enabled.setChecked(self.config.get("audio_enabled", True))
            priority_text = self.config.get("priority", "Normal")
            index = self.settings_widget.priority_combo.findText(priority_text, Qt.MatchFixedString)
            if index >= 0:
                self.settings_widget.priority_combo.setCurrentIndex(index)

    def return_to_main_menu_from_settings(self):
        """
        Slot called when settings are closed. It now reads and applies the new settings.
        """
        print("Returning to main menu from settings.")

        new_settings = self.settings_widget.get_settings()
        self.config.update(new_settings)
        self.apply_settings()
        self.apply_settings()

        self.central_stack.setCurrentIndex(0)