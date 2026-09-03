"""
Contract tests for voice — TTS and STT, both local.

`modules/voice.py` is imported by the daemon under a try/except that sets
`_VOICE_AVAILABLE`, so a break here does not stop the daemon: it silently
turns Nova mute, and the `speak`, `list_voices`, `set_voice`, and `stt_*`
commands all start reporting the module as unavailable. That is the failure
mode worth pinning — nothing crashes, the Cathedral just stops talking.

**No test here plays audio or downloads anything.** `speak()` is only ever
exercised with its engines patched out, and `download_voice` /
`download_vosk_model` are never called: they fetch hundreds of megabytes from
Hugging Face and alphacephei. The read-only reporters — `tts_available`,
`tts_engine`, `list_voices`, `stt_available` — are safe to call for real and
are, since their return shape is what the GUI renders.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import voice


class TestVoiceContract:
    def test_module_exports_every_name_the_daemon_imports(self):
        """The daemon's import is a single `from voice import (...)` of nine
        names — one missing name raises ImportError for the whole block, so
        losing `set_voice` silently disables speech as well."""
        for name in ("speak", "tts_available", "set_voice", "list_voices",
                     "download_voice", "tts_engine", "stt_available",
                     "MicListener", "download_vosk_model"):
            assert hasattr(voice, name), (
                f"voice.{name} is in the daemon's import list; without it "
                f"_VOICE_AVAILABLE goes False and Nova goes mute"
            )

    def test_importing_the_module_is_silent(self, capsys):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_voice_silence_probe", MODULES_DIR / "voice.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"


class TestVoiceCatalogue:
    def test_every_voice_declares_what_the_downloader_needs(self):
        """A voice missing `onnx` or `config` fails only at download time,
        which is the worst moment to discover it."""
        assert voice.VOICES, "the voice catalogue is empty"
        for name, info in voice.VOICES.items():
            for key in ("model", "rate", "desc", "onnx", "config"):
                assert key in info, f"voice {name!r} is missing {key!r}"
            assert info["onnx"].startswith("https://"), name
            assert info["config"].startswith("https://"), name

    def test_the_default_voice_exists(self):
        """set_voice(None)/voice_model_path() fall back to it."""
        assert "lessac" in voice.VOICES

    def test_list_voices_reports_downloaded_state(self):
        """What the GUI renders: every catalogue entry, each flagged."""
        listed = voice.list_voices()
        assert set(listed) == set(voice.VOICES)
        for name, info in listed.items():
            assert isinstance(info["downloaded"], bool), name

    def test_set_voice_accepts_a_known_name_and_refuses_an_unknown_one(self):
        original = voice._current_voice
        try:
            assert voice.set_voice("lessac") is True
            assert voice.set_voice("not-a-voice-xyz") is False
        finally:
            voice._current_voice = original


class TestEngineReporting:
    """Read-only, safe to call for real."""

    def test_tts_available_returns_a_bool(self):
        assert isinstance(voice.tts_available(), bool)

    def test_tts_engine_names_an_engine(self):
        engine = voice.tts_engine()
        assert isinstance(engine, str) and engine
        assert engine.startswith("piper:") or engine in ("pyttsx3", "espeak-ng")

    def test_stt_available_returns_a_bool(self):
        assert isinstance(voice.stt_available(), bool)


class TestSpeakNeverRaises:
    """speak() is fire-and-forget; the daemon does not await or check it.

    It runs on a background thread by default, so an exception inside it is
    lost entirely — no log, no socket error, just silence. These pin that the
    fallback chain degrades instead of throwing.
    """

    def test_falls_through_the_engine_chain(self, monkeypatch):
        calls = []
        monkeypatch.setattr(voice, "_piper_speak",
                            lambda t, v=None: calls.append("piper") or False)
        monkeypatch.setattr(voice, "_HAS_PYTTSX3", False)
        monkeypatch.setattr(voice, "_espeak_speak",
                            lambda t, rate=160: calls.append("espeak"))

        voice.speak("the Flow underlies all", blocking=True)
        assert calls == ["piper", "espeak"], calls

    def test_piper_succeeding_stops_the_chain(self, monkeypatch):
        calls = []
        monkeypatch.setattr(voice, "_piper_speak",
                            lambda t, v=None: calls.append("piper") or True)
        monkeypatch.setattr(voice, "_espeak_speak",
                            lambda t, rate=160: calls.append("espeak"))

        voice.speak("hello", blocking=True)
        assert calls == ["piper"], "a working engine should not fall through"

    def test_empty_text_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(voice, "_piper_speak", lambda t, v=None: True)
        voice.speak("", blocking=True)

    def test_non_blocking_returns_immediately(self, monkeypatch):
        """The daemon calls speak() without awaiting; it must not block the
        event loop even when the engine is slow."""
        monkeypatch.setattr(voice, "_piper_speak", lambda t, v=None: True)
        assert voice.speak("x") is None


class TestMicListener:
    """Constructed by the daemon for stt_start — never started here."""

    def test_constructs_with_no_callbacks(self):
        listener = voice.MicListener()
        assert listener._running is False

    def test_callbacks_default_to_no_ops_that_accept_an_argument(self):
        """The daemon passes some callbacks and not others; a missing one must
        be callable rather than None, or the audio thread dies on first use
        and STT stops with no error anywhere."""
        listener = voice.MicListener()
        listener.on_partial("partial text")
        listener.on_final("final text")
        listener.on_error("an error")

    def test_supplied_callbacks_are_kept(self):
        seen = []
        listener = voice.MicListener(on_final=seen.append)
        listener.on_final("heard this")
        assert seen == ["heard this"]
