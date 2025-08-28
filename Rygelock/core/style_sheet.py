# core/style_sheet.py — Minimal futuristic dark theme stylesheet

glass_style = """
QMainWindow {
    background-color: #121212;
    color: white;
}

QPushButton {
    background-color: #202020;
    color: #ffffff;
    border: 2px solid #ffaa00;
    border-radius: 10px;
    padding: 10px 25px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #333333;
}

QLabel {
    color: white;
    font-size: 14px;
}

QLineEdit, QTextEdit {
    background-color: #1e1e1e;
    color: white;
    border: 1px solid #ffaa00;
    border-radius: 5px;
    padding: 5px;
}

QToolTip {
    background-color: #FFFFE0; /* A light yellow, easier on the eyes than pure white */
    color: black;             /* Black text for readability */
    border: 1px solid #ffaa00; /* A border that matches your theme */
    padding: 5px;             /* Some space around the text */
    border-radius: 3px;
}

"""

