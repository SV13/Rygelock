
# Entry point for Rygelock

import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.style_sheet import glass_style
from utils.resource_path import resource_path #delete

if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setStyleSheet(glass_style)

    window = MainWindow()
    window.show()

    for p in ["assets/audio/error.mp3", "assets/images/audio.png", "assets/images/disable.png", "assets/disable.png",
              "assets/audio.png"]:
        print("Exists:", p, os.path.exists(resource_path(p)))


    sys.exit(app.exec_())
