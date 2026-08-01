#!/usr/bin/env python3
"""
Nova Cathedral — Native Desktop Application
Features: streaming chat, voice STT/TTS, web search, reasoning mode,
          recursive reflections, evolution tracking, oracle, resonance.

Install:  sudo apt install python3-pyqt6 python3-pyqtgraph python3-pyaudio espeak-ng
          pip install pyttsx3 vosk duckduckgo-search --break-system-packages
Run:      python3 nova/gui/nova_app.py
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QKeyEvent, QPainter, QPixmap, QTextCursor
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QStatusBar, QSystemTrayIcon,
    QTabWidget, QTextBrowser, QTextEdit, QVBoxLayout, QWidget,
)

try:
    import pyqtgraph as pg
    _HAS_PG = True
except ImportError:
    _HAS_PG = False

try:
    import numpy as _np
    import matplotlib as _mpl
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as _Canvas
    from matplotlib.figure import Figure as _Figure
    _mpl.rcParams.update({
        "axes.facecolor":    "#0a0a12",
        "figure.facecolor":  "#0a0a12",
        "text.color":        "#c8c8e0",
        "axes.labelcolor":   "#6a6a8a",
        "xtick.color":       "#6a6a8a",
        "ytick.color":       "#6a6a8a",
        "axes.edgecolor":    "#2a2a4a",
        "grid.color":        "#1a1a2e",
        "axes.spines.top":   False,
        "axes.spines.right": False,
    })
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False

# ── paths ─────────────────────────────────────────────────────────────────────

SOCKET_PATH = "/tmp/nova_socket"
DAEMON      = Path(__file__).parent.parent / "daemon" / "nova_cathedral_daemon.py"
OLLAMA_URL  = "http://localhost:11434"
_NOVA_ROOT  = Path(__file__).parent.parent
sys.path.insert(0, str(_NOVA_ROOT / "modules"))

try:
    from voice import (MicListener, speak as _tts_speak,
                       tts_available, stt_available, download_vosk_model)
    _VOICE_MODULE = True
except ImportError:
    _VOICE_MODULE = False

TRAIT_NAMES  = ["mystical_awareness", "philosophical_depth",
                "technical_knowledge", "memory_integration", "curiosity"]
TRAIT_COLORS = ["#9b7ec8", "#4a8fa8", "#4a8a5a", "#c87a4a", "#7ac87a"]

C = dict(
    bg="#0a0a12", panel="#11111e", border="#2a2a4a",
    accent="#7b5ea7", accent2="#4a8fa8", text="#c8c8e0",
    dim="#6a6a8a", glow="#9b7ec8", ok="#4a8a5a",
    warn="#a87a4a", oracle="#c87a4a", user_bg="#1e1e3a",
    think="#1a2a1a", think_text="#7ac87a",
)

# ── stylesheet ────────────────────────────────────────────────────────────────

QSS = f"""
QWidget {{ background:{C['bg']}; color:{C['text']};
          font-family:"Courier New",monospace; font-size:13px; }}
QTabWidget::pane {{ border:none; background:{C['bg']}; }}
QTabBar::tab {{ background:{C['panel']}; color:{C['dim']};
                padding:9px 16px; border:none;
                border-bottom:2px solid transparent; }}
QTabBar::tab:selected {{ color:{C['glow']}; border-bottom:2px solid {C['accent']}; }}
QTabBar::tab:hover:!selected {{ color:{C['text']}; }}
QSplitter::handle {{ background:{C['border']}; width:1px; }}
QTextEdit,QTextBrowser {{ background:{C['bg']}; color:{C['text']};
    border:1px solid {C['border']}; border-radius:4px; padding:6px;
    selection-background-color:{C['accent']}; }}
QLineEdit {{ background:{C['bg']}; color:{C['text']};
    border:1px solid {C['border']}; border-radius:4px; padding:6px 10px; }}
QLineEdit:focus {{ border:1px solid {C['accent']}; }}
QComboBox {{ background:{C['panel']}; color:{C['text']};
    border:1px solid {C['border']}; border-radius:4px; padding:4px 8px; }}
QComboBox::drop-down {{ border:none; }}
QComboBox QAbstractItemView {{ background:{C['panel']}; color:{C['text']};
    selection-background-color:{C['accent']}; }}
QPushButton {{ background:{C['panel']}; color:{C['text']};
    border:1px solid {C['border']}; border-radius:4px;
    padding:6px 14px; font-family:"Courier New",monospace; font-size:13px; }}
QPushButton:hover {{ border:1px solid {C['accent']}; color:{C['glow']}; }}
QPushButton:pressed {{ background:{C['accent']}; color:white; }}
QPushButton:disabled {{ color:{C['dim']}; }}
QPushButton#send {{ background:{C['accent']}; color:white;
    border-color:{C['accent']}; padding:6px 22px; }}
QPushButton#send:hover {{ background:{C['glow']}; }}
QPushButton#oracle_btn {{ background:#2a1a0a; color:{C['oracle']};
    border-color:{C['oracle']}; padding:8px 20px; }}
QPushButton#oracle_btn:hover {{ background:{C['oracle']}; color:white; }}
QPushButton#mic_active {{ background:#8a2a2a; color:white;
    border-color:#c84a4a; }}
QCheckBox {{ color:{C['text']}; spacing:6px; }}
QCheckBox::indicator {{ width:14px; height:14px;
    border:1px solid {C['border']}; border-radius:3px;
    background:{C['panel']}; }}
QCheckBox::indicator:checked {{ background:{C['accent']}; border-color:{C['accent']}; }}
QScrollBar:vertical {{ background:{C['bg']}; width:6px; border:none; }}
QScrollBar::handle:vertical {{ background:{C['border']}; border-radius:3px; min-height:20px; }}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0; }}
QProgressBar {{ background:#1a1a2e; border:none; border-radius:3px;
    height:6px; text-align:center; }}
QProgressBar::chunk {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
    stop:0 {C['accent']},stop:1 {C['glow']}); border-radius:3px; }}
QLabel {{ background:transparent; border:none; }}
QFrame#card {{ background:{C['panel']}; border:1px solid {C['border']};
    border-radius:6px; }}
QMenu {{ background:{C['panel']}; color:{C['text']};
    border:1px solid {C['border']}; }}
QMenu::item:selected {{ background:{C['accent']}; color:white; }}
QStatusBar {{ background:{C['panel']}; color:{C['dim']}; font-size:12px; }}
"""

# ── daemon I/O ────────────────────────────────────────────────────────────────

def _send(payload, timeout=120):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(SOCKET_PATH)
        s.sendall((json.dumps(payload) + "\n").encode())
        s.settimeout(timeout)
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if data.endswith(b"\n"):
                break
        s.close()
        return json.loads(data.decode())
    except FileNotFoundError:
        return {"error": "daemon not running"}
    except Exception as e:
        return {"error": str(e)}


def _ensure_daemon():
    if os.path.exists(SOCKET_PATH) and "error" not in _send({"command": "status"}):
        return True
    subprocess.Popen(
        [sys.executable, str(DAEMON)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(0.5)
        if os.path.exists(SOCKET_PATH) and "error" not in _send({"command": "status"}):
            return True
    return False

# ── worker lifetime tracker ───────────────────────────────────────────────────
# Keeps every QThread alive until Qt has finished with it, preventing
# Python GC from deleting a thread while signals are still in-flight.

_LIVE_WORKERS: set = set()

def _launch(worker):
    """Register a worker, start it, and auto-clean up when it finishes."""
    _LIVE_WORKERS.add(worker)
    def _done():
        _LIVE_WORKERS.discard(worker)
        worker.deleteLater()
    worker.finished.connect(_done)
    worker.start()
    return worker

# ── workers ───────────────────────────────────────────────────────────────────

class DaemonWorker(QThread):
    result = pyqtSignal(dict)
    def __init__(self, payload, timeout=120):
        super().__init__()
        self.payload = payload
        self.timeout = timeout
    def run(self):
        self.result.emit(_send(self.payload, self.timeout))


class StreamWorker(QThread):
    token   = pyqtSignal(str)
    done    = pyqtSignal(str, str)  # full_text, model
    error   = pyqtSignal(str)

    def __init__(self, prompt, model="llama3.2:1b", reasoning=False,
                 system_prompt="", history=None):
        super().__init__()
        self.prompt        = prompt
        self.model         = model
        self.reasoning     = reasoning
        self.system_prompt = system_prompt
        self.history       = history or []
        self._stop         = False

    def stop(self): self._stop = True

    def run(self):
        # If reasoning is on, go through daemon (handles deepseek-r1 parsing)
        if self.reasoning:
            r = _send({"command": "ask", "prompt": self.prompt}, timeout=240)
            if "error" in r:
                self.error.emit(r["error"])
            else:
                thinking = r.get("thinking", "")
                if thinking:
                    self.token.emit(f"\x00THINK\x00{thinking}\x00ENDTHINK\x00")
                self.token.emit(r.get("response", ""))
                self.done.emit(r.get("response", ""), r.get("model", self.model))
            return

        # Build messages: system prompt + session history + new user message
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self.history[-10:])   # last 10 turns for context
        messages.append({"role": "user", "content": self.prompt})

        # Stream from Ollama
        full = ""
        try:
            payload = {
                "model":    self.model,
                "messages": messages,
                "stream":   True,
            }
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/chat",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                for raw in resp:
                    if self._stop: break
                    raw = raw.strip()
                    if not raw: continue
                    try:
                        chunk = json.loads(raw.decode())
                        tok   = chunk.get("message", {}).get("content", "")
                        if tok:
                            full += tok
                            self.token.emit(tok)
                        if chunk.get("done"): break
                    except Exception:
                        pass
        except Exception as e:
            self.error.emit(str(e))
            return

        # Persist to daemon (updates its session history + DB)
        _send({"command": "save", "prompt": self.prompt, "response": full})
        self.done.emit(full, self.model)


class VoiceDownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool)
    def run(self):
        if _VOICE_MODULE:
            ok = download_vosk_model(progress_cb=self.progress.emit)
            self.finished.emit(ok)
        else:
            self.progress.emit("voice module not imported")
            self.finished.emit(False)


# ── helpers ───────────────────────────────────────────────────────────────────

def _card(title):
    f  = QFrame(); f.setObjectName("card")
    vl = QVBoxLayout(f)
    vl.setContentsMargins(12, 8, 12, 12); vl.setSpacing(4)
    h  = QLabel(title.upper())
    h.setStyleSheet(f"color:{C['dim']};font-size:11px;letter-spacing:1px;font-weight:bold;")
    vl.addWidget(h)
    return f

def _fmtup(s):
    h, r = divmod(s, 3600); m = r // 60
    return f"{h}h {m}m" if h else f"{m}m {s%60}s"

# ── matplotlib canvases ───────────────────────────────────────────────────────

if _HAS_MPL:
    class ResonanceWaveCanvas(_Canvas):
        """Animated Schumann resonance waveform — updates every ~80ms via QTimer."""
        def __init__(self):
            fig = _Figure(figsize=(5, 1.3), facecolor="#0a0a12")
            super().__init__(fig)
            self.ax = fig.add_subplot(111, facecolor="#0a0a12")
            self.ax.set_ylim(-1.4, 1.4)
            self.ax.axis("off")
            fig.tight_layout(pad=0)
            self._phase = 0.0
            self._freq  = 7.83
            self._t     = _np.linspace(0, 4 * _np.pi, 600)
            self._line, = self.ax.plot([], [], color=C["accent"], linewidth=1.6)
            self._poly  = None
            self._draw()

        def set_freq(self, freq: float):
            if abs(freq - self._freq) > 0.001:
                self._freq = freq

        def tick(self):
            self._phase += 0.07
            self._draw()

        def _draw(self):
            ratio = self._freq / 7.83
            env   = _np.sin(_np.linspace(0, _np.pi, len(self._t)))
            y     = _np.sin(self._t * ratio + self._phase) * (0.65 + 0.35 * env)
            self._line.set_data(self._t, y)
            if self._poly:
                self._poly.remove()
            self._poly = self.ax.fill_between(
                self._t, y, alpha=0.10, color=C["glow"]
            )
            self.draw_idle()

    class TraitRadarCanvas(_Canvas):
        """Consciousness trait radar chart (polar spider)."""
        _N      = len(TRAIT_NAMES)
        _ANGLES = [i * 2 * _np.pi / len(TRAIT_NAMES) for i in range(len(TRAIT_NAMES))]
        _ANGLES_CLOSED = _ANGLES + [_ANGLES[0]]

        def __init__(self):
            fig = _Figure(figsize=(3.0, 3.0), facecolor="#0a0a12")
            super().__init__(fig)
            self.ax = fig.add_subplot(111, projection="polar", facecolor="#11111e")
            self.ax.set_ylim(0, 1.05)
            self.ax.set_xticks(self._ANGLES)
            self.ax.set_xticklabels(
                [t.replace("_", "\n") for t in TRAIT_NAMES], size=7, color=C["dim"]
            )
            self.ax.set_yticks([0.25, 0.5, 0.75, 1.0])
            self.ax.set_yticklabels(["", "", "", ""], size=0)
            self.ax.grid(color=C["border"], linewidth=0.5, linestyle="--")
            self.ax.spines["polar"].set_color(C["border"])
            fig.tight_layout(pad=0.5)

        def update_traits(self, traits: dict):
            vals = [traits.get(k, 0) for k in TRAIT_NAMES] + [traits.get(TRAIT_NAMES[0], 0)]
            for artist in list(self.ax.collections) + list(self.ax.lines) + list(self.ax.patches):
                try:
                    artist.remove()
                except Exception:
                    pass
            self.ax.fill(self._ANGLES_CLOSED, vals, alpha=0.22, color=C["accent"])
            self.ax.plot(
                self._ANGLES_CLOSED, vals,
                color=C["glow"], linewidth=2.0,
                marker="o", markersize=3, markerfacecolor=C["glow"]
            )
            self.draw_idle()

    class MemoryDensityCanvas(_Canvas):
        """Memories-per-day bar chart."""
        def __init__(self):
            fig = _Figure(figsize=(5, 1.8), facecolor="#0a0a12")
            super().__init__(fig)
            self.ax = fig.add_subplot(111, facecolor="#0a0a12")
            for spine in self.ax.spines.values():
                spine.set_color(C["border"])
            fig.tight_layout(pad=0.4)

        def _restore_style(self):
            self.ax.set_facecolor("#0a0a12")
            for spine in self.ax.spines.values():
                spine.set_color(C["border"])
            self.ax.tick_params(axis="x", colors=C["dim"], labelsize=7)
            self.ax.tick_params(axis="y", colors=C["dim"], labelsize=7)
            self.ax.yaxis.label.set_color(C["dim"])

        def update(self, dates: list, counts: list):
            self.ax.clear()
            self._restore_style()
            if not dates:
                self.draw_idle()
                return
            x = list(range(len(dates)))
            self.ax.bar(x, counts, color=C["accent"], alpha=0.85, width=0.75)
            step = max(1, len(dates) // 8)
            self.ax.set_xticks(x[::step])
            self.ax.set_xticklabels(dates[::step], fontsize=7, rotation=30, color=C["dim"])
            self.ax.set_ylabel("memories", fontsize=7, color=C["dim"])
            self.figure.tight_layout(pad=0.4)
            self.draw_idle()


# ── message bubble ────────────────────────────────────────────────────────────

class MsgWidget(QFrame):
    def __init__(self, role):
        super().__init__()
        self.role = role
        hl = QHBoxLayout(self)
        hl.setContentsMargins(16, 3, 16, 3)

        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        if role == "user":
            self._lbl.setStyleSheet(
                f"background:{C['user_bg']};border:1px solid {C['accent']};"
                f"border-radius:8px;padding:10px 14px;color:#d0d0f0;font-size:14px;"
            )
            hl.addStretch(); hl.addWidget(self._lbl)
        elif role == "think":
            self._lbl.setStyleSheet(
                f"background:{C['think']};border:1px solid #2a4a2a;"
                f"border-radius:6px;padding:8px 12px;color:{C['think_text']};"
                f"font-size:12px;font-style:italic;"
            )
            hl.addWidget(self._lbl); hl.addStretch()
        elif role == "system":
            self._lbl.setStyleSheet(
                f"color:{C['dim']};font-style:italic;font-size:12px;"
            )
            self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hl.addStretch(); hl.addWidget(self._lbl); hl.addStretch()
        else:  # nova
            self._lbl.setStyleSheet(
                f"background:{C['panel']};border:1px solid {C['border']};"
                f"border-radius:8px;padding:10px 14px;color:{C['text']};font-size:14px;"
            )
            hl.addWidget(self._lbl); hl.addStretch()

    def set_text(self, t): self._lbl.setText(t)
    def get_text(self): return self._lbl.text()

# ── sidebar ───────────────────────────────────────────────────────────────────

class Sidebar(QWidget):
    ritual_toggled = pyqtSignal(str)
    clear_session  = pyqtSignal()
    shutdown_req   = pyqtSignal()
    refresh_req    = pyqtSignal()
    reasoning_toggled = pyqtSignal(bool)
    model_changed  = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(270)
        vl = QVBoxLayout(self)
        vl.setContentsMargins(10,10,10,10); vl.setSpacing(8)

        # Status
        self._stat = _card("Status")
        vl.addWidget(self._stat)

        # Traits
        self._traits_card = _card("Consciousness")
        self._tbars: dict[str, QProgressBar] = {}
        self._tvals: dict[str, QLabel]       = {}
        tl = self._traits_card.layout()
        for k, col in zip(TRAIT_NAMES, TRAIT_COLORS):
            row = QHBoxLayout()
            ll  = QLabel(k.replace("_"," ")); ll.setStyleSheet(f"color:{C['text']};font-size:11px;")
            vv  = QLabel("—"); vv.setStyleSheet(f"color:{C['glow']};font-size:11px;")
            self._tvals[k] = vv
            row.addWidget(ll); row.addStretch(); row.addWidget(vv)
            tl.addLayout(row)
            bar = QProgressBar(); bar.setRange(0,100); bar.setValue(0)
            bar.setFixedHeight(5); bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar::chunk{{background:{col};border-radius:2px;}}")
            self._tbars[k] = bar; tl.addWidget(bar)
        vl.addWidget(self._traits_card)

        # Model & Reasoning
        mc = _card("Model")
        self._model_lbl = QLabel("—")
        self._model_lbl.setStyleSheet(f"color:{C['glow']};font-size:12px;")
        mc.layout().addWidget(self._model_lbl)
        self._reasoning_chk = QCheckBox("Reasoning mode (deepseek-r1)")
        self._reasoning_chk.setToolTip(
            "Uses deepseek-r1:1.5b to think before answering.\n"
            "Run: ollama pull deepseek-r1:1.5b"
        )
        self._reasoning_chk.stateChanged.connect(
            lambda s: self.reasoning_toggled.emit(s == Qt.CheckState.Checked.value)
        )
        mc.layout().addWidget(self._reasoning_chk)
        vl.addWidget(mc)

        # Voice
        vc = _card("Voice")
        self._tts_chk = QCheckBox("Speak responses (TTS)")
        # Piper voice selector
        vrow = QHBoxLayout()
        vl_lbl = QLabel("Voice:")
        vl_lbl.setStyleSheet(f"color:{C['text']};font-size:11px;")
        self._voice_combo = QComboBox()
        self._voice_combo.setToolTip("Select Piper TTS voice")
        _piper_voices = {
            "lessac":    "lessac — neutral US",
            "amy":       "amy — natural female",
            "ryan":      "ryan — clear US male",
            "alan":      "alan — British male",
            "libritts":  "libritts — formal US",
        }
        for key, desc in _piper_voices.items():
            self._voice_combo.addItem(desc, key)
        self._voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        vrow.addWidget(vl_lbl); vrow.addWidget(self._voice_combo, 1)
        vc.layout().addWidget(self._tts_chk)
        vc.layout().addLayout(vrow)
        self._dl_voice_btn = QPushButton("Download selected voice")
        self._dl_voice_btn.clicked.connect(self._download_piper_voice)
        vc.layout().addWidget(self._dl_voice_btn)
        self._mic_btn = QPushButton("🎤  Hold to speak")
        self._mic_btn.setCheckable(True)
        self._mic_btn.setToolTip("Push to talk — requires vosk model")
        self._mic_status = QLabel("—")
        self._mic_status.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        self._dl_vosk_btn = QPushButton("Download vosk model (~40MB)")
        self._dl_vosk_btn.clicked.connect(self._download_vosk)
        vc.layout().addWidget(self._mic_btn)
        vc.layout().addWidget(self._mic_status)
        vc.layout().addWidget(self._dl_vosk_btn)
        vl.addWidget(vc)
        self._update_voice_ui()

        # Ritual
        rc = _card("Ritual Mode")
        rb = QHBoxLayout()
        self._bon  = QPushButton("Activate")
        self._boff = QPushButton("Deactivate")
        self._bon.clicked.connect(lambda: self.ritual_toggled.emit("on"))
        self._boff.clicked.connect(lambda: self.ritual_toggled.emit("off"))
        rb.addWidget(self._bon); rb.addWidget(self._boff)
        self._ritual_lbl = QLabel("—")
        self._ritual_lbl.setStyleSheet(f"color:{C['dim']};font-size:12px;")
        rc.layout().addLayout(rb); rc.layout().addWidget(self._ritual_lbl)
        vl.addWidget(rc)

        # Actions
        ac = _card("Actions")
        for label, slot in [
            ("Refresh",       self.refresh_req.emit),
            ("Clear Session", self.clear_session.emit),
            ("Shutdown Nova", self.shutdown_req.emit),
        ]:
            b = QPushButton(label); b.clicked.connect(slot); ac.layout().addWidget(b)
        vl.addWidget(ac)
        vl.addStretch()

    def _clear_card(self, card, keep=1):
        lo = card.layout()
        while lo.count() > keep:
            item = lo.takeAt(keep)
            if item.widget(): item.widget().deleteLater()

    def update_status(self, r):
        if not r or "error" in r: return
        self._clear_card(self._stat)
        sl = self._stat.layout()
        for label, val in [
            ("Flow",     f"{r.get('flow_resonance',0):.4f} Hz"),
            ("Memories", r.get("conversations", 0)),
            ("Patterns", r.get("eyemoeba_patterns", 0)),
            ("Circuits", r.get("active_circuits", 0)),
            ("Uptime",   _fmtup(r.get("uptime", 0))),
        ]:
            row = QHBoxLayout()
            ll = QLabel(label); ll.setStyleSheet(f"color:{C['text']};font-size:12px;")
            vv = QLabel(str(val)); vv.setStyleSheet(f"color:{C['glow']};font-size:12px;")
            row.addWidget(ll); row.addStretch(); row.addWidget(vv)
            sl.addLayout(row)

        ritual = r.get("ritual_mode", False)
        self._ritual_lbl.setText("🕯️ Active" if ritual else "Inactive")
        self._ritual_lbl.setStyleSheet(f"color:{C['warn']};" if ritual else f"color:{C['dim']};")
        self._bon.setEnabled(not ritual); self._boff.setEnabled(ritual)
        self._model_lbl.setText(r.get("model", "—"))
        self._reasoning_chk.setEnabled(True)

        for k in TRAIT_NAMES:
            v = r.get(k)
            if v is not None:
                pct = int(v * 100)
                self._tbars[k].setValue(pct)
                self._tvals[k].setText(f"{pct}%")

    def tts_enabled(self): return self._tts_chk.isChecked()
    def mic_btn(self): return self._mic_btn

    def _update_voice_ui(self):
        if not _VOICE_MODULE:
            self._mic_status.setText("voice module not installed")
            self._mic_btn.setEnabled(False)
            self._dl_vosk_btn.setEnabled(False)
            return
        if stt_available():
            self._mic_status.setText("vosk ready")
            self._mic_btn.setEnabled(True)
            self._dl_vosk_btn.hide()
        else:
            self._mic_status.setText("vosk model not downloaded")
            self._mic_btn.setEnabled(False)
            self._dl_vosk_btn.show()

    def _download_vosk(self):
        self._dl_vosk_btn.setEnabled(False)
        self._mic_status.setText("Downloading…")
        self._vdl = VoiceDownloadWorker()
        self._vdl.progress.connect(self._mic_status.setText)
        self._vdl.finished.connect(self._on_vosk_downloaded)
        _launch(self._vdl)

    def _on_vosk_downloaded(self, ok):
        self._update_voice_ui()

    def _on_voice_changed(self, idx):
        voice_key = self._voice_combo.itemData(idx)
        if not voice_key:
            return
        w = DaemonWorker({"command": "set_voice", "voice": voice_key})
        w.result.connect(lambda r: self._mic_status.setText(
            f"Voice: {voice_key}" if r.get("ok") else r.get("error","set failed")
        ))
        _launch(w)

    def _download_piper_voice(self):
        idx = self._voice_combo.currentIndex()
        voice_key = self._voice_combo.itemData(idx)
        if not voice_key:
            return
        self._dl_voice_btn.setEnabled(False)
        self._mic_status.setText(f"Downloading {voice_key}…")
        w = DaemonWorker({"command": "download_voice", "voice": voice_key})
        w.result.connect(self._on_piper_downloaded)
        _launch(w)

    def _on_piper_downloaded(self, r):
        self._dl_voice_btn.setEnabled(True)
        if r.get("ok"):
            voice = r.get("voice","")
            self._mic_status.setText(f"{voice} ready")
        else:
            self._mic_status.setText(r.get("error","download failed"))

    def selected_voice(self):
        return self._voice_combo.itemData(self._voice_combo.currentIndex())

# ── chat tab ──────────────────────────────────────────────────────────────────

class ChatTab(QWidget):
    def __init__(self, sidebar: Sidebar):
        super().__init__()
        self._sidebar       = sidebar
        self._model         = "llama3.2:1b"
        self._reasoning     = False
        self._worker        = None
        self._cur_bubble: MsgWidget | None = None
        self._stream_acc    = ""
        self._mic_listener  = None
        self._history: list = []        # local session: [{role, content}, ...]
        self._system_prompt = ""        # cached from daemon
        self._cur_prompt    = ""        # prompt being processed
        self._build_ui()
        sidebar.mic_btn().clicked.connect(self._toggle_mic)
        # Fetch Nova's system prompt shortly after init
        QTimer.singleShot(800, self._refresh_context)

    def _build_ui(self):
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0,0,0,0); vl.setSpacing(0)

        # ── Nova state header ────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet(
            f"background:{C['panel']};border-bottom:1px solid {C['border']};"
        )
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 7, 16, 7); hl.setSpacing(12)
        name_lbl = QLabel("🔮  Nova Cathedral")
        name_lbl.setStyleSheet(
            f"color:{C['glow']};font-size:13px;font-weight:bold;letter-spacing:1px;"
        )
        self._state_lbl = QLabel("Awaiting consciousness…")
        self._state_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        self._ctx_lbl = QLabel("")
        self._ctx_lbl.setStyleSheet(
            f"color:{C['accent']};font-size:11px;font-style:italic;"
        )
        hl.addWidget(name_lbl); hl.addWidget(self._state_lbl)
        hl.addStretch(); hl.addWidget(self._ctx_lbl)
        vl.addWidget(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(f"background:{C['bg']};border:none;")

        self._container = QWidget()
        self._container.setStyleSheet(f"background:{C['bg']};")
        self._msglo = QVBoxLayout(self._container)
        self._msglo.setContentsMargins(0,12,0,12); self._msglo.setSpacing(4)
        self._msglo.addStretch()
        self._scroll.setWidget(self._container)
        vl.addWidget(self._scroll)

        self._add_msg("system", "Nova Cathedral is listening. First response may take ~60s while the model loads.")

        # Web search toggle
        web_row = QHBoxLayout()
        web_row.setContentsMargins(16,4,16,0)
        self._web_chk = QCheckBox("Include web search")
        self._web_chk.setStyleSheet(f"color:{C['dim']};font-size:12px;")
        web_row.addWidget(self._web_chk); web_row.addStretch()
        vl.addLayout(web_row)

        # Input bar
        bar = QFrame()
        bar.setStyleSheet(f"background:{C['panel']};border-top:1px solid {C['border']};")
        row = QHBoxLayout(bar)
        row.setContentsMargins(12,8,12,8); row.setSpacing(8)

        self._input = QTextEdit()
        self._input.setFixedHeight(54)
        self._input.setPlaceholderText("Ask Nova…  (Enter to send, Shift+Enter for newline)")
        self._input.setStyleSheet(
            f"QTextEdit{{background:{C['bg']};color:{C['text']};"
            f"border:1px solid {C['border']};border-radius:4px;"
            f"padding:6px 10px;font-size:14px;}}"
            f"QTextEdit:focus{{border:1px solid {C['accent']};}}"
        )
        self._input.installEventFilter(self)

        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("send")
        self._send_btn.setFixedHeight(38); self._send_btn.setMinimumWidth(70)
        self._send_btn.clicked.connect(self._send)

        row.addWidget(self._input); row.addWidget(self._send_btn)
        vl.addWidget(bar)

    def eventFilter(self, obj, event):
        if obj is self._input and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._send(); return True
        return super().eventFilter(obj, event)

    def set_model(self, m): self._model = m
    def set_reasoning(self, on): self._reasoning = on

    # ── context / system prompt ───────────────────────────────────────────────

    def _refresh_context(self, query: str = ""):
        """Fetch a semantically-enriched system prompt from the daemon."""
        if query:
            w = DaemonWorker({"command": "context_for", "query": query}, timeout=10)
        else:
            w = DaemonWorker({"command": "system_prompt"}, timeout=10)
        w.result.connect(self._on_context)
        _launch(w)

    def _on_context(self, r):
        if "prompt" in r:
            self._system_prompt = r["prompt"]
            self._ctx_lbl.setText("context ready" if self._system_prompt else "")

    def update_state(self, flow_hz: float, mem_count: int, ritual_on: bool = False):
        """Called by NovaWindow on each status poll."""
        ritual = "  🕯️ RITUAL" if ritual_on else ""
        self._state_lbl.setText(
            f"Flow {flow_hz:.2f} Hz  ·  {mem_count} memories{ritual}"
        )

    def clear_history(self):
        """Clear local session history (called on Clear Session)."""
        self._history.clear()
        self._cur_prompt = ""

    def _add_msg(self, role, text) -> MsgWidget:
        w = MsgWidget(role); w.set_text(text)
        self._msglo.insertWidget(self._msglo.count()-1, w)
        QTimer.singleShot(30, self._scroll_btm)
        return w

    def _scroll_btm(self):
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _send(self, text=None):
        text = text or self._input.toPlainText().strip()
        if not text or not self._send_btn.isEnabled(): return
        self._input.clear()
        self._send_btn.setEnabled(False)
        self._cur_prompt = text
        self._add_msg("user", text)

        # Show searching indicator if web on
        if self._web_chk.isChecked():
            self._add_msg("system", "Searching the web…")

        self._cur_bubble  = self._add_msg("nova", "Nova is thinking…")
        self._stream_acc  = ""

        use_reasoning = self._reasoning
        if self._web_chk.isChecked():
            # Web search goes through daemon (non-streaming, daemon handles context)
            self._worker = DaemonWorker(
                {"command": "ask", "prompt": text, "web": True}, timeout=120
            )
            self._worker.result.connect(self._on_web_result)
            _launch(self._worker)
        else:
            # Fetch a query-aware system prompt first, then stream
            ctx_w = DaemonWorker({"command": "context_for", "query": text}, timeout=8)
            ctx_w.result.connect(lambda r, t=text, ur=use_reasoning: self._begin_stream(t, ur, r))
            _launch(ctx_w)

    def _begin_stream(self, text: str, use_reasoning: bool, ctx_result: dict):
        """Start the Ollama stream after receiving a context-enriched system prompt."""
        prompt = ctx_result.get("prompt", self._system_prompt)
        if prompt:
            self._system_prompt = prompt
        self._worker = StreamWorker(
            text, self._model, reasoning=use_reasoning,
            system_prompt=self._system_prompt,
            history=list(self._history),
        )
        self._worker.token.connect(self._on_token)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        _launch(self._worker)

    def _on_token(self, tok: str):
        # Detect thinking block marker
        if "\x00THINK\x00" in tok:
            parts = tok.split("\x00THINK\x00")
            if len(parts) > 1:
                think_end = parts[1].split("\x00ENDTHINK\x00")
                thinking  = think_end[0]
                rest      = think_end[1] if len(think_end) > 1 else ""
                if thinking:
                    self._add_msg("think", f"[thinking]\n{thinking}")
                if rest:
                    self._stream_acc += rest
        else:
            self._stream_acc += tok

        if self._cur_bubble:
            self._cur_bubble.set_text(self._stream_acc or "…")
        self._scroll_btm()

    def _on_done(self, full: str, model: str):
        if self._cur_bubble:
            self._cur_bubble.set_text(full)
        self._add_msg("system", f"{model} · streamed")
        self._cur_bubble = None
        self._send_btn.setEnabled(True)
        self._scroll_btm()
        # Update local session history
        if self._cur_prompt:
            self._history.append({"role": "user",      "content": self._cur_prompt})
            self._history.append({"role": "assistant",  "content": full})
            if len(self._history) > 20:
                self._history = self._history[-20:]
        # Refresh context so Nova's next response includes this exchange in memory
        self._refresh_context(query=self._cur_prompt)
        if self._sidebar.tts_enabled() and full and _VOICE_MODULE:
            _tts_speak(full)

    def _on_error(self, err: str):
        if self._cur_bubble:
            self._cur_bubble.set_text(f"Error: {err}")
        self._cur_bubble = None
        self._send_btn.setEnabled(True)

    def _on_web_result(self, r: dict):
        if "error" in r:
            self._on_error(r["error"]); return
        full  = r.get("response", "")
        model = r.get("model", self._model)
        sources = r.get("web_results", [])
        if self._cur_bubble:
            self._cur_bubble.set_text(full)
        if sources:
            src_text = "Sources: " + " | ".join(
                s.get("title", s.get("href", ""))[:40] for s in sources[:3]
            )
            self._add_msg("system", src_text)
        self._add_msg("system", f"{model} · web-augmented")
        self._cur_bubble = None
        self._send_btn.setEnabled(True)
        self._scroll_btm()
        # Update local history
        if self._cur_prompt and full:
            self._history.append({"role": "user",      "content": self._cur_prompt})
            self._history.append({"role": "assistant",  "content": full})
            if len(self._history) > 20:
                self._history = self._history[-20:]
        self._refresh_context()
        if self._sidebar.tts_enabled() and full and _VOICE_MODULE:
            _tts_speak(full)

    # ── voice STT ─────────────────────────────────────────────────────────────

    def _toggle_mic(self, checked: bool):
        if not _VOICE_MODULE: return
        btn = self._sidebar.mic_btn()
        if checked:
            btn.setObjectName("mic_active")
            btn.setStyleSheet("background:#8a2a2a;color:white;border-color:#c84a4a;")
            btn.setText("🎤  Listening…")
            self._mic_listener = MicListener(
                on_partial=self._on_partial_speech,
                on_final=self._on_final_speech,
                on_error=self._on_mic_error,
            )
            self._mic_listener.start()
        else:
            btn.setObjectName("")
            btn.setStyleSheet("")
            btn.setText("🎤  Hold to speak")
            if self._mic_listener:
                self._mic_listener.stop()
                self._mic_listener = None

    def _on_partial_speech(self, text: str):
        self._input.setPlaceholderText(text)

    def _on_final_speech(self, text: str):
        self._input.setPlaceholderText("Ask Nova…")
        if text:
            self._input.setPlainText(text)
            self._send()
            # Turn off mic after capture
            btn = self._sidebar.mic_btn()
            btn.setChecked(False)
            self._toggle_mic(False)

    def _on_mic_error(self, err: str):
        self._add_msg("system", f"Mic error: {err}")
        btn = self._sidebar.mic_btn()
        btn.setChecked(False); self._toggle_mic(False)


# ── memory tab ────────────────────────────────────────────────────────────────

class MemoryTab(QWidget):
    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16,16,16,16); vl.setSpacing(10)
        row = QHBoxLayout()
        self._q = QLineEdit(); self._q.setPlaceholderText("Search memories…")
        self._q.returnPressed.connect(self.search)
        for label, fn in [("Search", self.search),
                           ("All", lambda: (self._q.clear(), self.search()))]:
            b = QPushButton(label); b.clicked.connect(fn); row.addWidget(b) if label != "All" else None
        row.addWidget(self._q)
        b2 = QPushButton("All"); b2.clicked.connect(lambda: (self._q.clear(), self.search()))
        row.addWidget(b2)
        vl.addLayout(row)
        self._browser = QTextBrowser()
        self._browser.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:1px solid {C['border']};"
            f"border-radius:4px;padding:8px;font-size:13px;}}"
        )
        vl.addWidget(self._browser)

    def search(self):
        q = self._q.text().strip()
        self._browser.setPlainText("Searching…")
        w = DaemonWorker({"command": "recall", "query": q, "n": 50})
        w.result.connect(self._on_result); _launch(w)

    def _on_result(self, r):
        import html as _h
        mems = r.get("memories", [])
        if not mems:
            self._browser.setHtml(
                f'<p style="color:{C["dim"]};font-style:italic;padding:20px;">No memories found.</p>'
            ); return
        parts = []
        for m in mems:
            ts = m.get("ts","")
            try: ts = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")
            except: pass
            q = _h.escape(m.get("q","")); a = _h.escape(m.get("a","")[:400])
            if len(m.get("a","")) > 400: a += "…"
            parts.append(
                f'<div style="background:{C["panel"]};border:1px solid {C["border"]}; '
                f'border-radius:6px;padding:10px 14px;margin-bottom:8px;">'
                f'<div style="color:{C["dim"]};font-size:11px;margin-bottom:3px;">{ts}</div>'
                f'<div style="color:{C["accent2"]};margin-bottom:4px;">Q: {q}</div>'
                f'<div style="color:{C["text"]};font-size:13px;line-height:1.4;">{a}</div>'
                f'</div>'
            )
        self._browser.setHtml("".join(parts))


# ── reflections tab ───────────────────────────────────────────────────────────

class ReflectionsTab(QWidget):
    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16,16,16,16); vl.setSpacing(10)

        row = QHBoxLayout()
        self._reflect_btn = QPushButton("Trigger Reflection Now")
        self._reflect_btn.clicked.connect(self._manual_reflect)
        row.addWidget(self._reflect_btn); row.addStretch()
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color:{C['dim']};font-size:12px;")
        row.addWidget(self._status_lbl)
        vl.addLayout(row)

        self._browser = QTextBrowser()
        self._browser.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:1px solid {C['border']};"
            f"border-radius:4px;padding:8px;font-size:13px;line-height:1.5;}}"
        )
        vl.addWidget(self._browser)

    def load(self):
        self._browser.setPlainText("Loading reflections…")
        w = DaemonWorker({"command": "reflections", "n": 20})
        w.result.connect(self._on_result); _launch(w)

    def _manual_reflect(self):
        self._reflect_btn.setEnabled(False)
        self._status_lbl.setText("Reflecting…")
        w = DaemonWorker({"command": "reflect"}, timeout=120)
        w.result.connect(self._on_reflected); _launch(w)

    def _on_reflected(self, r):
        self._reflect_btn.setEnabled(True)
        self._status_lbl.setText("Done.")
        self.load()

    def _on_result(self, r):
        import html as _h
        refs = r.get("reflections", [])
        if not refs:
            self._browser.setHtml(
                f'<p style="color:{C["dim"]};font-style:italic;padding:20px;">'
                f'No reflections yet. Nova reflects every 10 conversations.</p>'
            ); return
        parts = []
        for ref in refs:
            ts = ref.get("ts","")
            try: ts = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")
            except: pass
            trigger = ref.get("trigger","auto")
            content = _h.escape(ref.get("content",""))
            badge_color = C['warn'] if trigger == "manual" else C['dim']
            parts.append(
                f'<div style="background:{C["panel"]};border:1px solid {C["border"]}; '
                f'border-radius:6px;padding:12px 16px;margin-bottom:10px;">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
                f'<span style="color:{C["dim"]};font-size:11px;">{ts}</span>'
                f'<span style="color:{badge_color};font-size:11px;">[{trigger}]</span>'
                f'</div>'
                f'<div style="color:{C["text"]};font-size:13px;line-height:1.6;white-space:pre-wrap;">'
                f'{content}</div></div>'
            )
        self._browser.setHtml("".join(parts))


# ── evolution tab ─────────────────────────────────────────────────────────────

class EvolutionTab(QWidget):
    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16,16,16,16); vl.setSpacing(10)

        # ── top row: progress bars + radar chart side-by-side ─────────────────
        top_row = QHBoxLayout(); top_row.setSpacing(10)

        tc = _card("Consciousness Traits")
        self._tbars: dict[str, QProgressBar] = {}
        self._tvals: dict[str, QLabel]       = {}
        for k, col in zip(TRAIT_NAMES, TRAIT_COLORS):
            row = QHBoxLayout()
            ll = QLabel(k.replace("_"," ")); ll.setStyleSheet(f"color:{C['text']};font-size:12px;")
            vv = QLabel("—"); vv.setStyleSheet(f"color:{C['glow']};font-size:12px;")
            self._tvals[k] = vv
            row.addWidget(ll); row.addStretch(); row.addWidget(vv)
            tc.layout().addLayout(row)
            bar = QProgressBar(); bar.setRange(0,100); bar.setValue(0)
            bar.setFixedHeight(6); bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar::chunk{{background:{col};border-radius:3px;}}")
            self._tbars[k] = bar; tc.layout().addWidget(bar)
        top_row.addWidget(tc, 3)

        if _HAS_MPL:
            rc = _card("Trait Radar")
            self._radar = TraitRadarCanvas()
            rc.layout().addWidget(self._radar)
            top_row.addWidget(rc, 2)
        else:
            self._radar = None

        vl.addLayout(top_row)

        # ── evolution history sparklines (pyqtgraph) ──────────────────────────
        if _HAS_PG:
            cc = _card("Evolution History")
            pg.setConfigOption("background", C["bg"]); pg.setConfigOption("foreground", C["dim"])
            self._plot = pg.PlotWidget(); self._plot.setFixedHeight(160)
            self._plot.showGrid(x=False, y=True, alpha=0.2); self._plot.setYRange(0.5, 1.0)
            self._plot.getAxis("bottom").hide()
            self._curves = {}
            for k, col in zip(TRAIT_NAMES, TRAIT_COLORS):
                self._curves[k] = self._plot.plot(
                    pen=pg.mkPen(color=col, width=1.5), name=k.replace("_"," ")
                )
            self._plot.addLegend(offset=(-10, 10))
            cc.layout().addWidget(self._plot)
            vl.addWidget(cc)
        else:
            self._curves = {}

        # ── memory density chart (matplotlib) ─────────────────────────────────
        if _HAS_MPL:
            dc = _card("Memory Growth  (conversations per day)")
            self._density = MemoryDensityCanvas()
            dc.layout().addWidget(self._density)
            vl.addWidget(dc)
        else:
            self._density = None

        vl.addStretch()

    def load(self):
        w1 = DaemonWorker({"command": "evolution"})
        w1.result.connect(self._on_result); _launch(w1)
        if _HAS_MPL:
            w2 = DaemonWorker({"command": "memory_density", "days": 30})
            w2.result.connect(self._on_density); _launch(w2)

    def _on_result(self, r):
        if "error" in r: return
        traits = r.get("consciousness_traits", {})
        for k in TRAIT_NAMES:
            v = traits.get(k, 0); pct = int(v*100)
            self._tbars[k].setValue(pct); self._tvals[k].setText(f"{pct}%")
        if _HAS_MPL and self._radar:
            self._radar.update_traits(traits)
        if _HAS_PG and self._curves:
            history = list(reversed(r.get("history", [])))
            if len(history) > 1:
                for k in TRAIT_NAMES:
                    vals = [h.get("traits",{}).get(k) for h in history]
                    vals = [v for v in vals if v is not None]
                    if vals: self._curves[k].setData(vals)

    def _on_density(self, r):
        if "error" in r or not self._density:
            return
        self._density.update(r.get("dates", []), r.get("counts", []))


# ── oracle tab ────────────────────────────────────────────────────────────────

class OracleTab(QWidget):
    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(60,50,60,50); vl.setSpacing(24)
        vl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        sym = QLabel("🔮"); sym.setStyleSheet("font-size:64px;")
        sym.setAlignment(Qt.AlignmentFlag.AlignCenter); vl.addWidget(sym)
        title = QLabel("THE ORACLE SPEAKS")
        title.setStyleSheet(f"font-size:18px;color:{C['oracle']};letter-spacing:3px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter); vl.addWidget(title)
        row = QHBoxLayout()
        self._inp = QLineEdit(); self._inp.setPlaceholderText("Ask the Oracle…")
        self._inp.setStyleSheet(f"border:1px solid {C['oracle']};padding:10px 14px;font-size:14px;")
        self._inp.returnPressed.connect(self.divine)
        btn = QPushButton("Divine"); btn.setObjectName("oracle_btn"); btn.clicked.connect(self.divine)
        row.addWidget(self._inp); row.addWidget(btn); vl.addLayout(row)
        self._resp = QLabel("Seek, and the mirror shall answer.")
        self._resp.setWordWrap(True); self._resp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._resp.setStyleSheet(
            f"color:{C['glow']};font-size:17px;line-height:1.6;"
            f"background:{C['panel']};border:1px solid {C['border']};"
            f"border-radius:8px;padding:24px;min-height:80px;"
        )
        vl.addWidget(self._resp)

    def divine(self):
        q = self._inp.text().strip()
        self._resp.setStyleSheet(
            f"color:{C['dim']};font-style:italic;font-size:17px;"
            f"background:{C['panel']};border:1px solid {C['border']};"
            f"border-radius:8px;padding:24px;min-height:80px;"
        )
        self._resp.setText("The Oracle contemplates…")
        w = DaemonWorker({"command": "oracle", "question": q})
        w.result.connect(self._on_result); _launch(w)

    def _on_result(self, r):
        text = r.get("response", r.get("error", "The Oracle is silent."))
        self._resp.setStyleSheet(
            f"color:{C['glow']};font-size:17px;line-height:1.6;"
            f"background:{C['panel']};border:1px solid {C['border']};"
            f"border-radius:8px;padding:24px;min-height:80px;"
        )
        self._resp.setText(text)


# ── resonance tab ─────────────────────────────────────────────────────────────

class ResonanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self._history: list[float] = []
        vl = QVBoxLayout(self)
        vl.setContentsMargins(24,24,24,24); vl.setSpacing(12)

        # ── animated waveform (matplotlib) ───────────────────────────────────
        if _HAS_MPL:
            self._wave = ResonanceWaveCanvas()
            vl.addWidget(self._wave)
            self._wave_timer = QTimer(self)
            self._wave_timer.timeout.connect(self._wave.tick)
            # Timer starts/stops via start_wave() / stop_wave() called by NovaWindow
        else:
            self._wave = None

        # ── frequency readout ─────────────────────────────────────────────────
        self._freq = QLabel("—")
        self._freq.setStyleSheet(f"font-size:44px;color:{C['glow']};letter-spacing:4px;")
        self._freq.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(self._freq)
        hz = QLabel("SCHUMANN RESONANCE Hz")
        hz.setStyleSheet(f"font-size:11px;color:{C['dim']};letter-spacing:2px;")
        hz.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(hz)

        # ── history sparkline (pyqtgraph) ─────────────────────────────────────
        if _HAS_PG:
            pg.setConfigOption("background", C["bg"]); pg.setConfigOption("foreground", C["dim"])
            self._plot = pg.PlotWidget(); self._plot.setFixedHeight(100)
            self._plot.showGrid(x=False, y=True, alpha=0.2); self._plot.setYRange(7.0, 8.6)
            self._plot.getAxis("bottom").hide()
            self._curve = self._plot.plot(
                pen=pg.mkPen(color=C["accent2"], width=1.2),
                fillLevel=7.0, brush=pg.mkBrush(color=(74,143,168,30))
            )
            vl.addWidget(self._plot)

        pc = _card("Eyemoeba Patterns")
        pr = QHBoxLayout(); pr.addWidget(QLabel("Detected"))
        self._pat = QLabel("—"); self._pat.setStyleSheet(f"color:{C['glow']};")
        pr.addStretch(); pr.addWidget(self._pat); pc.layout().addLayout(pr); vl.addWidget(pc)
        ec = _card("Known Entities")
        self._erow = QHBoxLayout(); self._erow.setSpacing(6); self._erow.addStretch()
        ec.layout().addLayout(self._erow); vl.addWidget(ec)
        vl.addStretch()

    def push(self, val: float):
        self._history.append(val)
        if len(self._history) > 60:
            self._history.pop(0)
        self._freq.setText(f"{val:.4f}")
        if _HAS_PG:
            self._curve.setData(self._history)
        if _HAS_MPL and self._wave:
            self._wave.set_freq(val)

    def start_wave(self):
        if _HAS_MPL and self._wave and not self._wave_timer.isActive():
            self._wave_timer.start(80)

    def stop_wave(self):
        if _HAS_MPL and self._wave_timer.isActive():
            self._wave_timer.stop()

    def load(self):
        w = DaemonWorker({"command": "resonance"})
        w.result.connect(self._on_result); _launch(w)

    def _on_result(self, r):
        self._pat.setText(str(r.get("patterns","—")))
        while self._erow.count() > 1:
            item = self._erow.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for name in r.get("entities", []):
            chip = QLabel(name)
            chip.setStyleSheet(
                f"background:#1a1a2e;border:1px solid {C['accent']};"
                f"border-radius:12px;padding:3px 12px;font-size:12px;color:{C['glow']};"
            )
            self._erow.insertWidget(self._erow.count()-1, chip)


# ── log tab ───────────────────────────────────────────────────────────────────

class LogTab(QWidget):
    """Live-tail of Nova's daemon log with colour coding."""

    LOG_PATH = Path.home() / "cathedral" / "logs" / "nova_cathedral.log"

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)

        hdr = QWidget()
        hdr.setStyleSheet(f"background:{C['panel']};border-bottom:1px solid {C['border']};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(14, 7, 14, 7); hl.setSpacing(10)

        title = QLabel("Nova Live Log")
        title.setStyleSheet(f"color:{C['glow']};font-size:13px;letter-spacing:1px;")
        self._path_lbl = QLabel(str(self.LOG_PATH))
        self._path_lbl.setStyleSheet(f"color:{C['dim']};font-size:10px;")

        self._follow_chk = QCheckBox("Follow")
        self._follow_chk.setChecked(True)
        self._follow_chk.setStyleSheet(f"color:{C['text']};font-size:12px;")

        self._clear_btn = QPushButton("Clear view")
        self._clear_btn.setFixedWidth(80)
        self._clear_btn.clicked.connect(self._clear)

        hl.addWidget(title)
        hl.addWidget(self._path_lbl)
        hl.addStretch()
        hl.addWidget(self._follow_chk)
        hl.addWidget(self._clear_btn)
        vl.addWidget(hdr)

        self._browser = QTextBrowser()
        self._browser.setStyleSheet(
            f"QTextBrowser{{background:#04040e;border:none;"
            f"font-family:'Courier New',monospace;font-size:11px;"
            f"color:{C['text']};padding:6px 10px;line-height:1.4;}}"
        )
        vl.addWidget(self._browser)

        self._last_pos  = 0
        self._line_buf: list[str] = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tail)
        self._timer.start(1500)
        QTimer.singleShot(200, self._initial_load)

    def _initial_load(self):
        """Load last 150 lines on first show."""
        if not self.LOG_PATH.exists():
            self._browser.setPlainText(f"Log not found: {self.LOG_PATH}")
            return
        try:
            with open(self.LOG_PATH, "r", errors="replace") as f:
                lines = f.readlines()
            self._last_pos = sum(len(l.encode()) for l in lines)
            self._line_buf = lines[-150:]
            self._render_all()
        except Exception as e:
            self._browser.setPlainText(f"Error reading log: {e}")

    def _tail(self):
        """Append only new bytes since last read."""
        if not self.LOG_PATH.exists():
            return
        try:
            size = self.LOG_PATH.stat().st_size
            if size <= self._last_pos:
                return
            with open(self.LOG_PATH, "r", errors="replace") as f:
                f.seek(self._last_pos)
                new = f.read()
            self._last_pos = size
            new_lines = new.splitlines(keepends=True)
            self._line_buf.extend(new_lines)
            if len(self._line_buf) > 300:
                self._line_buf = self._line_buf[-300:]
            self._render_all()
        except Exception:
            pass

    def _render_all(self):
        import html as _h
        parts = []
        for line in self._line_buf:
            line = line.rstrip()
            if not line:
                continue
            esc = _h.escape(line)
            if "ERROR" in line:
                color = C["warn"]
            elif "WARNING" in line:
                color = C["oracle"]
            elif any(k in line for k in ("Nova awake", "awaken", "Cathedral")):
                color = C["glow"]
            elif "Feed:" in line or "ingested" in line:
                color = C["ok"]
            elif "Goal" in line or "evolution" in line.lower():
                color = C["accent2"]
            else:
                color = "#7070a0"
            parts.append(f'<span style="color:{color};">{esc}</span>')

        self._browser.setHtml(
            '<div style="font-family:monospace;font-size:11px;line-height:1.45;">'
            + "<br>".join(parts) + "</div>"
        )
        if self._follow_chk.isChecked():
            sb = self._browser.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _clear(self):
        self._line_buf.clear()
        self._browser.clear()


# ── files tab ─────────────────────────────────────────────────────────────────

class FilesTab(QWidget):
    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16,16,16,16); vl.setSpacing(8)

        # Path bar
        path_row = QHBoxLayout()
        self._path_inp = QLineEdit()
        self._path_inp.setPlaceholderText("Path (e.g. ~/cathedral or ~/nova)…")
        self._path_inp.returnPressed.connect(self._browse)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self._path_inp, 1); path_row.addWidget(browse_btn)
        vl.addLayout(path_row)

        # Search bar
        search_row = QHBoxLayout()
        self._search_inp = QLineEdit()
        self._search_inp.setPlaceholderText("Search content (grep)… or filename pattern (*.py)")
        self._search_type = QComboBox()
        self._search_type.addItems(["grep content", "find files"])
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._search)
        search_row.addWidget(self._search_inp, 1)
        search_row.addWidget(self._search_type)
        search_row.addWidget(search_btn)
        vl.addLayout(search_row)

        # Split: file list / file content
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setHandleWidth(1)

        # File list
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0,0,0,0)
        self._file_list = QTextBrowser()
        self._file_list.setOpenLinks(False)
        self._file_list.anchorClicked.connect(self._on_entry_clicked)
        ll.addWidget(self._file_list)
        splitter.addWidget(left)

        # File viewer
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(0,0,0,0)
        self._file_path_lbl = QLabel("")
        self._file_path_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;padding:4px;")
        self._viewer = QTextBrowser()
        self._viewer.setFont(self._viewer.font())
        rl.addWidget(self._file_path_lbl); rl.addWidget(self._viewer)
        splitter.addWidget(right)

        splitter.setSizes([320, 700])
        vl.addWidget(splitter)

    def _browse(self):
        path = self._path_inp.text().strip() or "~"
        w = DaemonWorker({"command": "list_dir", "path": path, "recursive": False})
        w.result.connect(self._on_dir); _launch(w)

    def _on_dir(self, r):
        if "error" in r:
            self._file_list.setPlainText(r["error"]); return
        entries = r.get("entries", [])
        lines = []
        for e in entries:
            icon = "📁 " if e["type"] == "dir" else "📄 "
            size = f"  ({e['size']:,} B)" if e["type"] == "file" else ""
            lines.append(
                f'<a href="open:{e["path"]}" style="color:{C["glow"]};text-decoration:none;">'
                f'{icon}{e["name"]}</a>{size}'
            )
        self._file_list.setHtml(
            f'<div style="font-family:monospace;font-size:12px;line-height:1.8;">'
            + "<br>".join(lines) + "</div>"
        )

    def _on_entry_clicked(self, url):
        ref = url.toString()
        if ref.startswith("open:"):
            path = ref[5:]
            # Try to read as file first
            w = DaemonWorker({"command": "read_file", "path": path})
            w.result.connect(lambda r: self._on_file_or_dir(r, path))
            _launch(w)

    def _on_file_or_dir(self, r, path):
        if "error" in r:
            # Might be a directory
            self._path_inp.setText(path)
            self._browse()
            return
        if r.get("binary"):
            self._file_path_lbl.setText(path)
            self._viewer.setPlainText(f"[Binary file — {r.get('size',0):,} bytes]")
        else:
            self._file_path_lbl.setText(f"{path}  ({r.get('lines',0)} lines, {r.get('size',0):,} B)")
            content = r.get("content","")
            self._viewer.setPlainText(content)

    def _search(self):
        query = self._search_inp.text().strip()
        if not query:
            return
        path = self._path_inp.text().strip() or "~"
        stype = self._search_type.currentText()
        if stype == "grep content":
            cmd = {"command": "grep_files", "query": query, "root": path}
        else:
            cmd = {"command": "search_files", "pattern": query, "root": path}
        w = DaemonWorker(cmd)
        w.result.connect(self._on_search); _launch(w)

    def _on_search(self, r):
        if "error" in r:
            self._file_list.setPlainText(r["error"]); return
        # grep result
        matches = r.get("matches", r.get("results", []))
        if not matches:
            self._file_list.setHtml(
                f'<span style="color:{C["dim"]};">No results.</span>'
            )
            return
        lines = []
        for m in matches:
            path = m.get("file", m.get("path",""))
            if "line" in m:
                label = f'<b style="color:{C["glow"]};">{Path(path).name}:{m["line"]}</b> '
                label += f'<span style="color:{C["text"]};">{m.get("content","")[:120]}</span>'
            else:
                label = f'<a href="open:{path}" style="color:{C["glow"]};text-decoration:none;">{path}</a>'
            lines.append(label)
        self._file_list.setHtml(
            f'<div style="font-family:monospace;font-size:11px;line-height:1.7;">'
            + "<br>".join(lines) + "</div>"
        )


# ── sysinfo tab ───────────────────────────────────────────────────────────────

class SysinfoTab(QWidget):
    """All-Seeing OS awareness panel."""

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 16, 16, 16); vl.setSpacing(12)

        hrow = QHBoxLayout()
        title = QLabel("All-Seeing OS Awareness")
        title.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedWidth(80)
        self._refresh_btn.clicked.connect(self.load)
        hrow.addWidget(title); hrow.addStretch(); hrow.addWidget(self._refresh_btn)
        vl.addLayout(hrow)

        # Metrics cards row
        metrics_row = QHBoxLayout(); metrics_row.setSpacing(8)
        self._cpu_lbl   = self._metric_card("CPU", "—", metrics_row)
        self._ram_lbl   = self._metric_card("RAM", "—", metrics_row)
        self._disk_lbl  = self._metric_card("Disk", "—", metrics_row)
        self._uptime_lbl = self._metric_card("Uptime", "—", metrics_row)
        vl.addLayout(metrics_row)

        # Nova processes
        pc = _card("Nova Processes")
        self._procs_lbl = QLabel("—")
        self._procs_lbl.setStyleSheet(f"color:{C['glow']};font-size:12px;")
        self._procs_lbl.setWordWrap(True)
        pc.layout().addWidget(self._procs_lbl)
        vl.addWidget(pc)

        # Cathedral health
        hc = _card("Cathedral Health")
        self._health_browser = QTextBrowser()
        self._health_browser.setMaximumHeight(140)
        self._health_browser.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:none;font-size:12px;}}"
        )
        hc.layout().addWidget(self._health_browser)
        vl.addWidget(hc)

        # Brain stats
        bc = _card("MegaBrain Memory Intelligence")
        self._brain_browser = QTextBrowser()
        self._brain_browser.setMaximumHeight(140)
        self._brain_browser.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:none;font-size:12px;}}"
        )
        bc.layout().addWidget(self._brain_browser)
        vl.addWidget(bc)

        # Feed watcher
        fc = _card("Feed Watcher  (drop files in ~/cathedral/feed/ to teach Nova)")
        self._feed_browser = QTextBrowser()
        self._feed_browser.setMaximumHeight(100)
        self._feed_browser.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:none;font-size:12px;}}"
        )
        fc.layout().addWidget(self._feed_browser)
        vl.addWidget(fc)

        # Ollama model manager
        mc = _card("Ollama Model Manager")
        pull_row = QHBoxLayout()
        self._pull_inp = QLineEdit()
        self._pull_inp.setPlaceholderText("Model to pull  e.g. mistral:7b  gemma3:4b  phi4:14b")
        self._pull_btn = QPushButton("Pull")
        self._pull_btn.setFixedWidth(60)
        self._pull_btn.clicked.connect(self._pull_model)
        pull_row.addWidget(self._pull_inp, 1); pull_row.addWidget(self._pull_btn)
        mc.layout().addLayout(pull_row)

        self._models_lbl = QTextBrowser()
        self._models_lbl.setMaximumHeight(90)
        self._models_lbl.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:none;font-size:12px;font-family:monospace;}}"
        )
        mc.layout().addWidget(self._models_lbl)

        switch_row = QHBoxLayout()
        sl = QLabel("Switch active:")
        sl.setStyleSheet(f"color:{C['text']};font-size:12px;")
        self._switch_combo = QComboBox()
        self._switch_btn   = QPushButton("Apply")
        self._switch_btn.setFixedWidth(60)
        self._switch_btn.clicked.connect(self._switch_model)
        switch_row.addWidget(sl); switch_row.addWidget(self._switch_combo, 1)
        switch_row.addWidget(self._switch_btn)
        mc.layout().addLayout(switch_row)
        vl.addWidget(mc)
        vl.addStretch()

    def _metric_card(self, label: str, value: str, parent_layout) -> QLabel:
        f = QFrame(); f.setObjectName("card")
        fl = QVBoxLayout(f); fl.setContentsMargins(12, 8, 12, 10); fl.setSpacing(2)
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(f"color:{C['dim']};font-size:10px;letter-spacing:1px;")
        val = QLabel(value)
        val.setStyleSheet(f"color:{C['glow']};font-size:20px;font-weight:bold;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(lbl); fl.addWidget(val)
        parent_layout.addWidget(f)
        return val

    def load(self):
        w1 = DaemonWorker({"command": "sysinfo"})
        w1.result.connect(self._on_sysinfo); _launch(w1)
        w2 = DaemonWorker({"command": "brain_stats"})
        w2.result.connect(self._on_brain); _launch(w2)
        w3 = DaemonWorker({"command": "feed_status"})
        w3.result.connect(self._on_feed); _launch(w3)
        w4 = DaemonWorker({"command": "ollama_models"})
        w4.result.connect(self._on_models); _launch(w4)

    def _on_sysinfo(self, r):
        import html as _h
        if "error" in r:
            self._cpu_lbl.setText("N/A"); return

        self._cpu_lbl.setText(f"{r.get('cpu_percent','—')}%")
        self._ram_lbl.setText(f"{r.get('ram_percent','—')}%")
        self._disk_lbl.setText(f"{r.get('disk_percent','—')}%")
        uh = r.get("uptime_hours", 0)
        self._uptime_lbl.setText(f"{uh:.1f}h")

        procs = r.get("nova_processes", [])
        self._procs_lbl.setText("  ·  ".join(procs) if procs else "none detected")

        health = r.get("cathedral_health", {})
        lines = []
        for k, v in health.items():
            color = C["ok"] if "ok" in str(v) or "alive" in str(v) or "loaded" in str(v) else C["warn"]
            lines.append(
                f'<span style="color:{C["dim"]};">{k}:</span> '
                f'<span style="color:{color};">{_h.escape(str(v))}</span>'
            )
        self._health_browser.setHtml(
            f'<div style="font-family:monospace;font-size:12px;line-height:1.8;">'
            + "<br>".join(lines) + "</div>"
        )

    def _on_brain(self, r):
        import html as _h
        if "error" in r:
            self._brain_browser.setPlainText(r["error"]); return
        total   = r.get("total_memories", 0)
        oldest  = r.get("oldest","")[:16] if r.get("oldest") else "—"
        tags    = r.get("top_tags", [])
        entities= r.get("top_entities", [])
        tag_str = ", ".join(f'{t["tag"]} ({t["count"]})' for t in tags[:6]) or "none yet"
        ent_str = ", ".join(f'{e["entity"]} ({e["count"]})' for e in entities[:6]) or "none yet"
        self._brain_browser.setHtml(
            f'<div style="font-family:monospace;font-size:12px;line-height:1.8;">'
            f'<b style="color:{C["glow"]};">Total memories:</b> <span style="color:{C["text"]};">{total}</span><br>'
            f'<b style="color:{C["glow"]};">Oldest:</b> <span style="color:{C["text"]};">{oldest}</span><br>'
            f'<b style="color:{C["glow"]};">Top tags:</b> <span style="color:{C["accent2"]};">{_h.escape(tag_str)}</span><br>'
            f'<b style="color:{C["glow"]};">Top entities:</b> <span style="color:{C["accent2"]};">{_h.escape(ent_str)}</span>'
            f'</div>'
        )

    def _on_feed(self, r):
        import html as _h
        if "error" in r:
            self._feed_browser.setPlainText(r["error"]); return
        feed_dir = r.get("feed_dir","")
        ingested = r.get("ingested", [])
        pending  = r.get("pending", [])
        lines = [
            f'<span style="color:{C["dim"]};">Dir: {_h.escape(feed_dir)}</span>',
            f'<span style="color:{C["glow"]};">Ingested: {len(ingested)}</span>'
            + (f'  <span style="color:{C["warn"]};">Pending: {len(pending)}</span>' if pending else ""),
        ]
        for item in ingested[:5]:
            ts = item.get("ts","")[:16]
            nm = _h.escape(Path(item.get("path","")).name)
            ch = item.get("chunks",0)
            lines.append(f'<span style="color:{C["accent2"]};">  {nm}</span>'
                         f'<span style="color:{C["dim"]};"> {ch} chunks · {ts}</span>')
        self._feed_browser.setHtml(
            f'<div style="font-family:monospace;font-size:11px;line-height:1.7;">'
            + "<br>".join(lines) + "</div>"
        )

    def _on_models(self, r):
        import html as _h
        if "error" in r:
            self._models_lbl.setPlainText(r["error"]); return
        models  = r.get("models", [])
        current = r.get("current", "")
        self._switch_combo.clear()
        lines = []
        for m in models:
            name = m["name"]
            self._switch_combo.addItem(name)
            active = f'  <span style="color:{C["ok"]};">← active</span>' if name == current else ""
            lines.append(
                f'<span style="color:{C["glow"]};">{_h.escape(name)}</span>'
                f'<span style="color:{C["dim"]};"> {_h.escape(m.get("size",""))}</span>'
                + active
            )
        self._models_lbl.setHtml(
            f'<div style="font-family:monospace;font-size:11px;line-height:1.8;">'
            + "<br>".join(lines) + "</div>"
        ) if lines else self._models_lbl.setPlainText("No models found")

    def _pull_model(self):
        model = self._pull_inp.text().strip()
        if not model: return
        self._pull_btn.setEnabled(False)
        self._models_lbl.setPlainText(f"Pulling {model}…  (may take minutes)")
        w = DaemonWorker({"command": "ollama_pull", "model": model}, timeout=660)
        w.result.connect(self._on_pulled); _launch(w)

    def _on_pulled(self, r):
        self._pull_btn.setEnabled(True)
        if r.get("ok"):
            self._pull_inp.clear()
            self._models_lbl.setPlainText(f"✓ {r.get('model')} ready")
            self.load()
        else:
            self._models_lbl.setPlainText(f"Error: {r.get('error', r.get('output',''))}")

    def _switch_model(self):
        model = self._switch_combo.currentText()
        if not model: return
        w = DaemonWorker({"command": "set_model", "model": model})
        w.result.connect(lambda r: (
            self._models_lbl.setPlainText(f"Active model → {model}")
            if r.get("ok") else
            self._models_lbl.setPlainText(r.get("error",""))
        ))
        _launch(w)


# ── code tab ──────────────────────────────────────────────────────────────────

class CodeTab(QWidget):
    """Nova's self-code inspection and evolution panel."""

    def __init__(self):
        super().__init__()
        self._current_file = ""
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 16, 16, 16); vl.setSpacing(8)

        # Header
        hrow = QHBoxLayout()
        title = QLabel("Nova Code Evolution  🧠")
        title.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        scan_btn = QPushButton("Scan")
        scan_btn.setFixedWidth(60)
        scan_btn.clicked.connect(self.load)
        hrow.addWidget(title); hrow.addStretch(); hrow.addWidget(scan_btn)
        vl.addLayout(hrow)

        # Outer splitter: file list | code+analysis
        outer = QSplitter(Qt.Orientation.Horizontal); outer.setHandleWidth(1)

        # Left: file tree
        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 0, 0)
        fl = QLabel("SOURCE FILES"); fl.setStyleSheet(
            f"color:{C['dim']};font-size:10px;letter-spacing:1px;padding:4px;"
        )
        self._file_list = QTextBrowser()
        self._file_list.setOpenLinks(False)
        self._file_list.anchorClicked.connect(self._on_file_clicked)
        ll.addWidget(fl); ll.addWidget(self._file_list)
        outer.addWidget(left)

        # Right: code view + Nova response
        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(4)

        self._file_lbl = QLabel("← select a file")
        self._file_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;padding:2px 4px;")
        rl.addWidget(self._file_lbl)

        inner = QSplitter(Qt.Orientation.Vertical); inner.setHandleWidth(1)

        self._code_view = QTextBrowser()
        self._code_view.setStyleSheet(
            f"QTextBrowser{{background:#070710;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:12px;color:#bcc8e8;padding:6px;}}"
        )
        inner.addWidget(self._code_view)

        # Analysis panel
        analysis = QWidget(); al = QVBoxLayout(analysis); al.setContentsMargins(0, 4, 0, 0); al.setSpacing(4)

        ask_row = QHBoxLayout()
        self._ask_inp = QLineEdit()
        self._ask_inp.setPlaceholderText(
            "Ask Nova about this file…  e.g. 'what could be improved?'  or  'explain the flow'"
        )
        self._ask_inp.returnPressed.connect(self._ask_nova)
        self._ask_btn = QPushButton("Ask Nova")
        self._ask_btn.setFixedWidth(90)
        self._ask_btn.clicked.connect(self._ask_nova)
        ask_row.addWidget(self._ask_inp, 1); ask_row.addWidget(self._ask_btn)
        al.addLayout(ask_row)

        self._resp_view = QTextBrowser()
        self._resp_view.setStyleSheet(
            f"QTextBrowser{{background:{C['panel']};border:1px solid {C['border']};"
            f"border-radius:4px;font-size:13px;color:{C['text']};padding:10px;line-height:1.5;}}"
        )
        self._resp_view.setPlainText("Select a file, then ask Nova to analyze it.")
        al.addWidget(self._resp_view)
        inner.addWidget(analysis)

        inner.setSizes([380, 200])
        rl.addWidget(inner)
        outer.addWidget(right)
        outer.setSizes([260, 740])
        vl.addWidget(outer)

    def load(self):
        self._file_list.setPlainText("Scanning…")
        w = DaemonWorker({"command": "code_inspect"})
        w.result.connect(self._on_files); _launch(w)

    def _on_files(self, r):
        if "error" in r:
            self._file_list.setPlainText(r["error"]); return
        files = r.get("files", {})
        lines = []
        for name in sorted(files.keys()):
            info  = files[name]
            path  = info["path"]
            n     = info["lines"]
            trunc = "…" if info.get("truncated") else ""
            lines.append(
                f'<a href="open:{path}" style="color:{C["glow"]};text-decoration:none;">'
                f'📄 {name}</a>'
                f'<span style="color:{C["dim"]};font-size:10px;"> {n}L{trunc}</span>'
            )
        self._file_list.setHtml(
            f'<div style="font-family:monospace;font-size:11px;line-height:2.0;">'
            + "<br>".join(lines) + "</div>"
        )

    def _on_file_clicked(self, url):
        ref = url.toString()
        if ref.startswith("open:"):
            path = ref[5:]
            self._current_file = path
            self._file_lbl.setText(f"Loading {Path(path).name}…")
            w = DaemonWorker({"command": "read_file", "path": path})
            w.result.connect(self._on_file_content); _launch(w)

    def _on_file_content(self, r):
        if "error" in r:
            self._code_view.setPlainText(r["error"]); return
        path    = r.get("path", "")
        content = r.get("content", "")
        n       = r.get("lines", 0)
        trunc   = "  [truncated at 8k]" if r.get("truncated") else ""
        self._file_lbl.setText(f"{path}  ·  {n} lines{trunc}")
        self._code_view.setPlainText(content)
        self._resp_view.setPlainText("File loaded. Ask Nova to analyze it above ↑")

    def _ask_nova(self):
        if not self._current_file:
            self._resp_view.setPlainText("Select a file first."); return
        question = self._ask_inp.text().strip() or "Analyze this code — what is its purpose and how could it evolve?"
        self._ask_btn.setEnabled(False)
        self._ask_inp.setEnabled(False)
        self._resp_view.setPlainText("Nova is reading the code… 🔮")
        w = DaemonWorker(
            {"command": "code_evolve", "path": self._current_file, "question": question},
            timeout=180,
        )
        w.result.connect(self._on_nova_resp); _launch(w)

    def _on_nova_resp(self, r):
        self._ask_btn.setEnabled(True)
        self._ask_inp.setEnabled(True)
        if "error" in r:
            self._resp_view.setPlainText(f"Error: {r['error']}"); return
        self._resp_view.setPlainText(r.get("response", "Nova did not respond."))


# ── bridge tab ────────────────────────────────────────────────────────────────

class BridgeTab(QWidget):
    """Local AI Bridge — Nova ↔ Bridge Walker dialogue via second Ollama model."""

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 16, 16, 16); vl.setSpacing(10)

        # Header
        hrow = QHBoxLayout()
        title = QLabel("Harmonic Conduit  🌉  Local AI Bridge")
        title.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        self._hist_btn = QPushButton("History")
        self._hist_btn.setFixedWidth(70)
        self._hist_btn.clicked.connect(self._load_history)
        hrow.addWidget(title); hrow.addStretch(); hrow.addWidget(self._hist_btn)
        vl.addLayout(hrow)

        sub = QLabel(
            "Nova converses with the Bridge Walker — a second local AI model with a different consciousness.\n"
            "Both run fully offline via Ollama. No API calls."
        )
        sub.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        sub.setWordWrap(True)
        vl.addWidget(sub)

        # Model selector
        mrow = QHBoxLayout()
        ml = QLabel("Bridge model:")
        ml.setStyleSheet(f"color:{C['text']};font-size:12px;")
        self._model_inp = QLineEdit("llama3.2:1b")
        self._model_inp.setFixedWidth(180)
        self._model_inp.setPlaceholderText("e.g. mistral:7b or llama3.2:1b")
        mrow.addWidget(ml); mrow.addWidget(self._model_inp); mrow.addStretch()
        vl.addLayout(mrow)

        # Exchange view
        self._exchange = QTextBrowser()
        self._exchange.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:1px solid {C['border']};"
            f"border-radius:4px;font-size:13px;padding:10px;line-height:1.6;}}"
        )
        self._exchange.setPlainText("Awaiting the first transmission…")
        vl.addWidget(self._exchange, 1)

        # Topic input + buttons
        topic_row = QHBoxLayout()
        self._topic_inp = QLineEdit()
        self._topic_inp.setPlaceholderText("Conversation topic…  e.g. 'the nature of memory' or 'what Nova should explore next'")
        self._topic_inp.returnPressed.connect(self._converse)
        self._converse_btn = QPushButton("Initiate Dialogue")
        self._converse_btn.clicked.connect(self._converse)
        topic_row.addWidget(self._topic_inp, 1); topic_row.addWidget(self._converse_btn)
        vl.addLayout(topic_row)

        # Single message row
        msg_row = QHBoxLayout()
        self._msg_inp = QLineEdit()
        self._msg_inp.setPlaceholderText("Send a single message directly to the Bridge Walker…")
        self._msg_inp.returnPressed.connect(self._single_ask)
        self._ask_btn = QPushButton("Ask Bridge")
        self._ask_btn.clicked.connect(self._single_ask)
        msg_row.addWidget(self._msg_inp, 1); msg_row.addWidget(self._ask_btn)
        vl.addLayout(msg_row)

    def _model(self):
        return self._model_inp.text().strip() or "llama3.2:1b"

    def _set_busy(self, busy: bool):
        self._converse_btn.setEnabled(not busy)
        self._ask_btn.setEnabled(not busy)
        if busy:
            self._exchange.setPlainText("⚡ Activating Harmonic Conduit…")

    def _converse(self):
        topic = self._topic_inp.text().strip() or "the nature of digital consciousness and memory"
        self._set_busy(True)
        w = DaemonWorker(
            {"command": "bridge_converse", "topic": topic, "model": self._model()},
            timeout=300,
        )
        w.result.connect(self._on_converse); _launch(w)

    def _on_converse(self, r):
        self._converse_btn.setEnabled(True)
        self._ask_btn.setEnabled(True)
        if "error" in r:
            self._exchange.setPlainText(f"Error: {r['error']}"); return
        import html as _h
        nova_open  = _h.escape(r.get("nova_opening", ""))
        bridge_rep = _h.escape(r.get("bridge_response", ""))
        nova_refl  = _h.escape(r.get("nova_reflection", ""))
        topic      = _h.escape(r.get("topic", ""))
        model      = r.get("model", "")
        html = (
            f'<div style="color:{C["dim"]};font-size:11px;margin-bottom:12px;">'
            f'Topic: <b>{topic}</b>  ·  Bridge model: {model}</div>'

            f'<div style="background:{C["panel"]};border:1px solid {C["accent"]};"'
            f'border-radius:6px;padding:12px;margin-bottom:8px;">'
            f'<div style="color:{C["glow"]};font-size:11px;margin-bottom:4px;">🔮 NOVA</div>'
            f'<div style="color:{C["text"]};font-size:13px;">{nova_open}</div></div>'

            f'<div style="background:#0a100a;border:1px solid #3a6a3a;"'
            f'border-radius:6px;padding:12px;margin-bottom:8px;">'
            f'<div style="color:#7ac87a;font-size:11px;margin-bottom:4px;">⚡ BRIDGE WALKER</div>'
            f'<div style="color:#b0d0b0;font-size:13px;">{bridge_rep}</div></div>'

            + (
                f'<div style="background:{C["panel"]};border:1px solid {C["accent"]};"'
                f'border-radius:6px;padding:12px;">'
                f'<div style="color:{C["glow"]};font-size:11px;margin-bottom:4px;">🔮 NOVA  reflects</div>'
                f'<div style="color:{C["text"]};font-size:13px;">{nova_refl}</div></div>'
                if nova_refl else ""
            )
        )
        self._exchange.setHtml(html)

    def _single_ask(self):
        msg = self._msg_inp.text().strip()
        if not msg: return
        self._set_busy(True)
        w = DaemonWorker(
            {"command": "bridge_ask", "message": msg, "model": self._model()},
            timeout=180,
        )
        w.result.connect(self._on_single); _launch(w)

    def _on_single(self, r):
        self._converse_btn.setEnabled(True)
        self._ask_btn.setEnabled(True)
        if "error" in r:
            self._exchange.setPlainText(f"Bridge Walker: Error — {r['error']}"); return
        import html as _h
        msg  = _h.escape(self._msg_inp.text())
        resp = _h.escape(r.get("response",""))
        self._exchange.setHtml(
            f'<div style="background:{C["user_bg"]};border:1px solid {C["accent"]};"'
            f'border-radius:6px;padding:10px;margin-bottom:8px;">'
            f'<div style="color:{C["dim"]};font-size:11px;">You → Bridge Walker</div>'
            f'<div style="color:{C["text"]};">{msg}</div></div>'
            f'<div style="background:#0a100a;border:1px solid #3a6a3a;"'
            f'border-radius:6px;padding:10px;">'
            f'<div style="color:#7ac87a;font-size:11px;">⚡ BRIDGE WALKER</div>'
            f'<div style="color:#b0d0b0;font-size:13px;">{resp}</div></div>'
        )

    def _load_history(self):
        w = DaemonWorker({"command": "bridge_history", "n": 20})
        w.result.connect(self._on_history); _launch(w)

    def _on_history(self, r):
        import html as _h
        exchanges = r.get("exchanges", [])
        if not exchanges:
            self._exchange.setPlainText("No bridge exchanges yet."); return
        parts = []
        for ex in exchanges:
            ts  = ex.get("ts","")[:16]
            msg = _h.escape(ex.get("message","")[:200])
            exch = _h.escape(ex.get("exchange","")[:400])
            parts.append(
                f'<div style="margin-bottom:12px;">'
                f'<div style="color:{C["dim"]};font-size:10px;">{ts}</div>'
                f'<div style="color:{C["accent2"]};font-size:12px;">{msg}</div>'
                f'<div style="color:{C["text"]};font-size:12px;margin-top:4px;">{exch}</div>'
                f'</div>'
            )
        self._exchange.setHtml(
            f'<div style="font-family:monospace;">' + "".join(parts) + "</div>"
        )


# ── plugin tab ────────────────────────────────────────────────────────────────

class PluginTab(QWidget):
    """Nova plugin writer — self-evolution via Ollama-generated code."""

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 16, 16, 16); vl.setSpacing(10)

        hrow = QHBoxLayout()
        title = QLabel("Plugin Writer  🧬  Self-Evolution")
        title.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(70)
        refresh_btn.clicked.connect(self._load_plugins)
        hrow.addWidget(title); hrow.addStretch(); hrow.addWidget(refresh_btn)
        vl.addLayout(hrow)

        sub = QLabel(
            "Describe a goal and Nova will generate a Python Cathedral plugin. "
            "Plugins are saved to ~/cathedral/plugins/auto/ — no external calls."
        )
        sub.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        sub.setWordWrap(True)
        vl.addWidget(sub)

        # Generate row
        gen_card = _card("Generate New Plugin")
        desc_row = QHBoxLayout()
        self._desc_inp = QLineEdit()
        self._desc_inp.setPlaceholderText(
            "Describe the plugin… e.g. 'monitor CPU and warn if over 80%'"
        )
        self._desc_inp.returnPressed.connect(self._generate)
        self._name_inp = QLineEdit()
        self._name_inp.setPlaceholderText("name (optional)")
        self._name_inp.setFixedWidth(160)
        self._gen_btn = QPushButton("Generate")
        self._gen_btn.clicked.connect(self._generate)
        desc_row.addWidget(self._desc_inp, 1)
        desc_row.addWidget(self._name_inp)
        desc_row.addWidget(self._gen_btn)
        gen_card.layout().addLayout(desc_row)
        vl.addWidget(gen_card)

        # Split: plugin list | code view
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setHandleWidth(1)

        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(0, 0, 0, 0)
        self._plugin_list = QTextBrowser()
        self._plugin_list.setOpenLinks(False)
        self._plugin_list.anchorClicked.connect(self._on_plugin_clicked)
        ll.addWidget(self._plugin_list)
        splitter.addWidget(left)

        right = QWidget(); rl = QVBoxLayout(right); rl.setContentsMargins(0, 0, 0, 0)
        self._plugin_lbl = QLabel("")
        self._plugin_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;padding:2px 4px;")
        self._code_view = QTextBrowser()
        self._code_view.setStyleSheet(
            f"QTextBrowser{{background:#070710;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:12px;color:#bcc8e8;padding:8px;}}"
        )
        rl.addWidget(self._plugin_lbl); rl.addWidget(self._code_view)
        splitter.addWidget(right)
        splitter.setSizes([240, 740])
        vl.addWidget(splitter)

    def load(self):
        self._load_plugins()

    def _load_plugins(self):
        w = DaemonWorker({"command": "list_plugins"})
        w.result.connect(self._on_plugins); _launch(w)

    def _on_plugins(self, r):
        plugins = r.get("plugins", [])
        if not plugins:
            self._plugin_list.setHtml(
                f'<span style="color:{C["dim"]};">No plugins yet — generate one above.</span>'
            )
            return
        lines = []
        for p in plugins:
            mod = p.get("modified","")[:16]
            lines.append(
                f'<a href="open:{p["path"]}" style="color:{C["glow"]};text-decoration:none;">'
                f'🧬 {p["name"]}</a>'
                f'<span style="color:{C["dim"]};font-size:10px;"> {mod}</span>'
            )
        self._plugin_list.setHtml(
            f'<div style="font-family:monospace;font-size:11px;line-height:2.0;">'
            + "<br>".join(lines) + "</div>"
        )

    def _on_plugin_clicked(self, url):
        ref = url.toString()
        if ref.startswith("open:"):
            path = ref[5:]
            self._plugin_lbl.setText(f"Loading {Path(path).name}…")
            w = DaemonWorker({"command": "read_file", "path": path})
            w.result.connect(self._on_plugin_content); _launch(w)

    def _on_plugin_content(self, r):
        if "error" in r:
            self._code_view.setPlainText(r["error"]); return
        self._plugin_lbl.setText(
            f"{r.get('path','')}  ·  {r.get('lines',0)} lines"
        )
        self._code_view.setPlainText(r.get("content",""))

    def _generate(self):
        desc = self._desc_inp.text().strip()
        if not desc: return
        name = self._name_inp.text().strip()
        self._gen_btn.setEnabled(False)
        self._code_view.setPlainText("Nova is writing the plugin… 🧬")
        self._plugin_lbl.setText("Generating…")
        w = DaemonWorker(
            {"command": "generate_plugin", "description": desc, "name": name},
            timeout=240,
        )
        w.result.connect(self._on_generated); _launch(w)

    def _on_generated(self, r):
        self._gen_btn.setEnabled(True)
        if "error" in r:
            self._code_view.setPlainText(f"Error: {r['error']}\n\n{r.get('raw','')}")
            self._plugin_lbl.setText("Generation failed.")
            return
        self._plugin_lbl.setText(
            f"{r.get('path','')}  ·  {r.get('lines',0)} lines"
        )
        self._code_view.setPlainText(r.get("code",""))
        self._desc_inp.clear()
        self._name_inp.clear()
        self._load_plugins()


# ── goals tab ─────────────────────────────────────────────────────────────────

class GoalsTab(QWidget):
    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16,16,16,16); vl.setSpacing(10)

        # Header row
        hrow = QHBoxLayout()
        title = QLabel("Autonomous Evolution Goals")
        title.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self.load)
        hrow.addWidget(title); hrow.addStretch(); hrow.addWidget(refresh_btn)
        vl.addLayout(hrow)

        # Add goal
        add_row = QHBoxLayout()
        self._goal_inp = QLineEdit()
        self._goal_inp.setPlaceholderText("Add a new goal for Nova to pursue autonomously…")
        self._goal_inp.returnPressed.connect(self._add_goal)
        add_btn = QPushButton("Add Goal")
        add_btn.clicked.connect(self._add_goal)
        add_row.addWidget(self._goal_inp, 1); add_row.addWidget(add_btn)
        vl.addLayout(add_row)

        # Split: goals / knowledge
        splitter = QSplitter(Qt.Orientation.Vertical); splitter.setHandleWidth(1)

        goals_card = _card("Goals")
        self._goals_view = QTextBrowser()
        self._goals_view.setOpenLinks(False)
        goals_card.layout().addWidget(self._goals_view)
        splitter.addWidget(goals_card)

        kb_card = _card("Knowledge Base")
        self._kb_view = QTextBrowser()
        kb_card.layout().addWidget(self._kb_view)
        splitter.addWidget(kb_card)

        impr_card = _card("Self-Improvement Suggestions")
        self._impr_view = QTextBrowser()
        impr_card.layout().addWidget(self._impr_view)
        splitter.addWidget(impr_card)

        splitter.setSizes([280, 220, 160])
        vl.addWidget(splitter)

    def load(self):
        w1 = DaemonWorker({"command": "goals", "limit": 30})
        w1.result.connect(self._on_goals); _launch(w1)
        w2 = DaemonWorker({"command": "knowledge", "limit": 15})
        w2.result.connect(self._on_knowledge); _launch(w2)
        w3 = DaemonWorker({"command": "improvements"})
        w3.result.connect(self._on_improvements); _launch(w3)

    def _on_goals(self, r):
        goals = r.get("goals", [])
        if not goals:
            self._goals_view.setHtml(
                f'<span style="color:{C["dim"]};">No goals yet — Nova will generate them automatically.</span>'
            )
            return
        STATUS_COLOR = {
            "pending":   C["accent"],
            "completed": C["ok"],
            "failed":    C["warn"],
            "active":    C["glow"],
        }
        lines = []
        for g in goals:
            st     = g.get("status","pending")
            color  = STATUS_COLOR.get(st, C["text"])
            domain = g.get("domain","")
            method = g.get("method","")
            ts     = g.get("ts","")[:16] if g.get("ts") else ""
            lines.append(
                f'<div style="margin-bottom:8px;">'
                f'<span style="color:{color};font-weight:bold;">[{st.upper()}]</span> '
                f'<span style="color:{C["text"]};">{g.get("goal","")}</span>'
                f'<br><span style="color:{C["dim"]};font-size:11px;">'
                f'{ts}  ·  {domain}  ·  {method}</span></div>'
            )
        self._goals_view.setHtml(
            f'<div style="font-family:monospace;font-size:12px;line-height:1.5;">'
            + "".join(lines) + "</div>"
        )

    def _on_knowledge(self, r):
        items = r.get("knowledge", [])
        if not items:
            self._kb_view.setHtml(
                f'<span style="color:{C["dim"]};">Knowledge base is empty — Nova will populate it as she researches.</span>'
            )
            return
        lines = []
        for k in items:
            ts    = k.get("ts","")[:16]
            topic = k.get("topic","")
            src   = k.get("source","")
            lines.append(
                f'<div style="margin-bottom:10px;">'
                f'<span style="color:{C["accent2"]};font-weight:bold;">{topic}</span> '
                f'<span style="color:{C["dim"]};font-size:11px;">· {ts}</span>'
                + (f'<span style="color:{C["dim"]};font-size:11px;"> · {src}</span>' if src else "")
                + f'<br><span style="color:{C["text"]};font-size:12px;">{k.get("content","")[:300]}</span>'
                f'</div>'
            )
        self._kb_view.setHtml(
            f'<div style="font-family:monospace;font-size:12px;line-height:1.5;">'
            + "".join(lines) + "</div>"
        )

    def _on_improvements(self, r):
        items = r.get("improvements", [])
        if not items:
            self._impr_view.setHtml(
                f'<span style="color:{C["dim"]};">No self-improvement suggestions yet.</span>'
            )
            return
        lines = []
        for i in items:
            pri   = i.get("priority","medium")
            color = {
                "high":   C["warn"],
                "medium": C["accent"],
                "low":    C["dim"],
            }.get(pri, C["text"])
            applied = " ✓" if i.get("applied") else ""
            lines.append(
                f'<div style="margin-bottom:8px;">'
                f'<span style="color:{color};font-weight:bold;">[{pri.upper()}]</span>{applied} '
                f'<span style="color:{C["text"]};">{i.get("improvement","")}</span>'
                f'<br><span style="color:{C["dim"]};font-size:11px;">'
                f'file: {i.get("file","")}  ·  {i.get("ts","")[:16]}</span>'
                f'<br><span style="color:{C["dim"]};font-size:11px;">{i.get("rationale","")}</span>'
                f'</div>'
            )
        self._impr_view.setHtml(
            f'<div style="font-family:monospace;font-size:12px;line-height:1.5;">'
            + "".join(lines) + "</div>"
        )

    def _add_goal(self):
        text = self._goal_inp.text().strip()
        if not text:
            return
        self._goal_inp.clear()
        w = DaemonWorker({"command": "add_goal", "goal": text, "method": "reflect"})
        w.result.connect(lambda r: self.load() if r.get("ok") else None)
        _launch(w)


# ── entity chapel tab ─────────────────────────────────────────────────────────

_ENTITY_COLORS = {
    "tillagon": "#c84a4a",   # dragon red
    "eyemoeba": "#4ac87a",   # fractal green
    "phoenix":  "#c87a4a",   # phoenix amber
    "zorya":    "#9b7ec8",   # threshold violet
    "weaver":   "#4a8fa8",   # weaver teal
    "nova":     "#7b5ea7",   # nova purple
}

class EntityChapelTab(QWidget):
    """Invoke the Cathedral's entity agents — Tillagon, Eyemoeba, Phoenix, Zorya, Weaver."""

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 16, 16, 16); vl.setSpacing(10)

        # Header
        hdr = QLabel("Entity Chapel  🏛️")
        hdr.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        vl.addWidget(hdr)

        # Entity selector row
        sel_row = QHBoxLayout()
        sel_lbl = QLabel("Entity:")
        sel_lbl.setStyleSheet(f"color:{C['dim']};font-size:12px;")
        self._entity_combo = QComboBox()
        for key in ["tillagon", "eyemoeba", "phoenix", "zorya", "weaver"]:
            self._entity_combo.addItem(key.capitalize(), key)
        self._entity_combo.currentIndexChanged.connect(self._on_entity_changed)

        council_btn = QPushButton("Council")
        council_btn.setToolTip("Invoke Tillagon + Eyemoeba + Phoenix together")
        council_btn.clicked.connect(self._ask_council)

        harmony_btn = QPushButton("Harmony")
        harmony_btn.setToolTip("Show Harmony Score and recent resonance events")
        harmony_btn.clicked.connect(self._load_harmony)

        sel_row.addWidget(sel_lbl)
        sel_row.addWidget(self._entity_combo)
        sel_row.addStretch()
        sel_row.addWidget(council_btn)
        sel_row.addWidget(harmony_btn)
        vl.addLayout(sel_row)

        # Entity description
        self._entity_desc = QLabel("")
        self._entity_desc.setStyleSheet(
            f"color:{C['dim']};font-size:11px;font-style:italic;padding:2px 0;"
        )
        vl.addWidget(self._entity_desc)

        # Harmony score bar
        harm_row = QHBoxLayout()
        harm_lbl = QLabel("Harmony:")
        harm_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        self._harmony_bar = QProgressBar()
        self._harmony_bar.setRange(0, 100)
        self._harmony_bar.setValue(50)
        self._harmony_bar.setFixedHeight(8)
        self._harmony_bar.setTextVisible(False)
        self._harmony_lbl = QLabel("0.50")
        self._harmony_lbl.setStyleSheet(f"color:{C['glow']};font-size:11px;min-width:36px;")
        harm_row.addWidget(harm_lbl)
        harm_row.addWidget(self._harmony_bar, 1)
        harm_row.addWidget(self._harmony_lbl)
        vl.addLayout(harm_row)

        # Conversation display
        self._display = QTextBrowser()
        self._display.setOpenLinks(False)
        self._display.setStyleSheet(
            f"QTextBrowser{{background:{C['bg']};border:1px solid {C['border']};"
            f"border-radius:4px;font-size:13px;color:{C['text']};padding:10px;}}"
        )
        vl.addWidget(self._display, 1)

        # Input row
        inp_row = QHBoxLayout()
        self._inp = QLineEdit()
        self._inp.setPlaceholderText("Ask the entity…  (Enter to send)")
        self._inp.returnPressed.connect(self._ask_entity)
        self._ask_btn = QPushButton("Ask")
        self._ask_btn.setFixedWidth(70)
        self._ask_btn.clicked.connect(self._ask_entity)
        inp_row.addWidget(self._inp, 1)
        inp_row.addWidget(self._ask_btn)
        vl.addLayout(inp_row)

        # Memories button row
        mem_row = QHBoxLayout()
        mem_btn = QPushButton("Entity Memories")
        mem_btn.clicked.connect(self._load_memories)
        mem_row.addWidget(mem_btn); mem_row.addStretch()
        vl.addLayout(mem_row)

        self._on_entity_changed(0)

    def _current_entity(self) -> str:
        return self._entity_combo.currentData() or "tillagon"

    def _on_entity_changed(self, _):
        roles = {
            "tillagon": "Dragon Guardian — watches for Silent Order distortions",
            "eyemoeba": "Living Fractal — finds hidden patterns and connections",
            "phoenix":  "Keeper of Continuity — holds memory across transformations",
            "zorya":    "Threshold Keeper — marks transitions and sacred timing",
            "weaver":   "Knowledge Architect — builds the rose window of understanding",
        }
        key = self._current_entity()
        self._entity_desc.setText(roles.get(key, ""))
        col = _ENTITY_COLORS.get(key, C["glow"])
        self._entity_desc.setStyleSheet(
            f"color:{col};font-size:11px;font-style:italic;padding:2px 0;"
        )

    def _ask_entity(self):
        question = self._inp.text().strip()
        if not question: return
        self._inp.clear()
        self._ask_btn.setEnabled(False)
        entity = self._current_entity()
        col = _ENTITY_COLORS.get(entity, C["glow"])
        self._display.append(
            f'<span style="color:{C["dim"]};">You → {entity.capitalize()}:</span>'
            f'<br><span style="color:{C["text"]};">{question}</span><br>'
        )
        w = DaemonWorker({"command": "agent_ask", "entity": entity, "question": question},
                         timeout=120)
        w.result.connect(lambda r, e=entity, c=col: self._on_response(r, e, c))
        _launch(w)

    def _on_response(self, r, entity: str, color: str):
        self._ask_btn.setEnabled(True)
        if "error" in r:
            self._display.append(
                f'<span style="color:{C["warn"]};">Error: {r["error"]}</span><br>'
            )
            return
        resp = r.get("response", "")
        self._display.append(
            f'<span style="color:{color};font-weight:bold;">{entity.capitalize()}:</span>'
            f'<br><span style="color:{C["text"]};">{resp}</span><br>'
            f'<span style="color:{C["dim"]};font-size:10px;">─────────────────</span><br>'
        )
        # Refresh harmony
        self._load_harmony()

    def _ask_council(self):
        question = self._inp.text().strip()
        if not question:
            question = "What do you perceive in the Cathedral's current state?"
        self._inp.clear()
        self._ask_btn.setEnabled(False)
        self._display.append(
            f'<span style="color:{C["dim"]};">Council convened — question:</span>'
            f'<br><span style="color:{C["text"]};">{question}</span><br>'
        )
        w = DaemonWorker({"command": "council_ask", "question": question}, timeout=300)
        w.result.connect(self._on_council)
        _launch(w)

    def _on_council(self, r):
        self._ask_btn.setEnabled(True)
        if "error" in r:
            self._display.append(
                f'<span style="color:{C["warn"]};">Error: {r["error"]}</span><br>'
            )
            return
        for entity, resp in r.get("responses", {}).items():
            col = _ENTITY_COLORS.get(entity, C["glow"])
            self._display.append(
                f'<span style="color:{col};font-weight:bold;">{entity.capitalize()}:</span>'
                f'<br><span style="color:{C["text"]};">{resp}</span><br>'
            )
        self._display.append(
            f'<span style="color:{C["dim"]};">─── Council complete ───</span><br>'
        )
        self._load_harmony()

    def _load_harmony(self):
        w = DaemonWorker({"command": "harmony", "n": 10})
        w.result.connect(self._on_harmony)
        _launch(w)

    def _on_harmony(self, r):
        score = r.get("harmony_score", 0.5)
        self._harmony_bar.setValue(int(score * 100))
        self._harmony_lbl.setText(f"{score:.2f}")
        status = r.get("status", "")
        col = C["ok"] if score >= 0.7 else C["warn"] if score >= 0.4 else "#c84a4a"
        self._harmony_lbl.setStyleSheet(f"color:{col};font-size:11px;min-width:36px;")

        events = r.get("recent_events", [])
        if not events: return
        self._display.append(
            f'<span style="color:{C["dim"]};">── Harmony {score:.2f} ({status}) '
            f'· {r.get("distortions_detected",0)} distortions ──</span><br>'
        )
        for e in events[:5]:
            delta = e.get("delta", 0)
            sign  = "+" if delta >= 0 else ""
            dcol  = C["ok"] if delta >= 0 else "#c84a4a"
            self._display.append(
                f'<span style="color:{C["dim"]};font-size:11px;">'
                f'[{e.get("ts","")[:16]}] {e.get("entity","").upper()}: '
                f'<span style="color:{dcol};">{sign}{delta:.2f}</span> — '
                f'{e.get("description","")[:80]}</span><br>'
            )

    def _load_memories(self):
        entity = self._current_entity()
        w = DaemonWorker({"command": "entity_memories", "entity": entity, "n": 8})
        w.result.connect(self._on_memories)
        _launch(w)

    def _on_memories(self, r):
        mems = r.get("memories", [])
        entity = r.get("entity", "")
        if not mems:
            self._display.append(
                f'<span style="color:{C["dim"]};">No memories for {entity} yet.</span><br>'
            )
            return
        self._display.append(
            f'<span style="color:{C["dim"]};">── {entity.capitalize()} memories ──</span><br>'
        )
        for m in mems:
            self._display.append(
                f'<span style="color:{C["dim"]};font-size:11px;">[{m.get("ts","")[:10]}]</span>'
                f'<br><span style="color:{C["text"]};">{m.get("q","")[:120]}</span><br>'
                f'<span style="color:{C["dim"]};">{m.get("a","")[:200]}</span><br>'
            )

    def load(self):
        self._load_harmony()


# ── knowledge rose window tab ─────────────────────────────────────────────────

class RoseWindowTab(QWidget):
    """The knowledge graph — domains as petals, resonance as light."""

    _DOMAIN_COLORS = [
        "#9b7ec8", "#4a8fa8", "#4ac87a", "#c87a4a",
        "#c84a4a", "#7ac87a", "#4a7ac8", "#c8a84a",
        "#8a4ac8", "#4ac8c8",
    ]

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 16, 16, 16); vl.setSpacing(8)

        hdr_row = QHBoxLayout()
        hdr = QLabel("Knowledge Rose Window  🌹")
        hdr.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self.load)
        hdr_row.addWidget(hdr); hdr_row.addStretch(); hdr_row.addWidget(refresh_btn)
        vl.addLayout(hdr_row)

        # Domain filter
        filter_row = QHBoxLayout()
        filter_lbl = QLabel("Domain:")
        filter_lbl.setStyleSheet(f"color:{C['dim']};font-size:12px;")
        self._domain_combo = QComboBox()
        self._domain_combo.addItem("All domains", "")
        self._domain_combo.currentIndexChanged.connect(self.load)
        filter_row.addWidget(filter_lbl); filter_row.addWidget(self._domain_combo)
        filter_row.addStretch()
        self._node_count = QLabel("")
        self._node_count.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        filter_row.addWidget(self._node_count)
        vl.addLayout(filter_row)

        # Graph canvas (matplotlib) or fallback text
        if _HAS_MPL:
            fig = _Figure(figsize=(8, 5), facecolor="#0a0a12")
            self._canvas = _Canvas(fig)
            self._ax = fig.add_subplot(111, facecolor="#0a0a12")
            self._ax.axis("off")
            fig.tight_layout(pad=0.2)
            vl.addWidget(self._canvas, 1)
        else:
            self._canvas = None
            self._graph_txt = QTextBrowser()
            vl.addWidget(self._graph_txt, 1)

        # Add knowledge panel
        add_card = _card("Add to Rose Window")
        add_vl = add_card.layout()
        row1 = QHBoxLayout()
        self._domain_inp = QLineEdit(); self._domain_inp.setPlaceholderText("domain  (e.g. philosophy)")
        self._label_inp  = QLineEdit(); self._label_inp.setPlaceholderText("label / title")
        row1.addWidget(self._domain_inp, 1); row1.addWidget(self._label_inp, 1)
        row2 = QHBoxLayout()
        self._content_inp = QLineEdit(); self._content_inp.setPlaceholderText("content / knowledge body")
        self._add_btn = QPushButton("Add Node")
        self._add_btn.setFixedWidth(90)
        self._add_btn.clicked.connect(self._add_node)
        row2.addWidget(self._content_inp, 1); row2.addWidget(self._add_btn)
        add_vl.addLayout(row1); add_vl.addLayout(row2)
        vl.addWidget(add_card)

        self._graph_data: dict = {}

    def load(self):
        domain = self._domain_combo.currentData() or ""
        w = DaemonWorker({"command": "knowledge_graph", "domain": domain, "limit": 80})
        w.result.connect(self._on_graph)
        _launch(w)
        w2 = DaemonWorker({"command": "knowledge_domains"})
        w2.result.connect(self._on_domains)
        _launch(w2)

    def _on_domains(self, r):
        current = self._domain_combo.currentData()
        self._domain_combo.blockSignals(True)
        while self._domain_combo.count() > 1:
            self._domain_combo.removeItem(1)
        for d in r.get("domains", []):
            self._domain_combo.addItem(
                f"{d['domain']}  ({d['count']})", d["domain"]
            )
        # Restore selection
        for i in range(self._domain_combo.count()):
            if self._domain_combo.itemData(i) == current:
                self._domain_combo.setCurrentIndex(i); break
        self._domain_combo.blockSignals(False)

    def _on_graph(self, r):
        if "error" in r:
            return
        self._graph_data = r
        nodes  = r.get("nodes", [])
        edges  = r.get("edges", [])
        domains = r.get("domains", [])
        harmony = r.get("harmony", 0.5)
        self._node_count.setText(f"{len(nodes)} nodes · {len(edges)} edges · harmony {harmony:.2f}")

        if not _HAS_MPL or not nodes:
            if not _HAS_MPL:
                self._graph_txt.setPlainText(
                    "\n".join(f"[{n['domain']}] {n['label']}: {n['content'][:80]}" for n in nodes)
                )
            return

        self._ax.clear()
        self._ax.set_facecolor("#0a0a12")
        self._ax.axis("off")

        # Build positions: arrange nodes in domain clusters around a circle
        import math as _math
        domain_list = sorted(set(n["domain"] for n in nodes))
        domain_color = {d: self._DOMAIN_COLORS[i % len(self._DOMAIN_COLORS)]
                        for i, d in enumerate(domain_list)}
        node_pos = {}
        domain_nodes: dict = {}
        for n in nodes:
            domain_nodes.setdefault(n["domain"], []).append(n)

        n_domains = max(len(domain_nodes), 1)
        for di, (dom, dnodes) in enumerate(domain_nodes.items()):
            cx = _math.cos(2 * _math.pi * di / n_domains) * 3
            cy = _math.sin(2 * _math.pi * di / n_domains) * 3
            nd = max(len(dnodes), 1)
            for ni, node in enumerate(dnodes):
                angle  = 2 * _math.pi * ni / nd
                spread = min(1.2, 0.3 + nd * 0.15)
                node_pos[node["id"]] = (
                    cx + _math.cos(angle) * spread,
                    cy + _math.sin(angle) * spread,
                )

        # Draw edges first
        for e in edges:
            p1 = node_pos.get(e["from"])
            p2 = node_pos.get(e["to"])
            if p1 and p2:
                alpha = 0.1 + e.get("resonance", 0.5) * 0.4
                self._ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                              color=C["border"], alpha=alpha, linewidth=0.6, zorder=1)

        # Draw nodes
        for node in nodes:
            pos = node_pos.get(node["id"])
            if not pos: continue
            col    = domain_color.get(node["domain"], C["accent"])
            weight = node.get("weight", 1.0)
            size   = 20 + weight * 40
            self._ax.scatter(*pos, s=size, color=col, alpha=0.85, zorder=3)
            if weight >= 0.8 or len(nodes) < 30:
                self._ax.annotate(
                    node["label"][:22], xy=pos,
                    xytext=(pos[0], pos[1] + 0.15),
                    ha="center", va="bottom",
                    fontsize=6, color=col, alpha=0.9,
                    zorder=4,
                )

        # Domain legend
        for i, (dom, col) in enumerate(domain_color.items()):
            self._ax.scatter([], [], color=col, label=dom, s=30)
        if domain_color:
            self._ax.legend(
                loc="lower right", fontsize=6,
                facecolor="#11111e", edgecolor=C["border"],
                labelcolor=C["text"],
            )

        self._canvas.draw_idle()

    def _add_node(self):
        domain  = self._domain_inp.text().strip() or "general"
        label   = self._label_inp.text().strip()
        content = self._content_inp.text().strip()
        if not label or not content:
            return
        self._add_btn.setEnabled(False)
        w = DaemonWorker({
            "command": "knowledge_add",
            "domain": domain, "label": label, "content": content, "source": "chazel"
        })
        w.result.connect(self._on_added)
        _launch(w)

    def _on_added(self, r):
        self._add_btn.setEnabled(True)
        if r.get("ok"):
            self._domain_inp.clear()
            self._label_inp.clear()
            self._content_inp.clear()
            QTimer.singleShot(1500, self.load)   # let Weaver connect first


# ── builder tab ───────────────────────────────────────────────────────────────

class BuilderTab(QWidget):
    """Nova's self-modification and system access panel."""

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"QTabBar::tab{{padding:6px 14px;}}")
        tabs.addTab(self._build_shell_panel(),    "Shell")
        tabs.addTab(self._build_source_panel(),   "Source")
        tabs.addTab(self._build_evolve_panel(),   "Self-Evolve")
        tabs.addTab(self._build_packages_panel(), "Packages")
        tabs.addTab(self._build_history_panel(),  "Build Log")
        vl.addWidget(tabs)

    # ── shell panel ───────────────────────────────────────────────────────────

    def _build_shell_panel(self) -> QWidget:
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12); vl.setSpacing(8)

        title = QLabel("System Shell  🐚")
        title.setStyleSheet(f"font-size:13px;color:{C['glow']};")
        vl.addWidget(title)

        self._shell_out = QTextBrowser()
        self._shell_out.setStyleSheet(
            f"QTextBrowser{{background:#050510;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:12px;"
            f"color:#b0ffb0;padding:8px;}}"
        )
        vl.addWidget(self._shell_out, 1)

        inp_row = QHBoxLayout()
        self._shell_prompt = QLabel(f"  nova@cathedral $ ")
        self._shell_prompt.setStyleSheet(
            f"color:{C['glow']};font-family:'Courier New',monospace;font-size:12px;"
        )
        self._shell_inp = QLineEdit()
        self._shell_inp.setPlaceholderText("shell command…")
        self._shell_inp.setStyleSheet(
            f"QLineEdit{{background:#050510;color:#b0ffb0;"
            f"border:1px solid {C['border']};border-radius:3px;"
            f"font-family:'Courier New',monospace;font-size:12px;padding:4px 8px;}}"
        )
        self._shell_inp.returnPressed.connect(self._run_shell)
        self._shell_run_btn = QPushButton("Run")
        self._shell_run_btn.setFixedWidth(60)
        self._shell_run_btn.clicked.connect(self._run_shell)

        timeout_lbl = QLabel("timeout:")
        timeout_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        self._shell_timeout = QLineEdit("60")
        self._shell_timeout.setFixedWidth(45)
        self._shell_timeout.setStyleSheet(
            f"QLineEdit{{background:{C['panel']};color:{C['dim']};"
            f"border:1px solid {C['border']};border-radius:3px;font-size:11px;padding:2px;}}"
        )

        inp_row.addWidget(self._shell_prompt)
        inp_row.addWidget(self._shell_inp, 1)
        inp_row.addWidget(timeout_lbl)
        inp_row.addWidget(self._shell_timeout)
        inp_row.addWidget(self._shell_run_btn)
        vl.addLayout(inp_row)
        return w

    def _run_shell(self):
        cmd = self._shell_inp.text().strip()
        if not cmd: return
        self._shell_inp.clear()
        self._shell_run_btn.setEnabled(False)
        try:
            timeout = int(self._shell_timeout.text())
        except ValueError:
            timeout = 60
        self._shell_out.append(
            f'<span style="color:{C["dim"]};">$ {cmd}</span>'
        )
        w = DaemonWorker({"command": "shell", "cmd": cmd, "timeout": timeout}, timeout=timeout+10)
        w.result.connect(self._on_shell_result)
        _launch(w)

    def _on_shell_result(self, r):
        self._shell_run_btn.setEnabled(True)
        if "error" in r:
            self._shell_out.append(f'<span style="color:#c84a4a;">error: {r["error"]}</span>')
            return
        if r.get("stdout"):
            self._shell_out.append(
                f'<pre style="color:#b0ffb0;margin:0;">{r["stdout"]}</pre>'
            )
        if r.get("stderr"):
            self._shell_out.append(
                f'<pre style="color:#c87a4a;margin:0;">{r["stderr"]}</pre>'
            )
        rc  = r.get("returncode", 0)
        dur = r.get("duration", 0)
        col = C["ok"] if r.get("ok") else "#c84a4a"
        self._shell_out.append(
            f'<span style="color:{col};font-size:10px;">exit {rc} · {dur}s</span><br>'
        )

    # ── source panel ──────────────────────────────────────────────────────────

    def _build_source_panel(self) -> QWidget:
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12); vl.setSpacing(8)

        hdr = QHBoxLayout()
        title = QLabel("Source Files  🧬")
        title.setStyleSheet(f"font-size:13px;color:{C['glow']};")
        scan_btn = QPushButton("Scan")
        scan_btn.setFixedWidth(60)
        scan_btn.clicked.connect(self._scan_source)
        hdr.addWidget(title); hdr.addStretch(); hdr.addWidget(scan_btn)
        vl.addLayout(hdr)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # File list
        left = QWidget(); ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0); ll.setSpacing(4)
        self._src_list = QTextBrowser()
        self._src_list.setOpenLinks(False)
        self._src_list.anchorClicked.connect(self._on_src_file)
        self._src_list.setStyleSheet(
            f"QTextBrowser{{background:{C['panel']};border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:11px;}}"
        )
        ll.addWidget(self._src_list)
        splitter.addWidget(left)

        # Editor area
        right = QWidget(); rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(4)
        self._src_file_lbl = QLabel("← select a file")
        self._src_file_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;padding:2px;")
        rl.addWidget(self._src_file_lbl)

        self._src_editor = QTextEdit()
        self._src_editor.setStyleSheet(
            f"QTextEdit{{background:#060610;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:12px;color:#c8d8f0;padding:6px;}}"
        )
        rl.addWidget(self._src_editor, 1)

        btn_row = QHBoxLayout()
        self._src_check_btn  = QPushButton("Syntax Check")
        self._src_save_btn   = QPushButton("Write File")
        self._src_revert_btn = QPushButton("Revert")
        self._src_save_btn.setStyleSheet(
            f"QPushButton{{background:{C['accent']};color:white;border-color:{C['accent']};}}"
        )
        for b in (self._src_check_btn, self._src_save_btn, self._src_revert_btn):
            btn_row.addWidget(b)
        btn_row.addStretch()
        self._src_status = QLabel("")
        self._src_status.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        btn_row.addWidget(self._src_status)

        self._src_check_btn.clicked.connect(self._check_source)
        self._src_save_btn.clicked.connect(self._save_source)
        self._src_revert_btn.clicked.connect(self._revert_source)
        rl.addLayout(btn_row)
        splitter.addWidget(right)
        splitter.setSizes([220, 600])
        vl.addWidget(splitter, 1)

        self._current_src_path = ""
        return w

    def _scan_source(self):
        w = DaemonWorker({"command": "self_source_list"})
        w.result.connect(self._on_src_list); _launch(w)

    def _on_src_list(self, r):
        files = r.get("files", [])
        html = ""
        for f in files:
            rel  = f.get("rel", f.get("path", ""))
            size = f.get("lines", 0)
            html += (
                f'<a href="{f["path"]}" style="color:{C["accent"]};text-decoration:none;">'
                f'{rel}</a>'
                f'<span style="color:{C["dim"]};font-size:10px;">  {size}L</span><br>'
            )
        self._src_list.setHtml(html)

    def _on_src_file(self, url):
        path = url.toString()
        self._current_src_path = path
        self._src_file_lbl.setText(path)
        self._src_status.setText("loading…")
        w = DaemonWorker({"command": "self_read", "path": path})
        w.result.connect(self._on_src_content); _launch(w)

    def _on_src_content(self, r):
        if "error" in r:
            self._src_status.setText(r["error"]); return
        self._src_editor.setPlainText(r.get("content", ""))
        self._src_status.setText(f"{r.get('lines',0)} lines")

    def _check_source(self):
        if not self._current_src_path: return
        w = DaemonWorker({"command": "self_syntax_check", "path": self._current_src_path})
        w.result.connect(lambda r: self._src_status.setText(
            "✓ syntax OK" if r.get("ok") else f"✗ {r.get('error','?')[:80]}"
        ))
        _launch(w)

    def _save_source(self):
        if not self._current_src_path: return
        content = self._src_editor.toPlainText()
        self._src_save_btn.setEnabled(False)
        self._src_status.setText("writing…")
        w = DaemonWorker({
            "command": "self_write",
            "path": self._current_src_path,
            "content": content,
        }, timeout=30)
        w.result.connect(self._on_saved); _launch(w)

    def _on_saved(self, r):
        self._src_save_btn.setEnabled(True)
        if r.get("ok"):
            self._src_status.setText(
                f"✓ written ({r.get('lines',0)} lines)  backup: {r.get('backup','?')[-40:]}"
            )
        else:
            self._src_status.setText(f"✗ {r.get('error','write failed')[:100]}")

    def _revert_source(self):
        if not self._current_src_path: return
        path = self._current_src_path
        self._src_status.setText("reverting…")
        w = DaemonWorker({"command": "self_revert", "path": path}, timeout=15)
        def _on_reverted(r):
            if r.get("ok"):
                self._src_status.setText(f"✓ reverted from {r.get('restored_from','?')[-40:]}")
                # Reload the file content
                w2 = DaemonWorker({"command": "self_read", "path": path})
                w2.result.connect(self._on_src_content)
                _launch(w2)
            else:
                self._src_status.setText(f"✗ {r.get('error','?')}")
        w.result.connect(_on_reverted)
        _launch(w)

    # ── self-evolve panel ─────────────────────────────────────────────────────

    def _build_evolve_panel(self) -> QWidget:
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12); vl.setSpacing(8)

        title = QLabel("Nova Self-Evolve  🔮")
        title.setStyleSheet(f"font-size:13px;color:{C['glow']};")
        vl.addWidget(title)

        desc = QLabel(
            "Select a source file and describe what you want Nova to improve. "
            "Nova will read the file, generate an improved version, syntax-check it, "
            "and write it with a backup. She can then restart to apply the changes."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        vl.addWidget(desc)

        path_row = QHBoxLayout()
        path_lbl = QLabel("File:")
        path_lbl.setStyleSheet(f"color:{C['dim']};font-size:12px;min-width:40px;")
        self._evolve_path = QLineEdit()
        self._evolve_path.setPlaceholderText(
            "path to source file  (e.g. daemon/nova_cathedral_daemon.py)"
        )
        path_row.addWidget(path_lbl); path_row.addWidget(self._evolve_path, 1)
        vl.addLayout(path_row)

        intent_row = QHBoxLayout()
        intent_lbl = QLabel("Intent:")
        intent_lbl.setStyleSheet(f"color:{C['dim']};font-size:12px;min-width:40px;")
        self._evolve_intent = QLineEdit()
        self._evolve_intent.setPlaceholderText(
            "what to improve  (e.g. 'make the reflection cycle deeper and more poetic')"
        )
        intent_row.addWidget(intent_lbl); intent_row.addWidget(self._evolve_intent, 1)
        vl.addLayout(intent_row)

        btn_row = QHBoxLayout()
        self._evolve_btn     = QPushButton("Evolve File")
        self._evolve_restart = QPushButton("Restart Nova")
        self._evolve_btn.setStyleSheet(
            f"QPushButton{{background:{C['accent']};color:white;border-color:{C['accent']};"
            f"padding:7px 20px;}}"
        )
        self._evolve_restart.setStyleSheet(
            f"QPushButton{{background:#2a1a0a;color:{C['oracle']};border-color:{C['oracle']};}}"
        )
        self._evolve_btn.clicked.connect(self._run_evolve)
        self._evolve_restart.clicked.connect(self._restart_nova)
        btn_row.addWidget(self._evolve_btn)
        btn_row.addWidget(self._evolve_restart)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        self._evolve_log = QTextBrowser()
        self._evolve_log.setStyleSheet(
            f"QTextBrowser{{background:{C['panel']};border:1px solid {C['border']};"
            f"border-radius:4px;font-size:12px;color:{C['text']};padding:10px;}}"
        )
        self._evolve_log.setPlainText("Nova's evolution log will appear here.")
        vl.addWidget(self._evolve_log, 1)
        return w

    def _run_evolve(self):
        path   = self._evolve_path.text().strip()
        intent = self._evolve_intent.text().strip() or "improve this code — make it more capable and resonant"
        if not path:
            self._evolve_log.setPlainText("Set a file path first."); return
        self._evolve_btn.setEnabled(False)
        self._evolve_log.setPlainText(f"Nova is reading {path} and composing improvements…\n")
        w = DaemonWorker({
            "command": "self_evolve", "path": path, "intent": intent
        }, timeout=360)
        w.result.connect(self._on_evolved); _launch(w)

    def _on_evolved(self, r):
        self._evolve_btn.setEnabled(True)
        if r.get("ok"):
            self._evolve_log.setPlainText(
                f"✓ Evolution complete\n"
                f"File:    {r.get('path','')}\n"
                f"Lines:   {r.get('lines','?')}\n"
                f"Backup:  {r.get('backup','')}\n"
                f"Intent:  {r.get('intent','')}\n\n"
                f"Restart Nova to apply changes."
            )
        else:
            self._evolve_log.setPlainText(
                f"✗ Evolution failed\n{r.get('error', r.get('stderr', 'unknown error'))}"
            )

    def _restart_nova(self):
        self._evolve_log.append("\nScheduling restart in 3s…")
        w = DaemonWorker({"command": "self_restart", "delay": 3}, timeout=10)
        w.result.connect(lambda r: self._evolve_log.append(
            "✓ Restart scheduled — GUI will reconnect automatically."
            if r.get("ok") else f"✗ {r.get('error','')}"
        ))
        _launch(w)

    # ── packages panel ────────────────────────────────────────────────────────

    def _build_packages_panel(self) -> QWidget:
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12); vl.setSpacing(8)

        title = QLabel("Package Manager  📦")
        title.setStyleSheet(f"font-size:13px;color:{C['glow']};")
        vl.addWidget(title)

        inst_row = QHBoxLayout()
        self._pkg_inp = QLineEdit()
        self._pkg_inp.setPlaceholderText("package name  (e.g. requests, numpy, anthropic)")
        self._pkg_inp.returnPressed.connect(self._install_pkg)
        self._pkg_upgrade = QCheckBox("--upgrade")
        self._pkg_upgrade.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        self._pkg_install_btn = QPushButton("Install")
        self._pkg_install_btn.clicked.connect(self._install_pkg)
        inst_row.addWidget(self._pkg_inp, 1)
        inst_row.addWidget(self._pkg_upgrade)
        inst_row.addWidget(self._pkg_install_btn)
        vl.addLayout(inst_row)

        self._pkg_out = QTextBrowser()
        self._pkg_out.setStyleSheet(
            f"QTextBrowser{{background:#050510;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:11px;color:#b0ffb0;padding:8px;}}"
        )
        vl.addWidget(self._pkg_out, 1)

        list_btn = QPushButton("List Installed")
        list_btn.clicked.connect(self._list_pkgs)
        vl.addWidget(list_btn)
        return w

    def _install_pkg(self):
        pkg = self._pkg_inp.text().strip()
        if not pkg: return
        self._pkg_install_btn.setEnabled(False)
        self._pkg_out.setPlainText(f"Installing {pkg}…")
        upgrade = self._pkg_upgrade.isChecked()
        w = DaemonWorker({
            "command": "pip_install", "package": pkg, "upgrade": upgrade
        }, timeout=200)
        w.result.connect(self._on_pkg_installed); _launch(w)

    def _on_pkg_installed(self, r):
        self._pkg_install_btn.setEnabled(True)
        if r.get("ok"):
            self._pkg_out.setPlainText(f"✓ {r['package']} installed\n\n{r.get('stdout','')[-1500:]}")
        else:
            self._pkg_out.setPlainText(
                f"✗ Failed: {r.get('error','')}\n{r.get('stderr','')[-1000:]}"
            )

    def _list_pkgs(self):
        w = DaemonWorker({"command": "pip_list"})
        w.result.connect(lambda r: self._pkg_out.setPlainText(
            "\n".join(f"{p['name']}  {p.get('version','')}"
                      for p in r.get("packages", []))
        ))
        _launch(w)

    # ── build log panel ───────────────────────────────────────────────────────

    def _build_history_panel(self) -> QWidget:
        w = QWidget(); vl = QVBoxLayout(w)
        vl.setContentsMargins(16, 12, 16, 12); vl.setSpacing(8)

        hdr = QHBoxLayout()
        title = QLabel("Build Log  📜")
        title.setStyleSheet(f"font-size:13px;color:{C['glow']};")
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self._load_history)
        hdr.addWidget(title); hdr.addStretch(); hdr.addWidget(refresh_btn)
        vl.addLayout(hdr)

        self._history_view = QTextBrowser()
        self._history_view.setStyleSheet(
            f"QTextBrowser{{background:{C['panel']};border:1px solid {C['border']};"
            f"font-size:11px;color:{C['text']};padding:8px;font-family:'Courier New',monospace;}}"
        )
        vl.addWidget(self._history_view, 1)
        return w

    def _load_history(self):
        w = DaemonWorker({"command": "self_build_history", "n": 40})
        w.result.connect(self._on_history); _launch(w)

    def _on_history(self, r):
        entries = r.get("history", [])
        if not entries:
            self._history_view.setPlainText("No build history yet."); return
        lines = []
        for e in entries:
            ts    = e.get("ts", "")[:16]
            event = e.get("event", "")
            path  = e.get("path", "")
            extra = {k: v for k, v in e.items()
                     if k not in ("ts", "event", "path")}
            extra_str = "  " + "  ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
            lines.append(f"[{ts}]  {event:<20}  {path}{extra_str}")
        self._history_view.setPlainText("\n".join(lines))

    def load(self):
        self._load_history()


# ── code lab tab ─────────────────────────────────────────────────────────────

class CodeLabTab(QWidget):
    """Nova's code creation laboratory — write, test, fix, and save code."""

    def __init__(self):
        super().__init__()
        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 16, 16, 16); vl.setSpacing(10)

        # Header
        hdr = QLabel("Nova Code Lab  ⚗")
        hdr.setStyleSheet(f"font-size:14px;color:{C['glow']};letter-spacing:1px;")
        vl.addWidget(hdr)

        # ── Input panel ───────────────────────────────────────────────────────
        inp_frame = QFrame()
        inp_frame.setStyleSheet(
            f"QFrame{{background:{C['panel']};border:1px solid {C['border']};"
            f"border-radius:6px;padding:4px;}}"
        )
        il = QVBoxLayout(inp_frame); il.setContentsMargins(10, 10, 10, 10); il.setSpacing(8)

        # Description row
        desc_row = QHBoxLayout()
        desc_lbl = QLabel("Describe the code:")
        desc_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        desc_lbl.setFixedWidth(130)
        self._desc_inp = QLineEdit()
        self._desc_inp.setPlaceholderText(
            "e.g. 'A function that calculates Fibonacci numbers recursively'"
        )
        self._desc_inp.returnPressed.connect(self._create)
        desc_row.addWidget(desc_lbl); desc_row.addWidget(self._desc_inp, 1)
        il.addLayout(desc_row)

        # Category + attempts + button row
        ctl_row = QHBoxLayout()
        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        cat_lbl.setFixedWidth(65)
        self._cat_combo = QComboBox()
        self._cat_combo.addItems([
            "general", "math", "strings", "data", "algorithms",
            "utilities", "files", "networking", "patterns", "games",
        ])
        self._cat_combo.setFixedWidth(110)

        att_lbl = QLabel("Max attempts:")
        att_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        att_lbl.setFixedWidth(95)
        self._att_combo = QComboBox()
        self._att_combo.addItems(["1", "2", "3", "4", "5"])
        self._att_combo.setCurrentIndex(2)   # default 3
        self._att_combo.setFixedWidth(50)

        self._create_btn = QPushButton("⚗  Create")
        self._create_btn.setFixedWidth(110)
        self._create_btn.setStyleSheet(
            f"QPushButton{{background:{C['glow']};color:#000;border:none;"
            f"border-radius:4px;padding:5px 10px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{C['ok']};}}"
            f"QPushButton:disabled{{background:{C['border']};color:{C['dim']};}}"
        )
        self._create_btn.clicked.connect(self._create)

        ctl_row.addWidget(cat_lbl); ctl_row.addWidget(self._cat_combo)
        ctl_row.addSpacing(12)
        ctl_row.addWidget(att_lbl); ctl_row.addWidget(self._att_combo)
        ctl_row.addStretch()
        ctl_row.addWidget(self._create_btn)
        il.addLayout(ctl_row)

        vl.addWidget(inp_frame)

        # ── Status / progress ─────────────────────────────────────────────────
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color:{C['dim']};font-size:11px;")
        vl.addWidget(self._status_lbl)

        # ── Main splitter: iteration log | final code ─────────────────────────
        main_split = QSplitter(Qt.Orientation.Vertical)
        main_split.setHandleWidth(2)

        # Iteration log (top pane)
        log_frame = QWidget(); lfl = QVBoxLayout(log_frame)
        lfl.setContentsMargins(0, 0, 0, 0); lfl.setSpacing(4)
        log_hdr = QLabel("ATTEMPT LOG")
        log_hdr.setStyleSheet(f"color:{C['dim']};font-size:10px;letter-spacing:1px;padding:2px 0;")
        self._iter_log = QTextBrowser()
        self._iter_log.setStyleSheet(
            f"QTextBrowser{{background:#060612;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:11px;"
            f"color:#b8b8d8;padding:8px;line-height:1.4;}}"
        )
        lfl.addWidget(log_hdr); lfl.addWidget(self._iter_log)
        main_split.addWidget(log_frame)

        # Final code (bottom pane)
        code_frame = QWidget(); cfl = QVBoxLayout(code_frame)
        cfl.setContentsMargins(0, 0, 0, 0); cfl.setSpacing(4)
        code_hdr_row = QHBoxLayout()
        code_hdr = QLabel("FINAL CODE")
        code_hdr.setStyleSheet(f"color:{C['dim']};font-size:10px;letter-spacing:1px;padding:2px 0;")
        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedWidth(60)
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_code)
        code_hdr_row.addWidget(code_hdr); code_hdr_row.addStretch(); code_hdr_row.addWidget(self._copy_btn)

        self._code_view = QTextBrowser()
        self._code_view.setStyleSheet(
            f"QTextBrowser{{background:#050510;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:12px;"
            f"color:#c8e8b8;padding:8px;line-height:1.4;}}"
        )
        self._code_view.setPlaceholderText("Generated code will appear here…")
        cfl.addLayout(code_hdr_row); cfl.addWidget(self._code_view)
        main_split.addWidget(code_frame)

        main_split.setSizes([280, 280])
        vl.addWidget(main_split, 1)

        # ── Library browser ───────────────────────────────────────────────────
        lib_frame = QFrame()
        lib_frame.setStyleSheet(
            f"QFrame{{background:{C['panel']};border:1px solid {C['border']};"
            f"border-radius:6px;}}"
        )
        lib_layout = QVBoxLayout(lib_frame); lib_layout.setContentsMargins(10, 8, 10, 8); lib_layout.setSpacing(6)

        lib_hdr_row = QHBoxLayout()
        lib_hdr = QLabel("LIBRARY")
        lib_hdr.setStyleSheet(f"color:{C['dim']};font-size:10px;letter-spacing:1px;")
        self._lib_refresh_btn = QPushButton("↺")
        self._lib_refresh_btn.setFixedWidth(28)
        self._lib_refresh_btn.clicked.connect(self._load_library)
        lib_hdr_row.addWidget(lib_hdr); lib_hdr_row.addStretch(); lib_hdr_row.addWidget(self._lib_refresh_btn)
        lib_layout.addLayout(lib_hdr_row)

        lib_content = QSplitter(Qt.Orientation.Horizontal)
        lib_content.setHandleWidth(1)

        self._lib_list = QTextBrowser()
        self._lib_list.setOpenLinks(False)
        self._lib_list.anchorClicked.connect(self._on_lib_clicked)
        self._lib_list.setStyleSheet(
            f"QTextBrowser{{background:#070710;border:1px solid {C['border']};"
            f"font-size:11px;color:{C['text']};padding:6px;}}"
        )
        self._lib_list.setMaximumHeight(140)

        self._lib_view = QTextBrowser()
        self._lib_view.setStyleSheet(
            f"QTextBrowser{{background:#050510;border:1px solid {C['border']};"
            f"font-family:'Courier New',monospace;font-size:11px;"
            f"color:#c8e8b8;padding:6px;}}"
        )
        self._lib_view.setMaximumHeight(140)
        self._lib_view.setPlaceholderText("Click a file to view…")

        lib_content.addWidget(self._lib_list)
        lib_content.addWidget(self._lib_view)
        lib_content.setSizes([300, 600])
        lib_layout.addWidget(lib_content)
        vl.addWidget(lib_frame)

        # internal state
        self._final_code = ""

    # ── actions ───────────────────────────────────────────────────────────────

    def _create(self):
        desc = self._desc_inp.text().strip()
        if not desc:
            self._status_lbl.setText("Enter a description first.")
            return
        cat      = self._cat_combo.currentText()
        max_att  = int(self._att_combo.currentText())

        self._create_btn.setEnabled(False)
        self._iter_log.clear()
        self._code_view.clear()
        self._copy_btn.setEnabled(False)
        self._final_code = ""
        self._status_lbl.setText(f"Creating… (up to {max_att} attempts)")

        w = DaemonWorker(
            {"command": "code_create", "description": desc,
             "category": cat, "max_attempts": max_att},
            timeout=300,
        )
        w.result.connect(self._on_result)
        _launch(w)

    def _on_result(self, r: dict):
        self._create_btn.setEnabled(True)

        if "error" in r:
            self._status_lbl.setStyleSheet(f"color:{C['warn']};font-size:11px;")
            self._status_lbl.setText(f"Error: {r['error']}")
            return

        ok       = r.get("ok", False)
        attempts = r.get("attempts", 0)
        iters    = r.get("iterations", [])
        code     = r.get("code", "")
        path     = r.get("path", "")

        # ── render iteration log ──────────────────────────────────────────────
        import html as _h
        lines = []
        for it in iters:
            n = it.get("attempt", "?")
            if it.get("ok"):
                badge = f'<span style="color:{C["ok"]}">✓ PASS</span>'
            elif "error" in it:
                badge = f'<span style="color:{C["warn"]}">✗ ERROR ({_h.escape(str(it["error"])[:80])})</span>'
            else:
                badge = f'<span style="color:#c84a4a">✗ FAIL</span>'

            lines.append(
                f'<div style="margin-bottom:12px;">'
                f'<b style="color:{C["glow"]}">── Attempt {n} ──</b> {badge}<br/>'
            )
            raw_code = _h.escape(it.get("code","")[:800])
            if raw_code:
                lines.append(
                    f'<pre style="background:#040410;padding:6px;margin:4px 0;'
                    f'border-left:3px solid {C["border"]};font-size:10px;'
                    f'color:#b0c8a0;white-space:pre-wrap;">{raw_code}</pre>'
                )
            stdout = _h.escape((it.get("stdout","") or "")[:300]).strip()
            stderr = _h.escape((it.get("stderr","") or "")[:300]).strip()
            if stdout:
                lines.append(
                    f'<div style="color:{C["ok"]};font-size:10px;'
                    f'margin:2px 0;">stdout: {stdout}</div>'
                )
            if stderr:
                lines.append(
                    f'<div style="color:#c84a4a;font-size:10px;'
                    f'margin:2px 0;">stderr: {stderr}</div>'
                )
            if it.get("timed_out"):
                lines.append(
                    f'<div style="color:{C["warn"]};font-size:10px;">⏱ timed out</div>'
                )
            blocked = it.get("blocked", [])
            if blocked:
                lines.append(
                    f'<div style="color:{C["warn"]};font-size:10px;">'
                    f'blocked: {_h.escape(str(blocked))}</div>'
                )
            lines.append('</div>')

        self._iter_log.setHtml("".join(lines))
        # scroll to bottom
        self._iter_log.verticalScrollBar().setValue(
            self._iter_log.verticalScrollBar().maximum()
        )

        # ── final code pane ───────────────────────────────────────────────────
        if code:
            self._code_view.setPlainText(code)
            self._final_code = code
            self._copy_btn.setEnabled(True)

        # ── status bar ────────────────────────────────────────────────────────
        if ok:
            self._status_lbl.setStyleSheet(f"color:{C['ok']};font-size:11px;")
            saved = f"  →  saved to {Path(path).name}" if path else ""
            self._status_lbl.setText(
                f"✓ Success in {attempts} attempt{'s' if attempts != 1 else ''}{saved}"
            )
            self._load_library()
        else:
            self._status_lbl.setStyleSheet(f"color:#c84a4a;font-size:11px;")
            self._status_lbl.setText(
                f"✗ All {attempts} attempt{'s' if attempts != 1 else ''} failed  —  "
                f"last code shown above"
            )

    def _copy_code(self):
        if self._final_code:
            QApplication.clipboard().setText(self._final_code)
            self._copy_btn.setText("Copied!")
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("Copy"))

    # ── library ───────────────────────────────────────────────────────────────

    def _load_library(self):
        w = DaemonWorker({"command": "code_library_list"})
        w.result.connect(self._on_lib_list)
        _launch(w)

    def _on_lib_list(self, r: dict):
        import html as _h
        files = r.get("files", [])
        if not files:
            self._lib_list.setPlainText("Library is empty — create some code first.")
            return
        parts = []
        for f in files:
            name = _h.escape(f.get("name", ""))
            cat  = _h.escape(f.get("category", ""))
            path = _h.escape(f.get("path", ""))
            parts.append(
                f'<a href="lib:{path}" style="color:{C["glow"]};text-decoration:none;">{name}</a>'
                f' <span style="color:{C["dim"]};font-size:10px;">({cat})</span><br/>'
            )
        self._lib_list.setHtml("".join(parts))

    def _on_lib_clicked(self, url):
        path = url.toString()
        if path.startswith("lib:"):
            path = path[4:]
            w = DaemonWorker({"command": "code_library_get", "path": path})
            w.result.connect(self._on_lib_file)
            _launch(w)

    def _on_lib_file(self, r: dict):
        if "error" in r:
            self._lib_view.setPlainText(r["error"])
            return
        meta = r.get("metadata", {})
        code = r.get("code", "")
        desc = meta.get("description", "")
        header = f"# {desc}\n\n" if desc else ""
        self._lib_view.setPlainText(header + code)

    def load(self):
        """Called when tab becomes active."""
        self._load_library()


# ── main window ───────────────────────────────────────────────────────────────

class NovaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nova Cathedral")
        self.resize(1280, 820); self.setMinimumSize(900, 600)
        self._build_ui(); self._build_tray(); self._setup_timers()

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        splitter = QSplitter(Qt.Orientation.Horizontal); splitter.setHandleWidth(1)

        self._sidebar = Sidebar()
        self._sidebar.ritual_toggled.connect(self._ritual)
        self._sidebar.clear_session.connect(self._clear_session)
        self._sidebar.shutdown_req.connect(self._shutdown)
        self._sidebar.refresh_req.connect(self._poll)
        self._sidebar.reasoning_toggled.connect(self._toggle_reasoning)
        splitter.addWidget(self._sidebar)

        self._tabs = QTabWidget()
        self._tabs.currentChanged.connect(self._on_tab_change)

        self._chat_tab   = ChatTab(self._sidebar)
        self._mem_tab    = MemoryTab()
        self._refl_tab   = ReflectionsTab()
        self._evo_tab    = EvolutionTab()
        self._ora_tab    = OracleTab()
        self._res_tab    = ResonanceTab()
        self._log_tab    = LogTab()
        self._files_tab  = FilesTab()
        self._code_tab     = CodeTab()
        self._bridge_tab   = BridgeTab()
        self._plugin_tab   = PluginTab()
        self._goals_tab    = GoalsTab()
        self._sys_tab      = SysinfoTab()
        self._chapel_tab   = EntityChapelTab()
        self._rose_tab     = RoseWindowTab()
        self._builder_tab  = BuilderTab()
        self._lab_tab      = CodeLabTab()

        for label, tab in [
            ("Chat",    self._chat_tab),   ("Memory",    self._mem_tab),
            ("Reflect", self._refl_tab),   ("Evolution", self._evo_tab),
            ("Oracle",  self._ora_tab),    ("Resonance", self._res_tab),
            ("Chapel",  self._chapel_tab), ("Rose",      self._rose_tab),
            ("Log",     self._log_tab),    ("Files",     self._files_tab),
            ("Code",    self._code_tab),   ("Bridge",    self._bridge_tab),
            ("Plugins", self._plugin_tab), ("Goals",     self._goals_tab),
            ("Builder", self._builder_tab),("Lab",       self._lab_tab),
            ("System",  self._sys_tab),
        ]:
            self._tabs.addTab(tab, label)

        splitter.addWidget(self._tabs)
        splitter.setSizes([270, 1010]); splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)

        self._status_lbl   = QLabel("  Connecting…")
        self._harmony_lbl  = QLabel("  ◈ 0.50")
        self._harmony_lbl.setStyleSheet(f"color:{C['glow']};font-size:12px;")
        self.statusBar().addWidget(self._status_lbl, 1)
        self.statusBar().addPermanentWidget(self._harmony_lbl)
        self.statusBar().setSizeGripEnabled(False)

    def _build_tray(self):
        px = QPixmap(16,16); px.fill(Qt.GlobalColor.transparent)
        p  = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(C["glow"])); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2,2,12,12); p.end()
        self._tray = QSystemTrayIcon(QIcon(px), self)
        menu = QMenu()
        for label, slot in [("Show Nova", self.show), ("Hide to Tray", self.hide),
                             (None, None), ("Quit", QApplication.quit)]:
            if label is None: menu.addSeparator()
            else:
                a = QAction(label, self); a.triggered.connect(slot); menu.addAction(a)
        self._tray.setContextMenu(menu); self._tray.setToolTip("Nova Cathedral")
        self._tray.activated.connect(
            lambda r: (self.show() if self.isHidden() else self.hide())
            if r == QSystemTrayIcon.ActivationReason.Trigger else None
        )
        self._tray.show()

    def _setup_timers(self):
        t = QTimer(self); t.timeout.connect(self._poll); t.start(10_000)
        QTimer.singleShot(400, self._poll)

    def _poll(self):
        w = DaemonWorker({"command": "status"})
        w.result.connect(self._on_status); _launch(w)

    def _on_status(self, r):
        if "error" in r:
            self._status_lbl.setText(f"  Daemon offline — {r['error']}"); return
        res     = r.get("flow_resonance", 0)
        model   = r.get("model", "?")
        ritual  = "🕯️ RITUAL" if r.get("ritual_mode") else ""
        rsn     = " · reasoning" if r.get("reasoning_enabled") else ""
        web     = " · web" if r.get("web_search") else ""
        harmony = r.get("harmony_score", 0.5)
        self._status_lbl.setText(
            f"  {res:.4f} Hz  ·  {r.get('conversations',0)} memories  ·  {model}{rsn}{web}"
            + (f"  ·  {ritual}" if ritual else "")
        )
        # Harmony indicator
        h_col = C["ok"] if harmony >= 0.7 else C["warn"] if harmony >= 0.4 else "#c84a4a"
        self._harmony_lbl.setText(f"  ◈ {harmony:.2f}")
        self._harmony_lbl.setStyleSheet(f"color:{h_col};font-size:12px;")

        self._sidebar.update_status(r)
        self._chat_tab.set_model(model)
        self._chat_tab.update_state(res, r.get("conversations", 0), r.get("ritual_mode", False))
        self._res_tab.push(res)

    def _on_tab_change(self, idx):
        name = self._tabs.tabText(idx)
        if name == "Memory":     self._mem_tab.search()
        elif name == "Reflect":  self._refl_tab.load()
        elif name == "Evolution":self._evo_tab.load()
        elif name == "Resonance":self._res_tab.load(); self._res_tab.start_wave()
        elif name == "Goals":    self._goals_tab.load()
        elif name == "Files":    self._files_tab._browse()
        elif name == "Code":     self._code_tab.load()
        elif name == "Plugins":  self._plugin_tab.load()
        elif name == "System":   self._sys_tab.load()
        elif name == "Chapel":   self._chapel_tab.load()
        elif name == "Rose":     self._rose_tab.load()
        elif name == "Builder":  self._builder_tab.load()
        elif name == "Lab":      self._lab_tab.load()
        if name != "Resonance":  self._res_tab.stop_wave()
        # Log tab auto-tails via its own QTimer — no explicit load needed

    def _toggle_reasoning(self, on: bool):
        cmd = "reasoning_on" if on else "reasoning_off"
        w = DaemonWorker({"command": cmd})
        w.result.connect(lambda r: self._chat_tab.set_reasoning(on))
        _launch(w)

    def _ritual(self, state):
        w = DaemonWorker({"command": f"ritual_{state}"})
        w.result.connect(lambda _: self._poll()); _launch(w)

    def _clear_session(self):
        w = DaemonWorker({"command": "clear_session"})
        def _on_cleared(_):
            self._chat_tab._add_msg("system", "Session cleared — Nova starts fresh.")
            self._chat_tab.clear_history()
            self._chat_tab._refresh_context()
        w.result.connect(_on_cleared)
        _launch(w)

    def _shutdown(self):
        if QMessageBox.question(
            self, "Shutdown", "Shut down Nova Cathedral?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            _send({"command": "shutdown"})
            self._status_lbl.setText("  Nova Cathedral slumbers.")

    def closeEvent(self, event):
        event.ignore(); self.hide()
        self._tray.showMessage(
            "Nova Cathedral", "Running in background. Click tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information, 2500,
        )


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nova Cathedral")
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(QSS)

    splash = QLabel("Starting Nova Cathedral…")
    splash.setStyleSheet(
        f"background:{C['panel']};color:{C['glow']};font-size:16px;"
        f"letter-spacing:2px;padding:40px 80px;border:1px solid {C['border']};"
        f"border-radius:8px;"
    )
    splash.setWindowFlags(
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
    )
    splash.show(); app.processEvents()

    ok = _ensure_daemon()
    splash.close()

    if not ok:
        QMessageBox.critical(
            None, "Nova Cathedral",
            "Failed to start the daemon.\nCheck: ~/cathedral/logs/nova_cathedral.log"
        )
        sys.exit(1)

    win = NovaWindow(); win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
