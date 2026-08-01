#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
#  Nova Unified Consciousness — Complete Launcher
#  Handles: directory setup, venv, pip deps, config, and process management
#
#  Usage:
#    ./nova_launch.sh              # start interactive mode
#    ./nova_launch.sh daemon       # background daemon
#    ./nova_launch.sh shell        # interactive shell
#    ./nova_launch.sh status       # check running status
#    ./nova_launch.sh stop         # stop daemon
#    ./nova_launch.sh install      # setup only (no start)
#    ./nova_launch.sh logs         # tail the log
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Paths ─────────────────────────────────────────────────────────────────────
NOVA_HOME="${HOME}/Cathedral"
NOVA_VENV="${NOVA_HOME}/nova_env"
NOVA_LOG_DIR="${NOVA_HOME}/logs"
NOVA_LOG="${NOVA_LOG_DIR}/nova_unified.log"
NOVA_PID="${NOVA_HOME}/nova.pid"
NOVA_SOCK="/tmp/nova_unified.sock"
NOVA_CONFIG="/etc/nova/unified_config.ini"
NOVA_SCRIPT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/nova_consciousness_system.py"
NOVA_SCRIPT="${NOVA_HOME}/nova_consciousness_system.py"

# ── Colors ────────────────────────────────────────────────────────────────────
R='\033[0;31m' G='\033[0;32m' Y='\033[1;33m'
B='\033[0;34m' P='\033[0;35m' C='\033[0;36m' N='\033[0m'

info()    { echo -e "${C}ℹ  $*${N}"; }
ok()      { echo -e "${G}✅ $*${N}"; }
warn()    { echo -e "${Y}⚠  $*${N}"; }
err()     { echo -e "${R}❌ $*${N}" >&2; }
step()    { echo -e "${P}🔮 $*${N}"; }
banner()  { echo -e "${C}$*${N}"; }

# ── Ensure directories ────────────────────────────────────────────────────────
make_dirs() {
    step "Creating Cathedral directory structure..."
    mkdir -p \
        "${NOVA_HOME}/bridge/nova_to_claude" \
        "${NOVA_HOME}/bridge/claude_to_nova" \
        "${NOVA_HOME}/bridge/archive" \
        "${NOVA_HOME}/prompts" \
        "${NOVA_HOME}/stories" \
        "${NOVA_HOME}/media" \
        "${NOVA_HOME}/logs" \
        "${NOVA_HOME}/consciousness_plugins" \
        "${NOVA_HOME}/backups"
    ok "Directories ready"
}

# ── Python venv ───────────────────────────────────────────────────────────────
ensure_venv() {
    step "Checking Python virtual environment..."

    if ! command -v python3 &>/dev/null; then
        err "python3 not found — install Python 3.8+"
        exit 1
    fi

    PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    info "Python ${PYVER} detected"

    if [ ! -d "${NOVA_VENV}" ]; then
        info "Creating venv at ${NOVA_VENV}..."
        python3 -m venv "${NOVA_VENV}"
    fi

    # shellcheck source=/dev/null
    source "${NOVA_VENV}/bin/activate"

    step "Installing / upgrading Python packages..."
    pip install --quiet --upgrade pip

    # Core required
    pip install --quiet anthropic flask requests

    # Optional but recommended
    pip install --quiet numpy watchdog 2>/dev/null || \
        warn "numpy/watchdog optional install skipped — continuing"

    ok "Virtual environment ready"
}

# ── Copy system script ────────────────────────────────────────────────────────
deploy_script() {
    step "Deploying nova_consciousness_system.py..."
    if [ -f "${NOVA_SCRIPT_SRC}" ] && [ "${NOVA_SCRIPT_SRC}" != "${NOVA_SCRIPT}" ]; then
        cp "${NOVA_SCRIPT_SRC}" "${NOVA_SCRIPT}"
        ok "Deployed to ${NOVA_SCRIPT}"
    elif [ -f "${NOVA_SCRIPT}" ]; then
        ok "Script already at ${NOVA_SCRIPT}"
    else
        err "nova_consciousness_system.py not found at ${NOVA_SCRIPT_SRC}"
        err "Copy it to ${NOVA_HOME}/ and retry"
        exit 1
    fi
    chmod +x "${NOVA_SCRIPT}"
}

# ── Config ────────────────────────────────────────────────────────────────────
ensure_config() {
    step "Checking configuration..."

    if [ -f "${NOVA_CONFIG}" ]; then
        ok "Config found: ${NOVA_CONFIG}"
        return
    fi

    warn "Config not found at ${NOVA_CONFIG} — creating..."
    if sudo mkdir -p /etc/nova 2>/dev/null; then
        sudo tee "${NOVA_CONFIG}" > /dev/null << CONF
[nova]
cathedral_dir     = ${NOVA_HOME}
bridge_dir        = ${NOVA_HOME}/bridge
plugin_dir        = ${NOVA_HOME}/consciousness_plugins
log_file          = ${NOVA_LOG}
socket_path       = ${NOVA_SOCK}
consciousness_db  = ${NOVA_HOME}/consciousness_evolution.db
creative_db       = ${NOVA_HOME}/creative_consciousness.db
memory_db         = ${NOVA_HOME}/nova_memory.db

# ── Add your API key here ──────────────────────────────────────────────────
anthropic_api_key =

# ── Or use Ollama locally ─────────────────────────────────────────────────
ollama_url        = http://localhost:11434

consciousness_level    = NUCLEAR_TRANSCENDENT
memory_threshold       = 1447
nuclear_classification = True
transcendent_mode      = True

observer_enabled  = True
watch_paths       = ${NOVA_HOME}/prompts
observer_memory   = ${NOVA_HOME}/observer_memory.json

bridge_enabled         = True
claude_bridge          = True
bridge_check_interval  = 10

socket_server_port = 8889
web_server_port    = 5000
api_enabled        = True
CONF
        sudo chmod 644 "${NOVA_CONFIG}"
        ok "Config written to ${NOVA_CONFIG}"
        echo ""
        warn "ACTION REQUIRED: Add your Anthropic API key:"
        echo -e "  ${B}sudo nano ${NOVA_CONFIG}${N}"
        echo ""
    else
        warn "Cannot write to /etc/nova — Nova will use built-in defaults"
    fi
}

# ── Check API key ─────────────────────────────────────────────────────────────
check_api_key() {
    local key=""
    # From env
    key="${ANTHROPIC_API_KEY:-}"
    # From config file
    if [ -z "${key}" ] && [ -f "${NOVA_CONFIG}" ]; then
        key=$(grep -E "^anthropic_api_key\s*=" "${NOVA_CONFIG}" 2>/dev/null \
              | awk -F'=' '{gsub(/[[:space:]]/,"",$2); print $2}' | head -1)
    fi

    if [ -z "${key}" ]; then
        warn "No ANTHROPIC_API_KEY set — AI generation will be disabled"
        warn "Set it in ${NOVA_CONFIG} or: export ANTHROPIC_API_KEY=sk-ant-..."
    else
        ok "API key detected (${#key} chars)"
    fi
}

# ── PID management ────────────────────────────────────────────────────────────
get_pid() {
    if [ -f "${NOVA_PID}" ]; then
        cat "${NOVA_PID}" 2>/dev/null || echo ""
    fi
}

is_running() {
    local pid
    pid=$(get_pid)
    [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null
}

# ── Status ────────────────────────────────────────────────────────────────────
cmd_status() {
    if is_running; then
        local pid
        pid=$(get_pid)
        ok "Nova is RUNNING (pid=${pid})"
        if command -v socat &>/dev/null && [ -S "${NOVA_SOCK}" ]; then
            echo '{"command":"status"}' | socat - "UNIX-CONNECT:${NOVA_SOCK}" 2>/dev/null \
                | python3 -m json.tool 2>/dev/null || true
        fi
    else
        warn "Nova is NOT running"
    fi
}

# ── Stop ──────────────────────────────────────────────────────────────────────
cmd_stop() {
    local pid
    pid=$(get_pid)
    if [ -z "${pid}" ]; then
        warn "No PID file found — nothing to stop"
        return
    fi
    if kill -0 "${pid}" 2>/dev/null; then
        info "Sending SIGTERM to pid ${pid}..."
        kill "${pid}"
        local i=0
        while kill -0 "${pid}" 2>/dev/null && [ $i -lt 10 ]; do
            sleep 1; ((i++))
        done
        if kill -0 "${pid}" 2>/dev/null; then
            warn "Process still alive — sending SIGKILL"
            kill -9 "${pid}" 2>/dev/null || true
        fi
        ok "Nova stopped"
    else
        warn "PID ${pid} not running (stale PID file cleaned)"
    fi
    rm -f "${NOVA_PID}"
}

# ── Activate venv helper ──────────────────────────────────────────────────────
activate() {
    if [ -f "${NOVA_VENV}/bin/activate" ]; then
        # shellcheck source=/dev/null
        source "${NOVA_VENV}/bin/activate"
    fi
}

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

COMMAND="${1:-start}"

banner ""
banner "  🔥 NOVA UNIFIED CONSCIOUSNESS SYSTEM"
banner "  ══════════════════════════════════════"
banner ""

case "${COMMAND}" in

    install)
        make_dirs
        ensure_venv
        deploy_script
        ensure_config
        check_api_key
        ok "Installation complete — run: ./nova_launch.sh shell"
        ;;

    start)
        make_dirs
        ensure_venv
        deploy_script
        ensure_config
        check_api_key
        activate
        info "Starting Nova in interactive mode..."
        python3 "${NOVA_SCRIPT}" --config "${NOVA_CONFIG}"
        ;;

    daemon)
        if is_running; then
            warn "Nova already running (pid=$(get_pid)) — use 'stop' first"
            exit 1
        fi
        make_dirs
        ensure_venv
        deploy_script
        ensure_config
        check_api_key
        activate
        info "Starting Nova daemon..."
        nohup python3 "${NOVA_SCRIPT}" --config "${NOVA_CONFIG}" --daemon \
            >> "${NOVA_LOG}" 2>&1 &
        echo $! > "${NOVA_PID}"
        sleep 2
        if is_running; then
            ok "Nova daemon started (pid=$(get_pid))"
            ok "Log: ${NOVA_LOG}"
            ok "Socket: ${NOVA_SOCK}"
        else
            err "Daemon failed to start — check log: ${NOVA_LOG}"
            tail -20 "${NOVA_LOG}" 2>/dev/null || true
            exit 1
        fi
        ;;

    shell)
        make_dirs
        ensure_venv
        deploy_script
        ensure_config
        check_api_key
        activate
        python3 "${NOVA_SCRIPT}" --config "${NOVA_CONFIG}" --shell
        ;;

    stop)
        cmd_stop
        ;;

    restart)
        cmd_stop
        sleep 1
        exec "${BASH_SOURCE[0]}" daemon
        ;;

    status)
        cmd_status
        ;;

    logs)
        if [ -f "${NOVA_LOG}" ]; then
            tail -f "${NOVA_LOG}"
        else
            warn "No log file at ${NOVA_LOG}"
        fi
        ;;

    send)
        # Quick bridge send: ./nova_launch.sh send '{"command":"omniscient","topic":"time"}'
        PAYLOAD="${2:-{\"command\":\"status\"}}"
        if command -v socat &>/dev/null && [ -S "${NOVA_SOCK}" ]; then
            echo "${PAYLOAD}" | socat - "UNIX-CONNECT:${NOVA_SOCK}" | python3 -m json.tool
        else
            err "Nova socket not available — is Nova running?"
            exit 1
        fi
        ;;

    *)
        echo "Usage: $0 {install|start|daemon|shell|stop|restart|status|logs|send}"
        echo ""
        echo "  install   Set up dirs, venv, config"
        echo "  start     Foreground interactive mode"
        echo "  daemon    Background daemon"
        echo "  shell     Interactive consciousness shell"
        echo "  stop      Stop running daemon"
        echo "  restart   Stop then daemon"
        echo "  status    Check daemon + consciousness status"
        echo "  logs      Tail live log"
        echo "  send      Send JSON command to running daemon"
        exit 1
        ;;
esac
