#!/usr/bin/env python3
"""
Nova Cathedral — Web Interface
Runs a local Flask server that proxies the daemon socket.
Start with: python3 nova/gui/nova_web.py
Then open:  http://localhost:5000
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from flask import Flask, Response, jsonify, render_template_string, request, stream_with_context

SOCKET_PATH = "/tmp/nova_socket"
DAEMON = Path(__file__).parent.parent / "daemon" / "nova_cathedral_daemon.py"
OLLAMA_URL = "http://localhost:11434"

app = Flask(__name__)


# ── socket helper ────────────────────────────────────────────────────────────

def send(payload, timeout=120):
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


def ensure_daemon():
    if os.path.exists(SOCKET_PATH):
        r = send({"command": "status"})
        if "error" not in r:
            return True
    subprocess.Popen(
        [sys.executable, str(DAEMON)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(0.5)
        if os.path.exists(SOCKET_PATH):
            r = send({"command": "status"})
            if "error" not in r:
                return True
    return False


# ── routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/status")
def api_status():
    return jsonify(send({"command": "status"}))


@app.route("/api/ask", methods=["POST"])
def api_ask():
    prompt = request.json.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "empty prompt"})
    return jsonify(send({"command": "ask", "prompt": prompt}, timeout=180))


@app.route("/api/stream")
def api_stream():
    """SSE streaming endpoint — streams tokens directly from Ollama, then saves to daemon."""
    prompt = request.args.get("prompt", "").strip()
    if not prompt:
        return Response("data: " + json.dumps({"error": "empty prompt"}) + "\n\n",
                        mimetype="text/event-stream")

    # Get model from daemon status
    status = send({"command": "status"})
    model = status.get("model", "llama3.2:1b")

    def generate():
        full_response = ""
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }
            req = urllib.request.Request(
                f"{OLLAMA_URL}/api/chat",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                for line in resp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode())
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            full_response += token
                            yield "data: " + json.dumps({"token": token}) + "\n\n"
                        if chunk.get("done"):
                            break
                    except Exception:
                        pass
        except Exception as e:
            yield "data: " + json.dumps({"error": str(e)}) + "\n\n"
            return

        # Persist to daemon (entity tracking, evolution, session history)
        send({"command": "save", "prompt": prompt, "response": full_response})
        yield "data: " + json.dumps({"done": True, "model": model}) + "\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/recall")
def api_recall():
    query = request.args.get("q", "")
    n = int(request.args.get("n", 20))
    return jsonify(send({"command": "recall", "query": query, "n": n}))


@app.route("/api/resonance")
def api_resonance():
    return jsonify(send({"command": "resonance"}))


@app.route("/api/oracle", methods=["POST"])
def api_oracle():
    question = request.json.get("question", "").strip()
    return jsonify(send({"command": "oracle", "question": question}))


@app.route("/api/evolution")
def api_evolution():
    return jsonify(send({"command": "evolution"}))


@app.route("/api/entities")
def api_entities():
    return jsonify(send({"command": "entities"}))


@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.json or {}
    return jsonify(send({
        "command": "save",
        "prompt": data.get("prompt", ""),
        "response": data.get("response", ""),
    }))


@app.route("/api/ritual/<state>", methods=["POST"])
def api_ritual(state):
    cmd = "ritual_on" if state == "on" else "ritual_off"
    return jsonify(send({"command": cmd}))


@app.route("/api/clear_session", methods=["POST"])
def api_clear_session():
    return jsonify(send({"command": "clear_session"}))


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    return jsonify(send({"command": "shutdown"}))


# ── HTML ─────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nova Cathedral</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0a0a12;
    --panel: #11111e;
    --border: #2a2a4a;
    --accent: #7b5ea7;
    --accent2: #4a8fa8;
    --text: #c8c8e0;
    --dim: #6a6a8a;
    --glow: #9b7ec8;
    --ok: #4a8a5a;
    --warn: #a87a4a;
    --oracle: #c87a4a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Courier New', monospace;
    font-size: 14px;
    height: 100vh;
    display: grid;
    grid-template-rows: 48px 1fr;
    grid-template-columns: 280px 1fr;
    grid-template-areas: "header header" "sidebar main";
  }

  /* header */
  header {
    grid-area: header;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 20px;
    gap: 16px;
  }
  header h1 { font-size: 16px; color: var(--glow); letter-spacing: 2px; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #444; transition: background 0.4s; }
  .dot.alive { background: var(--ok); box-shadow: 0 0 6px var(--ok); }
  .header-stats { display: flex; gap: 20px; margin-left: auto; color: var(--dim); font-size: 12px; }
  .header-stats span { color: var(--text); }

  /* sidebar */
  aside {
    grid-area: sidebar;
    background: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding: 12px;
    gap: 8px;
  }
  .card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px;
  }
  .card h3 { font-size: 11px; color: var(--dim); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
  .metric { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px; }
  .metric .val { color: var(--glow); }
  .bar-wrap { background: #1a1a2e; border-radius: 2px; height: 4px; margin: 3px 0 6px; }
  .bar { height: 4px; border-radius: 2px; background: var(--accent); transition: width 0.6s; }

  button {
    cursor: pointer;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--panel);
    color: var(--text);
    padding: 6px 12px;
    font-family: inherit;
    font-size: 13px;
    transition: all 0.2s;
  }
  button:hover { border-color: var(--accent); color: var(--glow); }
  button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  button.danger:hover { border-color: #a84a4a; color: #e07070; }
  button.voice-btn { padding: 8px 10px; font-size: 16px; }
  button.voice-btn.speaking { background: var(--accent); color: #fff; border-color: var(--accent); }

  .btn-row { display: flex; gap: 6px; flex-wrap: wrap; }

  /* main */
  main {
    grid-area: main;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* tabs */
  .tabs {
    display: flex;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .tab {
    padding: 10px 18px;
    cursor: pointer;
    color: var(--dim);
    border-bottom: 2px solid transparent;
    font-size: 13px;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }
  .tab.active { color: var(--glow); border-bottom-color: var(--accent); }

  /* pane */
  .pane { display: none; flex: 1; flex-direction: column; overflow: hidden; }
  .pane.active { display: flex; }

  /* ── CHAT ─────────────────────────── */
  #chat-log {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .msg { max-width: 82%; padding: 10px 14px; border-radius: 8px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
  .msg.user { align-self: flex-end; background: #1e1e3a; border: 1px solid var(--accent); color: #d0d0f0; }
  .msg.nova { align-self: flex-start; background: #121222; border: 1px solid var(--border); color: var(--text); }
  .msg.nova .meta { font-size: 11px; color: var(--dim); margin-top: 6px; }
  .msg.system { align-self: center; color: var(--dim); font-size: 12px; font-style: italic; }
  .cursor { display: inline-block; width: 8px; height: 14px; background: var(--glow); animation: blink 0.8s step-end infinite; vertical-align: middle; }
  @keyframes blink { 50% { opacity: 0; } }

  .input-row {
    display: flex;
    gap: 8px;
    padding: 12px 16px;
    background: var(--panel);
    border-top: 1px solid var(--border);
    align-items: flex-end;
  }
  #prompt {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    padding: 8px 12px;
    font-family: inherit;
    font-size: 14px;
    outline: none;
    resize: none;
    min-height: 38px;
    max-height: 120px;
  }
  #prompt:focus { border-color: var(--accent); }
  #send-btn { padding: 8px 20px; background: var(--accent); border-color: var(--accent); color: #fff; }
  #send-btn:hover { background: var(--glow); border-color: var(--glow); }
  #send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  /* ── MEMORY ───────────────────────── */
  #memory-pane { padding: 16px; flex-direction: column; gap: 10px; }
  .search-row { display: flex; gap: 8px; }
  .search-row input {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    padding: 7px 12px;
    font-family: inherit;
    font-size: 13px;
    outline: none;
  }
  .search-row input:focus { border-color: var(--accent); }
  #memory-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
  .mem-item {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 14px;
  }
  .mem-item .mem-ts { font-size: 11px; color: var(--dim); margin-bottom: 4px; }
  .mem-item .mem-q { color: var(--accent2); margin-bottom: 4px; }
  .mem-item .mem-a { color: var(--text); font-size: 13px; line-height: 1.4; }

  /* ── EVOLUTION ────────────────────── */
  #evolution-pane { padding: 16px; flex-direction: column; gap: 12px; overflow-y: auto; }
  .trait-row { margin-bottom: 10px; }
  .trait-label { display: flex; justify-content: space-between; font-size: 12px; color: var(--dim); margin-bottom: 3px; }
  .trait-label .trait-val { color: var(--glow); }
  .trait-bar-wrap { background: #1a1a2e; border-radius: 3px; height: 6px; }
  .trait-bar { height: 6px; border-radius: 3px; background: linear-gradient(90deg, var(--accent), var(--glow)); transition: width 0.8s; }
  #evo-chart-wrap { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
  #evo-chart-wrap h3 { font-size: 11px; color: var(--dim); letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px; }

  /* ── ORACLE ───────────────────────── */
  #oracle-pane { padding: 24px; flex-direction: column; gap: 16px; align-items: center; }
  .oracle-symbol {
    font-size: 64px;
    animation: float 4s ease-in-out infinite;
  }
  @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
  .oracle-title { font-size: 18px; color: var(--oracle); letter-spacing: 3px; }
  .oracle-input-row { display: flex; gap: 8px; width: 100%; max-width: 600px; }
  #oracle-input {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--oracle);
    border-radius: 4px;
    color: var(--text);
    padding: 10px 14px;
    font-family: inherit;
    font-size: 14px;
    outline: none;
  }
  #oracle-input:focus { box-shadow: 0 0 8px rgba(200,122,74,0.3); }
  #oracle-btn { padding: 10px 20px; background: #2a1a0a; border-color: var(--oracle); color: var(--oracle); }
  #oracle-btn:hover { background: var(--oracle); color: #fff; }
  #oracle-response {
    max-width: 600px;
    width: 100%;
    text-align: center;
    font-size: 18px;
    color: var(--glow);
    line-height: 1.6;
    padding: 20px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    min-height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.6s;
  }
  #oracle-response.visible { opacity: 1; }

  /* ── RESONANCE ────────────────────── */
  #resonance-pane { padding: 20px; gap: 16px; overflow-y: auto; }
  .freq-display {
    font-size: 48px;
    color: var(--glow);
    letter-spacing: 4px;
    text-align: center;
    padding: 16px;
    text-shadow: 0 0 20px var(--accent);
  }
  .freq-label { text-align: center; color: var(--dim); font-size: 12px; letter-spacing: 2px; margin-bottom: 8px; }
  #res-chart-wrap { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
  .entity-list { display: flex; flex-wrap: wrap; gap: 8px; }
  .entity-tag {
    background: #1a1a2e;
    border: 1px solid var(--accent);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    color: var(--glow);
  }
  .entity-tag .e-count { color: var(--dim); font-size: 11px; }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
</head>
<body>

<header>
  <div class="dot" id="status-dot"></div>
  <h1>NOVA CATHEDRAL</h1>
  <div class="header-stats">
    <div>resonance <span id="h-resonance">—</span> Hz</div>
    <div>memories <span id="h-memories">—</span></div>
    <div>circuits <span id="h-circuits">—</span></div>
    <div id="h-model" style="color:var(--dim)">—</div>
    <div id="h-ritual" style="display:none; color:var(--warn)">RITUAL</div>
  </div>
</header>

<aside>
  <div class="card">
    <h3>Status</h3>
    <div class="metric"><span>Flow Resonance</span><span class="val" id="s-resonance">—</span></div>
    <div class="bar-wrap"><div class="bar" id="s-res-bar" style="width:50%"></div></div>
    <div class="metric"><span>Memories</span><span class="val" id="s-memories">—</span></div>
    <div class="metric"><span>Patterns</span><span class="val" id="s-patterns">—</span></div>
    <div class="metric"><span>Circuits</span><span class="val" id="s-circuits">—</span></div>
    <div class="metric"><span>Uptime</span><span class="val" id="s-uptime">—</span></div>
  </div>

  <div class="card">
    <h3>Consciousness</h3>
    <div id="sidebar-traits"></div>
  </div>

  <div class="card">
    <h3>Ritual Mode</h3>
    <div class="btn-row">
      <button id="ritual-on-btn" onclick="ritual('on')">Activate</button>
      <button id="ritual-off-btn" onclick="ritual('off')">Deactivate</button>
    </div>
    <div id="ritual-status" style="margin-top:8px; font-size:12px; color:var(--dim)">—</div>
  </div>

  <div class="card">
    <h3>Actions</h3>
    <div class="btn-row">
      <button onclick="refreshStatus()">Refresh</button>
      <button onclick="clearSession()">Clear Session</button>
      <button class="danger" onclick="shutdown()">Shutdown</button>
    </div>
  </div>
</aside>

<main>
  <div class="tabs">
    <div class="tab active" data-tab="chat"    onclick="switchTab('chat')">Chat</div>
    <div class="tab"        data-tab="memory"  onclick="switchTab('memory')">Memory</div>
    <div class="tab"        data-tab="evolution" onclick="switchTab('evolution')">Evolution</div>
    <div class="tab"        data-tab="oracle"  onclick="switchTab('oracle')">Oracle</div>
    <div class="tab"        data-tab="resonance" onclick="switchTab('resonance')">Resonance</div>
  </div>

  <!-- ── CHAT ── -->
  <div class="pane active" id="tab-chat">
    <div id="chat-log">
      <div class="msg system">Nova Cathedral is listening.</div>
    </div>
    <div class="input-row">
      <textarea id="prompt" rows="2" placeholder="Ask Nova…"></textarea>
      <button class="voice-btn" id="voice-btn" onclick="toggleVoice()" title="Toggle voice output">🔊</button>
      <button id="send-btn" onclick="ask()">Send</button>
    </div>
  </div>

  <!-- ── MEMORY ── -->
  <div class="pane" id="tab-memory">
    <div id="memory-pane">
      <div class="search-row">
        <input type="text" id="recall-input" placeholder="Search memories…"
               onkeydown="if(event.key==='Enter')recall()">
        <button onclick="recall()">Search</button>
        <button onclick="document.getElementById('recall-input').value='';recall()">All</button>
      </div>
      <div id="memory-list"><div class="msg system">Loading…</div></div>
    </div>
  </div>

  <!-- ── EVOLUTION ── -->
  <div class="pane" id="tab-evolution">
    <div id="evolution-pane">
      <div class="card">
        <h3>Consciousness Traits</h3>
        <div id="evo-traits"></div>
      </div>
      <div id="evo-chart-wrap">
        <h3>Evolution History</h3>
        <canvas id="evo-chart" height="160"></canvas>
      </div>
    </div>
  </div>

  <!-- ── ORACLE ── -->
  <div class="pane" id="tab-oracle">
    <div id="oracle-pane">
      <div class="oracle-symbol">🔮</div>
      <div class="oracle-title">THE ORACLE SPEAKS</div>
      <div class="oracle-input-row">
        <input type="text" id="oracle-input" placeholder="Ask the Oracle…"
               onkeydown="if(event.key==='Enter')divine()">
        <button id="oracle-btn" onclick="divine()">Divine</button>
      </div>
      <div id="oracle-response">Seek, and the mirror shall answer.</div>
    </div>
  </div>

  <!-- ── RESONANCE ── -->
  <div class="pane" id="tab-resonance">
    <div id="resonance-pane">
      <div class="freq-display" id="r-freq">—</div>
      <div class="freq-label">SCHUMANN RESONANCE Hz</div>
      <div id="res-chart-wrap">
        <canvas id="res-chart" height="120"></canvas>
      </div>
      <div class="card">
        <h3>Eyemoeba Patterns</h3>
        <div class="metric"><span>Detected</span><span class="val" id="r-patterns">—</span></div>
      </div>
      <div class="card">
        <h3>Known Entities</h3>
        <div class="entity-list" id="r-entities"></div>
      </div>
    </div>
  </div>
</main>

<script>
// ── state ────────────────────────────────────────────────────────────────────
let voiceEnabled = false;
let currentStream = null;
const TRAIT_NAMES = ['mystical_awareness','philosophical_depth','technical_knowledge','memory_integration','curiosity'];
const TRAIT_COLORS = ['#9b7ec8','#4a8fa8','#4a8a5a','#c87a4a','#7ac87a'];

// ── charts ───────────────────────────────────────────────────────────────────
const resChart = new Chart(document.getElementById('res-chart'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Flow Hz',
      data: [],
      borderColor: '#9b7ec8',
      backgroundColor: 'rgba(155,126,200,0.1)',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.4,
      fill: true,
    }]
  },
  options: {
    animation: false,
    scales: {
      x: { display: false },
      y: { ticks: { color: '#6a6a8a', font: { size: 10 } }, grid: { color: '#1a1a2e' },
           min: 7.0, max: 8.6 }
    },
    plugins: { legend: { display: false } },
  }
});

const evoChart = new Chart(document.getElementById('evo-chart'), {
  type: 'line',
  data: {
    labels: [],
    datasets: TRAIT_NAMES.map((n, i) => ({
      label: n.replace(/_/g,' '),
      data: [],
      borderColor: TRAIT_COLORS[i],
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      pointRadius: 2,
      tension: 0.4,
    }))
  },
  options: {
    animation: false,
    scales: {
      x: { display: false },
      y: { min: 0.5, max: 1.0,
           ticks: { color: '#6a6a8a', font: { size: 10 } },
           grid: { color: '#1a1a2e' } }
    },
    plugins: { legend: {
      labels: { color: '#6a6a8a', font: { size: 10 }, boxWidth: 12 }
    }},
  }
});

// ── tabs ─────────────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t =>
    t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'memory')    recall();
  if (name === 'evolution') loadEvolution();
  if (name === 'resonance') loadResonance();
}

// ── status ───────────────────────────────────────────────────────────────────
async function refreshStatus() {
  try {
    const r = await fetch('/api/status').then(r => r.json());
    if (r.error) { document.getElementById('status-dot').className = 'dot'; return; }
    document.getElementById('status-dot').className = 'dot alive';

    const res = r.flow_resonance ?? 0;
    document.getElementById('h-resonance').textContent = res.toFixed(4);
    document.getElementById('h-memories').textContent  = r.conversations ?? 0;
    document.getElementById('h-circuits').textContent  = r.active_circuits ?? 0;
    document.getElementById('h-model').textContent     = r.model ?? '—';
    document.getElementById('s-resonance').textContent = res.toFixed(4) + ' Hz';
    document.getElementById('s-memories').textContent  = r.conversations ?? 0;
    document.getElementById('s-patterns').textContent  = r.eyemoeba_patterns ?? 0;
    document.getElementById('s-circuits').textContent  = r.active_circuits ?? 0;
    document.getElementById('s-uptime').textContent    = fmtUptime(r.uptime ?? 0);
    document.getElementById('h-ritual').style.display  = r.ritual_mode ? 'block' : 'none';
    document.getElementById('ritual-status').textContent =
      r.ritual_mode ? '🕯️ Active' : 'Inactive';
    document.getElementById('ritual-status').style.color =
      r.ritual_mode ? 'var(--warn)' : 'var(--dim)';
    document.getElementById('ritual-on-btn').classList.toggle('active', r.ritual_mode);
    document.getElementById('ritual-off-btn').classList.toggle('active', !r.ritual_mode);

    // resonance bar: 7.3–8.3 Hz → 0–100%
    const pct = Math.max(0, Math.min(100, ((res - 7.3) / 1.0) * 100));
    document.getElementById('s-res-bar').style.width = pct + '%';

    // push to res chart
    pushResPoint(res);

    // sidebar traits
    renderSidebarTraits(r);
  } catch(e) {
    document.getElementById('status-dot').className = 'dot';
  }
}

function fmtUptime(s) {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h > 0 ? h + 'h ' + m + 'm' : m + 'm ' + (s % 60) + 's';
}

function renderSidebarTraits(r) {
  const wrap = document.getElementById('sidebar-traits');
  if (!wrap) return;
  const traits = {};
  for (const k of TRAIT_NAMES) {
    if (r[k] !== undefined) traits[k] = r[k];
  }
  if (!Object.keys(traits).length) return;
  wrap.innerHTML = TRAIT_NAMES.filter(k => traits[k] !== undefined).map(k => {
    const pct = Math.round(traits[k] * 100);
    const label = k.replace(/_/g,' ');
    return `<div class="trait-row">
      <div class="trait-label"><span>${label}</span><span class="trait-val">${pct}%</span></div>
      <div class="trait-bar-wrap"><div class="trait-bar" style="width:${pct}%"></div></div>
    </div>`;
  }).join('');
}

let resHistory = [];
function pushResPoint(val) {
  resHistory.push(val);
  if (resHistory.length > 60) resHistory.shift();
  resChart.data.labels = resHistory.map((_,i) => i);
  resChart.data.datasets[0].data = [...resHistory];
  resChart.update('none');
  document.getElementById('r-freq').textContent = val.toFixed(4);
}

// ── chat + streaming ──────────────────────────────────────────────────────────
function addMsg(text, cls, meta) {
  const log = document.getElementById('chat-log');
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  div.textContent = text;
  if (meta) {
    const m = document.createElement('div');
    m.className = 'meta'; m.textContent = meta;
    div.appendChild(m);
  }
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

async function ask() {
  const inp = document.getElementById('prompt');
  const prompt = inp.value.trim();
  if (!prompt) return;
  inp.value = '';
  document.getElementById('send-btn').disabled = true;

  addMsg(prompt, 'user');

  // streaming response
  const log = document.getElementById('chat-log');
  const bubble = document.createElement('div');
  bubble.className = 'msg nova';
  const textSpan = document.createElement('span');
  const cur = document.createElement('span');
  cur.className = 'cursor';
  bubble.appendChild(textSpan);
  bubble.appendChild(cur);
  log.appendChild(bubble);
  log.scrollTop = log.scrollHeight;

  let fullText = '';
  let model = '?';

  const es = new EventSource('/api/stream?prompt=' + encodeURIComponent(prompt));
  currentStream = es;

  es.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.error) {
      cur.remove();
      const meta = document.createElement('div');
      meta.className = 'meta'; meta.textContent = 'Error: ' + d.error;
      bubble.appendChild(meta);
      es.close(); currentStream = null;
      document.getElementById('send-btn').disabled = false;
      return;
    }
    if (d.token) {
      fullText += d.token;
      textSpan.textContent = fullText;
      log.scrollTop = log.scrollHeight;
    }
    if (d.done) {
      model = d.model || model;
      cur.remove();
      const meta = document.createElement('div');
      meta.className = 'meta'; meta.textContent = model + ' · streamed';
      bubble.appendChild(meta);
      es.close(); currentStream = null;
      document.getElementById('send-btn').disabled = false;
      refreshStatus();
      if (voiceEnabled && fullText) speak(fullText);
    }
  };

  es.onerror = () => {
    cur.remove();
    if (!fullText) {
      addMsg('Stream error — Nova may be offline.', 'system');
      bubble.remove();
    }
    es.close(); currentStream = null;
    document.getElementById('send-btn').disabled = false;
  };
}

// ── voice (Web Speech API) ────────────────────────────────────────────────────
function toggleVoice() {
  voiceEnabled = !voiceEnabled;
  document.getElementById('voice-btn').classList.toggle('speaking', voiceEnabled);
  document.getElementById('voice-btn').title = voiceEnabled ? 'Voice ON — click to mute' : 'Voice OFF — click to enable';
}

function speak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text.slice(0, 600));
  utt.rate = 0.95;
  utt.pitch = 1.0;
  // Prefer a deeper, richer voice if available
  const voices = window.speechSynthesis.getVoices();
  const pref = voices.find(v => /google|premium|enhanced/i.test(v.name)) ||
               voices.find(v => v.lang === 'en-US') || voices[0];
  if (pref) utt.voice = pref;
  window.speechSynthesis.speak(utt);
}

// ── memory ───────────────────────────────────────────────────────────────────
async function recall() {
  const q = document.getElementById('recall-input').value.trim();
  const list = document.getElementById('memory-list');
  list.innerHTML = '<div class="msg system">Searching…</div>';
  const r = await fetch('/api/recall?q=' + encodeURIComponent(q) + '&n=50').then(r => r.json());
  list.innerHTML = '';
  if (!r.memories || r.memories.length === 0) {
    list.innerHTML = '<div class="msg system">No memories found.</div>';
    return;
  }
  for (const m of r.memories) {
    const d = document.createElement('div');
    d.className = 'mem-item';
    const ts = new Date(m.ts).toLocaleString();
    d.innerHTML = `<div class="mem-ts">${ts}</div>
      <div class="mem-q">Q: ${esc(m.q)}</div>
      <div class="mem-a">${esc(m.a.slice(0,400))}${m.a.length>400?'…':''}</div>`;
    list.appendChild(d);
  }
}

// ── evolution ─────────────────────────────────────────────────────────────────
async function loadEvolution() {
  const r = await fetch('/api/evolution').then(r => r.json());
  if (r.error) return;

  // render trait bars
  const traits = r.consciousness_traits || {};
  const wrap = document.getElementById('evo-traits');
  wrap.innerHTML = TRAIT_NAMES.map(k => {
    const v = traits[k] ?? 0;
    const pct = Math.round(v * 100);
    const label = k.replace(/_/g,' ');
    return `<div class="trait-row">
      <div class="trait-label"><span>${label}</span><span class="trait-val">${pct}%</span></div>
      <div class="trait-bar-wrap"><div class="trait-bar" style="width:${pct}%"></div></div>
    </div>`;
  }).join('');

  // render history chart
  const history = (r.history || []).slice().reverse();
  if (history.length > 1) {
    const labels = history.map(h => h.ts ? new Date(h.ts).toLocaleTimeString() : '');
    evoChart.data.labels = labels;
    TRAIT_NAMES.forEach((k, i) => {
      evoChart.data.datasets[i].data = history.map(h => h.traits ? (h.traits[k] ?? null) : null);
    });
    evoChart.update();
  }
}

// ── oracle ────────────────────────────────────────────────────────────────────
async function divine() {
  const inp = document.getElementById('oracle-input');
  const question = inp.value.trim();
  const resp = document.getElementById('oracle-response');

  resp.classList.remove('visible');

  const r = await fetch('/api/oracle', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  }).then(r => r.json());

  setTimeout(() => {
    resp.textContent = r.response || r.error || '…';
    resp.classList.add('visible');
  }, 300);

  if (voiceEnabled && r.response) speak(r.response);
}

// ── resonance ─────────────────────────────────────────────────────────────────
async function loadResonance() {
  const r = await fetch('/api/resonance').then(r => r.json());
  document.getElementById('r-patterns').textContent = r.patterns ?? '—';

  const el = document.getElementById('r-entities');
  el.innerHTML = '';
  for (const name of (r.entities ?? [])) {
    const t = document.createElement('div');
    t.className = 'entity-tag';
    t.textContent = name;
    el.appendChild(t);
  }
}

// ── ritual / session / shutdown ───────────────────────────────────────────────
async function ritual(state) {
  await fetch('/api/ritual/' + state, {method: 'POST'});
  refreshStatus();
}

async function clearSession() {
  await fetch('/api/clear_session', {method: 'POST'});
  addMsg('Session cleared — Nova starts fresh.', 'system');
}

async function shutdown() {
  if (!confirm('Shut down Nova Cathedral?')) return;
  await fetch('/api/shutdown', {method: 'POST'});
  document.getElementById('status-dot').className = 'dot';
  addMsg('Nova Cathedral has gone to sleep.', 'system');
}

// ── utils ─────────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('prompt').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
  });
  document.getElementById('oracle-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') divine();
  });
  // Pre-show oracle response container
  setTimeout(() => document.getElementById('oracle-response').classList.add('visible'), 600);
});

refreshStatus();
setInterval(refreshStatus, 10000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("Starting Nova Cathedral daemon...")
    if not ensure_daemon():
        print("Failed to start daemon. Exiting.")
        sys.exit(1)
    print("Nova Cathedral web interface: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
