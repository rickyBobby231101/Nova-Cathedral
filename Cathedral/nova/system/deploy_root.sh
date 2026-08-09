#!/usr/bin/env bash
# Switch the Nova Cathedral daemon from a user-level service to a root
# system service, WITHOUT losing Nova's data (keeps ~/cathedral via
# NOVA_CATHEDRAL_HOME). Run with:  sudo bash deploy_root.sh
set -e

REPO=/home/daniel/Nova-Cathedral
UNIT_SRC="$REPO/Cathedral/nova/system/nova-cathedral-root.service"
UNIT_DST=/etc/systemd/system/nova-cathedral.service

if [ "$(id -u)" -ne 0 ]; then
  echo "Run me with sudo:  sudo bash $0"; exit 1
fi

echo "==> Stopping the user-level daemon (if running)"
# The user service runs under daniel's session; stop it as daniel.
sudo -u daniel XDG_RUNTIME_DIR=/run/user/1000 systemctl --user stop nova-cathedral.service 2>/dev/null || true
sudo -u daniel XDG_RUNTIME_DIR=/run/user/1000 systemctl --user disable nova-cathedral.service 2>/dev/null || true

echo "==> Installing the root system service"
cp "$UNIT_SRC" "$UNIT_DST"
systemctl daemon-reload
systemctl enable nova-cathedral.service
systemctl restart nova-cathedral.service

echo "==> Waiting for the socket…"
for i in $(seq 1 20); do [ -S /tmp/nova_socket ] && break; sleep 1; done

echo "==> Verifying Nova woke with her real data (not an empty /root/cathedral)"
sleep 2
printf '{"command":"status"}\n' | socat -t 8 - UNIX-CONNECT:/tmp/nova_socket 2>/dev/null \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"  Nova awake={d['is_awakened']} as UID {__import__('os').getuid()==0 and 'root(daemon)' or '?'} | conversations={d['conversations']} | model={d['model']}\")" 2>/dev/null \
  || echo "  (socket not answering yet — check: sudo journalctl -u nova-cathedral -n 30)"

echo "==> Confirming the daemon is running as root"
ps -o user,pid,cmd -C python3 | grep nova_cathedral_daemon || true

echo
echo "Done. Nova now runs as root. The GUI stays a user service and reaches"
echo "the socket (now world-accessible). To watch: sudo journalctl -u nova-cathedral -f"
echo "To revert to user mode:  sudo systemctl disable --now nova-cathedral && \\"
echo "  systemctl --user enable --now nova-cathedral.service"
