#!/usr/bin/env python3
"""Nova Cathedral — Desktop Window (Qt5 WebEngine wrapper for nova_gui.html)."""
import sys
import os

os.environ.setdefault("DISPLAY", ":0")

from PyQt5.QtCore import QUrl, Qt, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QToolBar, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtGui import QIcon, QFont


class NovaCathedralWindow(QMainWindow):
    def __init__(self, url="http://localhost:5000"):
        super().__init__()
        self.setWindowTitle("Nova Cathedral · Harmonic Accord")
        self.resize(1400, 900)
        self._url = url

        # ── Web view ──────────────────────────────────────────────────────────
        self.browser = QWebEngineView()
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

        self.browser.setUrl(QUrl(url))
        self.setCentralWidget(self.browser)

        # ── Minimal toolbar ───────────────────────────────────────────────────
        tb = QToolBar("Nav", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        tb.setStyleSheet(
            "QToolBar { background: #0d1219; border-bottom: 1px solid #1e3a4a; padding: 2px 8px; }"
            "QToolButton { color: #4a7a8a; font-family: monospace; font-size: 11px;"
            "  padding: 4px 10px; border: none; }"
            "QToolButton:hover { color: #00c8ff; }"
            "QLabel { color: #00c8ff; font-family: monospace; font-size: 12px;"
            "  letter-spacing: 2px; padding: 0 8px; }"
        )
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        lbl = QLabel("NOVA · CATHEDRAL")
        tb.addWidget(lbl)
        tb.addSeparator()

        back = QAction("◂ Back", self)
        back.triggered.connect(self.browser.back)
        tb.addAction(back)

        fwd = QAction("Forward ▸", self)
        fwd.triggered.connect(self.browser.forward)
        tb.addAction(fwd)

        reload = QAction("⟳ Reload", self)
        reload.triggered.connect(self.browser.reload)
        tb.addAction(reload)

        home = QAction("⌂ Home", self)
        home.triggered.connect(lambda: self.browser.setUrl(QUrl(self._url)))
        tb.addAction(home)

        # Status bar
        self.statusBar().setStyleSheet(
            "QStatusBar { background: #080c10; color: #4a7a8a;"
            "  font-family: monospace; font-size: 10px; }"
        )
        self.statusBar().showMessage("Nova Cathedral · localhost:5000")
        self.browser.loadStarted.connect(
            lambda: self.statusBar().showMessage("Loading…"))
        self.browser.loadFinished.connect(
            lambda ok: self.statusBar().showMessage(
                "Nova Cathedral · localhost:5000" if ok else "Load failed"))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nova Cathedral")
    app.setApplicationDisplayName("Nova · Harmonic Accord")
    app.setFont(QFont("Exo 2", 10))

    win = NovaCathedralWindow("http://localhost:5000")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
