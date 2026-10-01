#!/usr/bin/env python3
"""
Downloadyha GUI Mockup (PyQt6 Example)

This is a minimal example showing how to integrate the Downloadyha branding
and assets into a PyQt6 desktop application.

Install dependencies:
    pip install PyQt6
"""

import sys
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout,
        QHBoxLayout, QLabel, QPushButton, QLineEdit,
        QProgressBar, QTextEdit, QListWidget, QSplitter
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon, QPixmap, QFont
except ImportError:
    print("PyQt6 not installed. Run: pip install PyQt6")
    sys.exit(1)


class DownloadyhaWindow(QMainWindow):
    """Main application window for Downloadyha GUI."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Downloadyha - YouTube Downloader")
        self.setGeometry(100, 100, 900, 600)

        # Set application icon if available
        icon_path = Path(__file__).parent.parent / "icons" / "app_icon_256.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header with logo/title
        header = self.create_header()
        layout.addWidget(header)

        # URL input section
        url_section = self.create_url_input()
        layout.addLayout(url_section)

        # Splitter for queue and log
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Download queue list
        queue_widget = self.create_queue_widget()
        splitter.addWidget(queue_widget)

        # Log/console output
        log_widget = self.create_log_widget()
        splitter.addWidget(log_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #9B51E0;
                border-radius: 8px;
                text-align: center;
                background-color: #2a2a2a;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D2FF, stop:0.5 #9B51E0, stop:1 #DC50FF);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)

        central_widget.setLayout(layout)

        # Apply dark theme stylesheet
        self.apply_stylesheet()

    def create_header(self) -> QWidget:
        """Create the header section with logo and title."""
        header = QWidget()
        header_layout = QHBoxLayout()

        # Title
        title = QLabel("Downloadyha")
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #00D2FF;")

        # Subtitle
        subtitle = QLabel("Fast & Beautiful YouTube Downloader")
        subtitle_font = QFont("Arial", 10)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet("color: #9B51E0;")

        # Layout
        text_layout = QVBoxLayout()
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        text_layout.setSpacing(0)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        header.setLayout(header_layout)
        return header

    def create_url_input(self) -> QHBoxLayout:
        """Create URL input section."""
        layout = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube video or playlist URL...")
        self.url_input.setMinimumHeight(40)
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #9B51E0;
                border-radius: 8px;
                background-color: #2a2a2a;
                color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #00D2FF;
            }
        """)

        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.setMinimumHeight(40)
        self.download_btn.setMinimumWidth(120)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D2FF, stop:1 #9B51E0);
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00E5FF, stop:1 #B060FF);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00A5BF, stop:1 #7B41C0);
            }
        """)

        layout.addWidget(self.url_input, stretch=4)
        layout.addWidget(self.download_btn, stretch=1)

        return layout

    def create_queue_widget(self) -> QWidget:
        """Create download queue list widget."""
        container = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Download Queue")
        label.setStyleSheet("color: #00D2FF; font-weight: bold; font-size: 13px;")

        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 2px solid #9B51E0;
                border-radius: 8px;
                color: white;
                padding: 8px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #9B51E0;
            }
        """)

        # Add sample items
        self.queue_list.addItem("📹 Sample Video 1.mp4 - 45.2 MB - [Ready]")
        self.queue_list.addItem("🎵 Sample Audio Track.mp3 - 8.5 MB - [Downloading...]")

        layout.addWidget(label)
        layout.addWidget(self.queue_list)
        container.setLayout(layout)

        return container

    def create_log_widget(self) -> QWidget:
        """Create log console widget."""
        container = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Console Log")
        label.setStyleSheet("color: #00D2FF; font-weight: bold; font-size: 13px;")

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                border: 2px solid #9B51E0;
                border-radius: 8px;
                color: #00FF00;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.log_text.setPlainText(
            "Downloadyha v1.0.0 initialized...\n"
            "Ready to download!\n"
            "Paste a YouTube URL and click Download."
        )

        layout.addWidget(label)
        layout.addWidget(self.log_text)
        container.setLayout(layout)

        return container

    def apply_stylesheet(self):
        """Apply global dark theme stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel {
                color: white;
            }
        """)


def main():
    """Launch the Downloadyha GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Downloadyha")
    app.setOrganizationName("Ahmed Tarek")

    window = DownloadyhaWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
