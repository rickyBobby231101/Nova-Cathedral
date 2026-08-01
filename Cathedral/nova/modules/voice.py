#!/usr/bin/env python3
"""
Nova voice module.

TTS priority:  Piper (neural, best quality) → pyttsx3 → espeak-ng
STT:           vosk + pyaudio (offline)

Install:
  pip install piper-tts pyttsx3 vosk --break-system-packages
  sudo apt install python3-pyaudio espeak-ng

Piper voices available (download with download_voice(name)):
  lessac    — neutral US male   (default)
  amy       — natural US female
  ryan      — clear US male
  alan      — British male
  libritts  — formal US, high quality
"""

import json
import os
import subprocess
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

# ── voice catalogue ───────────────────────────────────────────────────────────

VOICES = {
    "lessac":    {
        "model":   "en_US-lessac-medium",
        "rate":    22050,
        "desc":    "US neutral male (default)",
        "onnx":    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "config":  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    },
    "amy": {
        "model":   "en_US-amy-medium",
        "rate":    22050,
        "desc":    "US natural female",
        "onnx":    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "config":  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
    },
    "ryan": {
        "model":   "en_US-ryan-high",
        "rate":    22050,
        "desc":    "US clear male, high quality",
        "onnx":    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx",
        "config":  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx.json",
    },
    "alan": {
        "model":   "en_GB-alan-medium",
        "rate":    22050,
        "desc":    "British male",
        "onnx":    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx",
        "config":  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json",
    },
    "libritts": {
        "model":   "en_US-libritts_r-medium",
        "rate":    22050,
        "desc":    "US formal, high clarity",
        "onnx":    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx",
        "config":  "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json",
    },
}

VOICES_DIR    = Path.home() / "cathedral" / "models" / "voices"
_current_voice = "lessac"
_tts_lock      = threading.Lock()


# ── Piper TTS ─────────────────────────────────────────────────────────────────

def _piper_available() -> bool:
    return subprocess.run(["which", "piper"], capture_output=True).returncode == 0


def voice_model_path(voice_name: str = None) -> Path | None:
    name  = voice_name or _current_voice
    info  = VOICES.get(name)
    if not info:
        return None
    path = VOICES_DIR / f"{info['model']}.onnx"
    return path if path.exists() else None


def download_voice(voice_name: str = "lessac", progress_cb=None) -> bool:
    """Download a Piper voice model. Returns True on success."""
    info = VOICES.get(voice_name)
    if not info:
        if progress_cb:
            progress_cb(f"Unknown voice: {voice_name}. Available: {list(VOICES)}")
        return False

    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path   = VOICES_DIR / f"{info['model']}.onnx"
    config_path = VOICES_DIR / f"{info['model']}.onnx.json"

    if onnx_path.exists() and config_path.exists():
        return True

    for url, dest in [(info["onnx"], onnx_path), (info["config"], config_path)]:
        if dest.exists():
            continue
        if progress_cb:
            progress_cb(f"Downloading {dest.name}…")
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            if progress_cb:
                progress_cb(f"Download failed: {e}")
            return False

    if progress_cb:
        progress_cb(f"Voice '{voice_name}' ready.")
    return True


def set_voice(voice_name: str) -> bool:
    global _current_voice
    if voice_name not in VOICES:
        return False
    _current_voice = voice_name
    return True


def _piper_speak(text: str, voice_name: str = None) -> bool:
    """Synthesize with Piper and play via aplay. Returns True on success."""
    if not _piper_available():
        return False
    model = voice_model_path(voice_name)
    if not model:
        return False
    rate  = VOICES.get(voice_name or _current_voice, {}).get("rate", 22050)
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        proc = subprocess.run(
            ["piper", "--model", str(model), "--output_file", tmp_path],
            input=text[:800].encode(),
            capture_output=True,
        )
        if proc.returncode != 0:
            return False

        subprocess.Popen(
            ["aplay", "-q", tmp_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # Clean up after a delay
        threading.Timer(15, lambda: Path(tmp_path).unlink(missing_ok=True)).start()
        return True
    except Exception:
        return False


# ── pyttsx3 fallback ──────────────────────────────────────────────────────────

try:
    import pyttsx3 as _pyttsx3
    _HAS_PYTTSX3 = True
except ImportError:
    _HAS_PYTTSX3 = False


def _pyttsx3_speak(text: str, rate: int = 165):
    try:
        engine = _pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.say(text[:600])
        engine.runAndWait()
        engine.stop()
    except Exception:
        pass


# ── espeak fallback ────────────────────────────────────────────────────────────

def _espeak_speak(text: str, rate: int = 160):
    try:
        subprocess.run(
            ["espeak-ng", "-s", str(rate), text[:600]],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass


# ── public API ─────────────────────────────────────────────────────────────────

def speak(text: str, voice_name: str = None, blocking: bool = False):
    """Speak text using the best available engine."""
    def _run():
        with _tts_lock:
            if _piper_speak(text, voice_name):
                return
            if _HAS_PYTTSX3:
                _pyttsx3_speak(text)
                return
            _espeak_speak(text)

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def tts_available() -> bool:
    if _piper_available() and voice_model_path():
        return True
    if _HAS_PYTTSX3:
        return True
    return subprocess.run(["which", "espeak-ng"], capture_output=True).returncode == 0


def tts_engine() -> str:
    if _piper_available() and voice_model_path():
        return f"piper:{_current_voice}"
    if _HAS_PYTTSX3:
        return "pyttsx3"
    return "espeak-ng"


def list_voices() -> dict:
    available = {}
    for name, info in VOICES.items():
        path = VOICES_DIR / f"{info['model']}.onnx"
        available[name] = {**info, "downloaded": path.exists()}
    return available


# ── STT (vosk) ────────────────────────────────────────────────────────────────

VOSK_MODEL_DIR = Path.home() / "cathedral" / "models" / "vosk-model-small-en-us-0.15"
VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

try:
    import vosk as _vosk
    _HAS_VOSK = True
except ImportError:
    _HAS_VOSK = False

try:
    import pyaudio as _pyaudio
    _HAS_PYAUDIO = True
except ImportError:
    _HAS_PYAUDIO = False


def stt_available() -> bool:
    return _HAS_VOSK and _HAS_PYAUDIO and VOSK_MODEL_DIR.exists()


def download_vosk_model(progress_cb=None) -> bool:
    if VOSK_MODEL_DIR.exists():
        return True
    if not _HAS_VOSK:
        if progress_cb:
            progress_cb("vosk not installed — pip install vosk --break-system-packages")
        return False
    dest = VOSK_MODEL_DIR.parent
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "vosk_model.zip"
    if progress_cb:
        progress_cb("Downloading vosk model (~40 MB)…")
    try:
        urllib.request.urlretrieve(VOSK_MODEL_URL, zip_path)
        if progress_cb:
            progress_cb("Extracting…")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest)
        zip_path.unlink(missing_ok=True)
        if progress_cb:
            progress_cb("Vosk model ready.")
        return True
    except Exception as e:
        if progress_cb:
            progress_cb(f"Download failed: {e}")
        return False


def get_vosk_model():
    if not _HAS_VOSK or not VOSK_MODEL_DIR.exists():
        return None
    try:
        _vosk.SetLogLevel(-1)
        return _vosk.Model(str(VOSK_MODEL_DIR))
    except Exception:
        return None


class MicListener:
    RATE    = 16000
    CHUNK   = 4000

    def __init__(self, on_partial=None, on_final=None, on_error=None):
        self.on_partial = on_partial or (lambda t: None)
        self.on_final   = on_final   or (lambda t: None)
        self.on_error   = on_error   or (lambda e: None)
        self._running   = False
        self._thread    = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        if not stt_available():
            self.on_error("STT unavailable — install vosk + pyaudio and download model.")
            return
        try:
            model  = get_vosk_model()
            if not model:
                self.on_error("Could not load vosk model.")
                return
            rec    = _vosk.KaldiRecognizer(model, self.RATE)
            pa     = _pyaudio.PyAudio()
            stream = pa.open(rate=self.RATE, channels=1,
                             format=_pyaudio.paInt16, input=True,
                             frames_per_buffer=self.CHUNK)
            stream.start_stream()
            while self._running:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text", "").strip()
                    if text:
                        self.on_final(text)
                else:
                    partial = json.loads(rec.PartialResult()).get("partial", "")
                    if partial:
                        self.on_partial(partial)
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception as e:
            self.on_error(str(e))
