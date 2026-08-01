#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Nova Cathedral — Build Script
# Compiles daemon and GUI into standalone binaries via PyInstaller.
#
# Usage:
#   ./build.sh              # build both
#   ./build.sh daemon       # daemon only
#   ./build.sh gui          # GUI only
#   ./build.sh install      # build both + update systemd service
#
# Output:
#   dist/nova-daemon/nova-daemon   ← background daemon
#   dist/nova-gui/nova-gui         ← desktop GUI
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
DIST="$REPO/dist"
BUILD_LOG="$REPO/build.log"

# ── helpers ───────────────────────────────────────────────────────────────────

log()  { echo "[build] $*"; }
fail() { echo "[build] ERROR: $*" >&2; exit 1; }

check_deps() {
    python3 -c "import PyInstaller" 2>/dev/null \
        || fail "PyInstaller not found — run: pip3 install --break-system-packages pyinstaller"
    python3 -c "import yaml"   2>/dev/null || fail "PyYAML not found — run: pip3 install pyyaml"
    python3 -c "import psutil" 2>/dev/null || fail "psutil not found — run: pip3 install psutil"
}

build_target() {
    local spec="$1"
    local name="$2"
    log "Building $name …"
    python3 -m PyInstaller \
        --noconfirm \
        --clean \
        --distpath "$DIST" \
        --workpath "$REPO/build_work" \
        --log-level WARN \
        "$spec" \
        2>&1 | tee -a "$BUILD_LOG"
    if [[ -x "$DIST/$name/$name" ]]; then
        log "$name built → $DIST/$name/$name"
    else
        fail "$name binary not found after build — check $BUILD_LOG"
    fi
}

install_service() {
    local daemon_bin="$DIST/nova-daemon/nova-daemon"
    local service_file="$HOME/.config/systemd/user/nova-cathedral.service"

    [[ -x "$daemon_bin" ]] || fail "Daemon binary not found — build first"

    log "Stopping nova-cathedral service …"
    systemctl --user stop nova-cathedral 2>/dev/null || true

    log "Writing updated systemd service …"
    cat > "$service_file" << EOF
[Unit]
Description=Nova Cathedral Daemon — Rose Cathedral of Knowledge
After=network.target

[Service]
Type=simple
ExecStart=$daemon_bin
WorkingDirectory=$REPO
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

    systemctl --user daemon-reload
    systemctl --user enable nova-cathedral
    loginctl enable-linger "$USER"
    systemctl --user start nova-cathedral
    sleep 2
    systemctl --user is-active nova-cathedral \
        && log "nova-cathedral service is active — running compiled binary" \
        || fail "Service failed to start — check: journalctl --user -u nova-cathedral"
}

# ── entry point ───────────────────────────────────────────────────────────────

mkdir -p "$REPO/build_work"
> "$BUILD_LOG"

check_deps

TARGET="${1:-both}"

case "$TARGET" in
    daemon)
        build_target "$REPO/nova-daemon.spec" "nova-daemon"
        ;;
    gui)
        build_target "$REPO/nova-gui.spec" "nova-gui"
        ;;
    install)
        build_target "$REPO/nova-daemon.spec" "nova-daemon"
        build_target "$REPO/nova-gui.spec"    "nova-gui"
        install_service
        ;;
    both|*)
        build_target "$REPO/nova-daemon.spec" "nova-daemon"
        build_target "$REPO/nova-gui.spec"    "nova-gui"
        log ""
        log "Both targets built."
        log "Run './build.sh install' to switch the systemd service to the compiled binary."
        ;;
esac

log "Done. Binaries in $DIST/"
