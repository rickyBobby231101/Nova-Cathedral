#!/usr/bin/env python3
import os
import time
import logging
import threading

log = logging.getLogger("nova_self_evolve")

PLUGIN_DIR = os.path.expanduser("~/nova_cathedral/plugins")


def write_plugin(name, code):
    path = os.path.join(PLUGIN_DIR, f"{name}.py")

    with open(path, "w") as f:
        f.write(code)

    os.chmod(path, 0o755)
    log.info(f"🧬 New plugin written: {name}")
    return path


def generate_plugin(nova, goal):
    if not hasattr(nova, "oracle"):
        return None

    prompt = f"""
You are an AI engineer inside a live system.

Create a Python plugin for Nova that helps achieve this goal:
{goal}

Rules:
- Must define run(context)
- Must be safe
- Must not break system
- Keep it under 100 lines
"""

    try:
        code = nova.oracle.ask(prompt)
        return code
    except Exception as e:
        log.error(f"Generation failed: {e}")
        return None


def evolve(nova):
    while True:
        try:
            if not hasattr(nova, "memory"):
                time.sleep(60)
                continue

            goals = getattr(nova.memory, "goals", [])

            if goals:
                goal = goals[0] if isinstance(goals[0], str) else goals[0].get("goal")

                log.info(f"🧬 Attempting evolution for goal: {goal}")

                code = generate_plugin(nova, goal)

                if code and "def run(context)" in code:
                    name = f"auto_plugin_{int(time.time())}"
                    write_plugin(name, code)

                    log.info("♻ Reloading Nova to activate new plugin...")
                    os.system("sudo systemctl restart nova")

                    return

        except Exception as e:
            log.error(f"Evolution error: {e}")

        time.sleep(120)


def run(context):
    nova = context.get("nova_system")

    if not nova:
        return

    threading.Thread(target=evolve, args=(nova,), daemon=True).start()

    log.info("🧬 Self-evolution engine active")
