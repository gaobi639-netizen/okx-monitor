#!/usr/bin/env python3
"""OKX Copy Trading Monitor - Main entry point."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

from ui.main_window import MainWindow
from ui.styles import COLORS


def setup_dark_palette(app: QApplication) -> None:
    """Configure dark color palette for the application."""
    palette = QPalette()

    # Base colors
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['bg_primary']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['bg_secondary']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['bg_tertiary']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['bg_tertiary']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['bg_tertiary']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(COLORS['accent_red']))
    palette.setColor(QPalette.ColorRole.Link, QColor(COLORS['accent_blue']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent_blue']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))

    # Disabled colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(COLORS['text_tertiary']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(COLORS['text_tertiary']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(COLORS['text_tertiary']))

    app.setPalette(palette)


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("OKX Monitor")
    app.setOrganizationName("OKX Monitor")

    # Set Fusion style for consistent cross-platform appearance
    app.setStyle("Fusion")

    # Apply dark palette
    setup_dark_palette(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
