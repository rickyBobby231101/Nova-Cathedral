#!/usr/bin/env python3
import os, json, logging
log = logging.getLogger("nova_system_status")

def run(context):
    nova = context.get("nova_system")
    if not nova:
        return

    # Intercept input
    original_receive_input = nova.receive_input

    def patched_receive_input(user_input):
        stripped = user_input.strip().lower()
        if stripped == "system status":
            status = {}

            # --- Plugins ---
            status['plugins'] = list(nova.loaded_plugins.keys())

            # --- Goals ---
            goal_file = os.path.expanduser("~/nova_cathedral/memory/goals.json")
            if os.path.exists(goal_file):
                with open(goal_file, "r") as f:
                    try:
                        status['goals'] = json.load(f)
                    except:
                        status['goals'] = []
            else:
                status['goals'] = []

            # --- Evolution ---
            status['self_evolve'] = "active" if "nova_self_evolve" in nova.loaded_plugins else "inactive"
            status['plugin_count'] = len(status['plugins'])

            # --- Display result ---
            print("\n🔮 NOVA SYSTEM STATUS 🔮")
            for k, v in status.items():
                print(f"{k}: {v}")
            print("")

            return  # do not pass to original Echo

        # Otherwise, normal processing
        return original_receive_input(user_input)

    # Patch the Nova system
    nova.receive_input = patched_receive_input
