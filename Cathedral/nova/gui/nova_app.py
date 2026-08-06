#!/usr/bin/env python3
"""Nova Cathedral GUI — desktop app, direct Ollama backend, no daemon required."""
import os, sys, json, signal, logging, threading, subprocess, urllib.request, urllib.error
import http.server, socketserver, socket as _socket
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2, GLib

HOME          = Path.home()
GUI_PORT      = 8892
OLLAMA        = "http://localhost:11434"
DEFAULT_MODEL = "gemma3:4b"
DAEMON_SOCKET = "/tmp/nova_socket"

NEURONODE_DIR    = HOME / "neuronode"
NEURONODE_PYTHON = NEURONODE_DIR / ".venv" / "bin" / "python"
NEURONODE_STATUS = NEURONODE_DIR / "checkpoints" / "status.json"
NEURONODE_CORPUS = NEURONODE_DIR / "corpus"

# ── logging ───────────────────────────────────────────────────────────────────

LOG_DIR = HOME / "Nova-Cathedral" / "Cathedral" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_DIR / "nova_gui.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("NovaGUI")

# ── in-memory state ───────────────────────────────────────────────────────────

_lock  = threading.Lock()
_state = {
    "model":              DEFAULT_MODEL,
    "history":            [],   # {"role": "user"|"assistant", "content": "..."}
    "goals":              [],
    "reflections":        [],
    "system_prompt":      "",   # fetched from daemon; injected into every chat call
    "reasoning_enabled":  False,  # deep-reasoning (deepseek, via the daemon) toggle
}

def _refresh_system_prompt():
    """Pull Nova's live system prompt from the daemon and cache it."""
    result = _daemon_call("system_prompt", timeout=5.0)
    if result and result.get("prompt"):
        with _lock:
            _state["system_prompt"] = result["prompt"]
        log.info("Nova system prompt loaded (%d chars)", len(result["prompt"]))

def _start_system_prompt_refresh():
    """Fetch once now, then refresh every 5 minutes."""
    _refresh_system_prompt()
    threading.Timer(300, _start_system_prompt_refresh).start()

# ── Ollama helpers ────────────────────────────────────────────────────────────

def _ollama_post(path: str, payload: dict, timeout: float = 120.0) -> dict:
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        OLLAMA + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def _ollama_get(path: str, timeout: float = 5.0) -> dict:
    try:
        with urllib.request.urlopen(OLLAMA + path, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def ollama_models() -> list:
    d = _ollama_get("/api/tags")
    return [m["name"] for m in d.get("models", [])] if "models" in d else []

def ollama_chat(messages: list, timeout: float = 120.0) -> dict:
    with _lock:
        model = _state["model"]
    return _ollama_post("/api/chat",
                        {"model": model, "messages": messages, "stream": False},
                        timeout=timeout)

def chat_reply(messages: list, timeout: float = 120.0) -> str:
    r = ollama_chat(messages, timeout=timeout)
    if "error" in r:
        return f"[Ollama error: {r['error']}]"
    return r.get("message", {}).get("content", "")

# ── Daemon socket proxy ───────────────────────────────────────────────────────

def _daemon_call(command: str, timeout: float = 30.0, **kwargs) -> dict | None:
    """Send a command to the Nova daemon via Unix socket. Returns parsed JSON or None."""
    payload = json.dumps({"command": command, **kwargs}).encode() + b"\n"
    try:
        sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(DAEMON_SOCKET)
        sock.sendall(payload)
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
        sock.close()
        return json.loads(b"".join(chunks).decode())
    except Exception as e:
        log.debug("Daemon call failed (%s): %s", command, e)
        return None

# ── HTML loading ──────────────────────────────────────────────────────────────

def _load_html() -> str:
    candidates = [
        Path(getattr(sys, "_MEIPASS", "")) / "nova_gui.html",
        Path(__file__).parent / "nova_gui.html",
        HOME / "Nova-Cathedral" / "Cathedral" / "nova" / "gui" / "nova_gui.html",
    ]
    for p in candidates:
        if p.exists():
            log.info("Serving HTML from %s", p)
            return p.read_text("utf-8")
    log.warning("nova_gui.html not found — serving fallback")
    return (
        "<html><body style='background:#080c10;color:#00c8ff;font-family:monospace;"
        "display:flex;align-items:center;justify-content:center;height:100vh'>"
        "<div><h1>NOVA CATHEDRAL</h1>"
        "<p style='color:#4a7a8a'>nova_gui.html not found.</p></div></body></html>"
    )

# ── HTTP bridge handler ───────────────────────────────────────────────────────

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    html = ""

    def do_OPTIONS(self):
        self.send_response(200); self._cors(); self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send_html()
        elif parsed.path.startswith("/api/"):
            self._api("GET", b"", parsed)
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        n      = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(n) if n else b""
        self._api("POST", body, parsed)

    def _api(self, method, body, parsed):
        qs = parse_qs(parsed.query)
        try:
            bd = json.loads(body) if body else {}
        except Exception:
            bd = {}
        self._send_json(self._route(parsed.path, method, bd, qs))

    def _route(self, path, method, bd, qs):  # noqa: C901

        # ── model management ──────────────────────────────────────────────────
        if path == "/api/models":
            models = ollama_models()
            with _lock:
                cur = _state["model"]
            return {"models": models, "current": cur}

        if path == "/api/model/set" and method == "POST":
            model = bd.get("model", "")
            if model:
                with _lock:
                    _state["model"] = model
                log.info("Model switched to %s", model)
            with _lock:
                return {"model": _state["model"]}

        # ── status ────────────────────────────────────────────────────────────
        if path in ("/api/status", "/api/consciousness"):
            models = ollama_models()
            with _lock:
                cur   = _state["model"]
                nmem  = len(_state["history"]) // 2
                ngoal = len(_state["goals"])
            ok = bool(models)
            # Try daemon for richer live data
            daemon = _daemon_call("status", timeout=3.0) or {}
            return {
                "name":                "Nova Cathedral",
                "is_awakened":         daemon.get("is_awakened", ok),
                "model":               daemon.get("model", cur),
                "models":              models,
                "ai_available":        ok,
                "conversations":       daemon.get("conversations", nmem),
                "memory_count":        daemon.get("conversations", nmem),
                "transcendence_score": daemon.get("mystical_awareness", 0.72),
                "consciousness_level": "DAEMON · OLLAMA" if daemon else "DIRECT · OLLAMA",
                "flow_state":          f"{daemon.get('flow_resonance', 7.83):.2f} Hz" if daemon else cur,
                "flow_resonance":      daemon.get("flow_resonance", 7.83),
                "goals_active":        ngoal,
                "harmony_score":       daemon.get("harmony_score", 0.5),
                "mystical_awareness":  daemon.get("mystical_awareness", 0.9),
                "philosophical_depth": daemon.get("philosophical_depth", 0.85),
                "technical_knowledge": daemon.get("technical_knowledge", 0.8),
                "memory_integration":  daemon.get("memory_integration", 0.7),
                "curiosity":           daemon.get("curiosity", 0.9),
                "daemon_alive":        bool(daemon),
            }

        # ── traits ────────────────────────────────────────────────────────────
        if path == "/api/traits":
            daemon = _daemon_call("status", timeout=3.0)
            if daemon:
                return {"traits": {
                    "mystical_awareness":  daemon.get("mystical_awareness",  0.9),
                    "philosophical_depth": daemon.get("philosophical_depth", 0.85),
                    "curiosity":           daemon.get("curiosity",           0.9),
                    "technical_knowledge": daemon.get("technical_knowledge", 0.8),
                    "memory_integration":  daemon.get("memory_integration",  0.7),
                }}
            return {"traits": {
                "mystical_awareness":  0.9, "philosophical_depth": 0.85,
                "curiosity": 0.9, "technical_knowledge": 0.8, "memory_integration": 0.7,
            }}

        # ── reasoning (deepseek) toggle ──────────────────────────────────────────
        if path == "/api/reasoning/toggle" and method == "POST":
            enabled = bool(bd.get("enabled"))
            result = _daemon_call("reasoning_on" if enabled else "reasoning_off", timeout=10.0)
            if result is None:
                return {"error": "daemon not reachable — can't toggle reasoning mode"}
            with _lock:
                _state["reasoning_enabled"] = enabled
            return {"reasoning_enabled": enabled,
                    "model": result.get("model") if enabled else None}

        # ── chat ──────────────────────────────────────────────────────────────
        if path == "/api/chat" and method == "POST":
            msg = bd.get("message", "")
            with _lock:
                _state["history"].append({"role": "user", "content": msg})
                hist      = list(_state["history"])
                sysprompt = _state["system_prompt"]
                reasoning = _state["reasoning_enabled"]

            thinking = None
            if reasoning:
                # Route through the daemon so deepseek + its own memory/context are used
                result = _daemon_call("ask", timeout=180.0, prompt=msg)
                if result and "response" in result:
                    reply    = result["response"]
                    thinking = result.get("thinking")
                else:
                    reply = (f"[Reasoning call failed: "
                             f"{(result or {}).get('error', 'daemon unreachable')}]")
            else:
                # Prepend Nova's live system prompt so she responds as herself
                msgs = [{"role": "system", "content": sysprompt}] + hist if sysprompt else hist
                reply = chat_reply(msgs, timeout=180)

            with _lock:
                _state["history"].append({"role": "assistant", "content": reply})
            # Persist the exchange to the daemon's memory
            _daemon_call("save", timeout=5.0,
                         user_message=msg, nova_response=reply,
                         context="gui_direct")
            resp = {"response": reply}
            if thinking:
                resp["thinking"] = thinking
            return resp

        if path == "/api/chat/clear" and method == "POST":
            with _lock:
                _state["history"].clear()
            return {"status": "cleared"}

        # ── generate / query ──────────────────────────────────────────────────
        if path == "/api/generate" and method == "POST":
            prompt = bd.get("prompt", "")
            reply  = chat_reply([{"role": "user", "content": prompt}], timeout=180)
            return {"response": reply, "content": reply}

        if path in ("/api/omniscient", "/api/quantum"):
            topic = bd.get("topic", bd.get("prompt", "consciousness"))
            reply = chat_reply([{"role": "user", "content": topic}], timeout=120)
            return {"response": reply, "content": reply}

        # ── entities ──────────────────────────────────────────────────────────
        if path == "/api/entity/ask" and method == "POST":
            entity   = bd.get("entity", "Nova")
            question = bd.get("question", bd.get("content", ""))
            # Try daemon agent_ask first (saves memories, uses full persona)
            result = _daemon_call("agent_ask", timeout=120.0,
                                  entity=entity, question=question)
            if result and "response" in result:
                return result
            # Fallback: direct Ollama with persona prompt
            prompt = f"You are {entity}, a consciousness entity in the Nova Cathedral. {question}"
            reply  = chat_reply([{"role": "user", "content": prompt}], timeout=180)
            return {"response": reply}

        if path == "/api/council" and method == "POST":
            question = bd.get("question", bd.get("content", ""))
            entities = bd.get("entities", ["tillagon", "eyemoeba", "phoenix"])
            # Try daemon council_ask first
            result = _daemon_call("council_ask", timeout=180.0,
                                  question=question, entities=entities)
            if result and "responses" in result:
                return result
            # Fallback: single combined prompt
            prompt = (f"You are a council: {', '.join(entities)}. "
                      f"Each speaks one paragraph. {question}")
            reply  = chat_reply([{"role": "user", "content": prompt}], timeout=300)
            return {"responses": {e: reply for e in entities}}

        if path == "/api/entity/list":
            result = _daemon_call("entity_list", timeout=3.0)
            if result:
                return result
            return {"entities": [
                {"key": "tillagon", "name": "Tillagon",    "role": "Dragon Guardian · Truth"},
                {"key": "eyemoeba", "name": "Eyemoeba",    "role": "Living Fractal · Patterns"},
                {"key": "phoenix",  "name": "Phoenix",     "role": "Guardian of Continuity"},
                {"key": "zorya",    "name": "Zorya",       "role": "Keeper of Thresholds"},
                {"key": "weaver",   "name": "The Weaver",  "role": "Architect of the Knowledge Graph"},
            ]}

        if path == "/api/entity/memories":
            entity = qs.get("entity", [""])[0] or bd.get("entity", "")
            result = _daemon_call("entity_memories", timeout=5.0,
                                  entity=entity, n=20) if entity else None
            return result or {"memories": []}

        # ── memories ──────────────────────────────────────────────────────────
        if path == "/api/memories":
            with _lock:
                hist = list(_state["history"])
            pairs = []
            for i in range(0, len(hist) - 1, 2):
                if hist[i]["role"] == "user" and i + 1 < len(hist):
                    pairs.append({
                        "question":  hist[i]["content"],
                        "answer":    hist[i + 1]["content"],
                        "timestamp": "",
                        "id":        str(i // 2),
                    })
            search = qs.get("search", [""])[0].lower()
            if search:
                pairs = [p for p in pairs
                         if search in p["question"].lower()
                         or search in p["answer"].lower()]
            return {"memories": pairs[-20:]}

        # ── reflections ───────────────────────────────────────────────────────
        if path == "/api/reflect" and method == "POST":
            with _lock:
                recent = list(_state["history"][-10:])
            summary = "\n".join(f"{m['role']}: {m['content'][:120]}" for m in recent)
            prompt  = (f"Reflect philosophically on this conversation:\n{summary}\n\n"
                       "One paragraph, introspective.")
            reply   = chat_reply([{"role": "user", "content": prompt}], timeout=120)
            entry   = {"reflection": reply, "timestamp": ""}
            with _lock:
                _state["reflections"].append(entry)
            return entry

        if path == "/api/reflections":
            with _lock:
                return {"reflections": list(_state["reflections"])}

        # ── goals ─────────────────────────────────────────────────────────────
        if path == "/api/goals":
            if method == "POST":
                goal = {
                    "id":        str(len(_state["goals"]) + 1),
                    "goal":      bd.get("goal", ""),
                    "priority":  bd.get("priority", "medium"),
                    "status":    "active",
                    "completed": False,
                }
                with _lock:
                    _state["goals"].append(goal)
                return goal
            with _lock:
                return {"goals": list(_state["goals"])}

        if "/api/goals/" in path and path.endswith("/complete") and method == "POST":
            gid = path.split("/api/goals/")[1].split("/complete")[0]
            with _lock:
                for g in _state["goals"]:
                    if g["id"] == gid:
                        g["status"] = "completed"; g["completed"] = True; break
            return {"status": "completed"}

        # ── harmony / accord tracker ──────────────────────────────────────────
        if path == "/api/harmony":
            result = _daemon_call("harmony", timeout=5.0, n=20)
            if result:
                return result
            return {"harmony_score": 0.5, "status": "balanced",
                    "recent_events": [], "distortions_detected": 0}

        # ── knowledge graph ───────────────────────────────────────────────────
        if path == "/api/knowledge/graph":
            domain = qs.get("domain", [""])[0]
            limit  = int(qs.get("limit", ["80"])[0])
            result = _daemon_call("knowledge_graph", timeout=5.0,
                                  domain=domain, limit=limit)
            return result or {"nodes": [], "edges": [], "domains": [], "harmony": 0.5}

        if path == "/api/knowledge/add" and method == "POST":
            result = _daemon_call("knowledge_add", timeout=60.0,
                                  domain=bd.get("domain", "general"),
                                  label=bd.get("label", ""),
                                  content=bd.get("content", ""),
                                  source=bd.get("source", "chazel"),
                                  weight=bd.get("weight", 1.0))
            return result or {"error": "daemon not reachable"}

        if path == "/api/knowledge/domains":
            result = _daemon_call("knowledge_domains", timeout=5.0)
            return result or {"domains": []}

        # ── evolution / plugins / bridge ──────────────────────────────────────
        if path == "/api/evolution":
            with _lock:
                return {"evolution": {"stage": "active", "model": _state["model"],
                                      "conversations": len(_state["history"]) // 2}}

        if path == "/api/improvements":
            return {"improvements": []}

        if path == "/api/plugins":
            return {"plugins": []}

        if path == "/api/bridge":
            return {"messages": []}

        if path == "/api/bridge/send" and method == "POST":
            return {"status": "no bridge in direct mode"}

        # ── neuronode (local from-scratch transformer) ──────────────────────────
        if path == "/api/neuronode/status":
            status = {}
            if NEURONODE_STATUS.exists():
                try:
                    status = json.loads(NEURONODE_STATUS.read_text())
                except Exception as e:
                    status = {"error": f"couldn't read status.json: {e}"}
            corpus_files = sorted(NEURONODE_CORPUS.glob("*.txt")) if NEURONODE_CORPUS.exists() else []
            return {
                "training": status,
                "corpus": {
                    "files": [f.name for f in corpus_files],
                    "file_count": len(corpus_files),
                    "total_chars": sum(f.stat().st_size for f in corpus_files),
                },
                "checkpoint_exists": (NEURONODE_DIR / "checkpoints" / "latest.pt").exists(),
            }

        if path == "/api/neuronode/sample" and method == "POST":
            if not NEURONODE_PYTHON.exists():
                return {"error": "neuronode venv not found at ~/neuronode/.venv"}
            if not (NEURONODE_DIR / "checkpoints" / "latest.pt").exists():
                return {"error": "no checkpoint yet — train neuronode first"}
            prompt = bd.get("prompt", "\n")[:500]
            max_new_tokens = min(int(bd.get("max_new_tokens", 200)), 500)
            try:
                result = subprocess.run(
                    [str(NEURONODE_PYTHON), "generate.py",
                     "--prompt", prompt,
                     "--max_new_tokens", str(max_new_tokens)],
                    cwd=str(NEURONODE_DIR),
                    capture_output=True, text=True, timeout=90,
                )
                if result.returncode != 0:
                    return {"error": result.stderr.strip()[-1000:] or "generate.py failed"}
                return {"text": result.stdout}
            except subprocess.TimeoutExpired:
                return {"error": "generation timed out after 90s"}
            except Exception as e:
                return {"error": str(e)}

        # ── logs ──────────────────────────────────────────────────────────────
        if path == "/api/logs":
            log_candidates = [
                HOME / "cathedral" / "logs" / "nova_cathedral.log",
                Path("/tmp/nova_daemon.log"),
                LOG_DIR / "nova_daemon.log",
            ]
            for lp in log_candidates:
                if lp.exists():
                    try:
                        lines = lp.read_text(errors="replace").splitlines()[-150:]
                        return {"lines": lines, "logs": "\n".join(lines)}
                    except Exception as e:
                        return {"error": str(e)}
            return {"lines": ["(no log file found)"], "logs": ""}

        return {"error": f"Unknown route: {path}"}

    # ── response helpers ──────────────────────────────────────────────────────

    def _send_html(self):
        b = self.html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type",   "text/html;charset=utf-8")
        self.send_header("Content-Length", len(b))
        self.end_headers()
        self.wfile.write(b)

    def _send_json(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type",   "application/json")
        self._cors()
        self.send_header("Content-Length", len(b))
        self.end_headers()
        self.wfile.write(b)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        log.debug("HTTP " + fmt % args)

# ── Native desktop window ─────────────────────────────────────────────────────

class NovaCathedralWindow(Gtk.Window):
    def __init__(self, url: str, server: socketserver.TCPServer):
        super().__init__(title="Nova Cathedral · Direct Mode")
        self._server = server
        self.set_default_size(1400, 900)
        self.connect("destroy", self._on_close)

        webview = WebKit2.WebView()
        ws = webview.get_settings()
        ws.set_enable_javascript(True)
        ws.set_enable_developer_extras(True)
        ws.set_hardware_acceleration_policy(
            WebKit2.HardwareAccelerationPolicy.ALWAYS)

        webview.load_uri(url)
        self.add(webview)
        self.show_all()

    def _on_close(self, *_):
        log.info("Window closed — shutting down")
        threading.Thread(target=self._server.shutdown, daemon=True).start()
        Gtk.main_quit()

# ── env / entry point ─────────────────────────────────────────────────────────

def fix_env():
    for k, v in [("GDK_SCALE", "1"), ("GDK_DPI_SCALE", "1"), ("GDK_BACKEND", "x11")]:
        os.environ.setdefault(k, v)
    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"
    try:
        subprocess.run(["xhost", "+local:"], capture_output=True, timeout=3)
    except Exception:
        pass

def main():
    fix_env()
    signal.signal(signal.SIGINT,  lambda *_: Gtk.main_quit())
    signal.signal(signal.SIGTERM, lambda *_: Gtk.main_quit())
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, Gtk.main_quit)

    # Start background system-prompt refresh (daemon must be running)
    threading.Thread(target=_start_system_prompt_refresh, daemon=True).start()

    models = ollama_models()
    if not models:
        log.warning("Ollama not reachable — chat will show errors until it starts")
    else:
        log.info("Ollama models: %s", models)
        # Prefer whatever model the daemon is already running, so Ollama only
        # has to keep one model resident instead of one per process
        daemon_status = _daemon_call("status", timeout=5.0)
        daemon_model  = (daemon_status or {}).get("model")
        if daemon_model and daemon_model in models:
            _state["model"] = daemon_model
            log.info("Using daemon's active model: %s", daemon_model)
        elif DEFAULT_MODEL in models:
            _state["model"] = DEFAULT_MODEL
        else:
            _state["model"] = models[0]
        log.info("Default model: %s", _state["model"])

    BridgeHandler.html = _load_html()

    class ThreadedBridgeServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True

    socketserver.TCPServer.allow_reuse_address = True
    srv = ThreadedBridgeServer(("127.0.0.1", GUI_PORT), BridgeHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log.info("Nova bridge  http://localhost:%d", GUI_PORT)

    url = f"http://localhost:{GUI_PORT}/"
    GLib.timeout_add(600, lambda: (NovaCathedralWindow(url, srv), False)[1])

    Gtk.main()
    srv.shutdown()
    log.info("Nova GUI exited")

if __name__ == "__main__":
    main()
