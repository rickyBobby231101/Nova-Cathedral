#!/usr/bin/env python3
import time
import threading
import logging
import json
import os

log = logging.getLogger("nova_autonomous")

GOAL_FILE = os.path.expanduser("~/nova_cathedral/memory/goals.json")


def load_goals():
    if not os.path.exists(GOAL_FILE):
        return []
    try:
        with open(GOAL_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_goals(goals):
    os.makedirs(os.path.dirname(GOAL_FILE), exist_ok=True)
    with open(GOAL_FILE, "w") as f:
        json.dump(goals, f, indent=2)


def add_goal(goal):
    goals = load_goals()
    goals.append({
        "goal": goal,
        "priority": 1,
        "created": time.time()
    })
    save_goals(goals)
    return goals


def prioritize():
    goals = load_goals()
    goals.sort(key=lambda g: g["priority"], reverse=True)
    return goals


def autonomous_loop(nova):
    while True:
        try:
            goals = prioritize()
            if goals:
                g = goals[0]["goal"]
                log.info(f"🔮 Nova contemplating goal: {g}")

                if hasattr(nova, "oracle"):
                    response = nova.oracle.ask(
                        f"How should I approach this goal: {g}"
                    )
                    log.info(f"Oracle insight: {response}")

            time.sleep(60)

        except Exception as e:
            log.error(f"Autonomous loop error: {e}")
            time.sleep(60)


def run(context):
    nova = context.get("nova_system")

    if not nova:
        return

    original = nova.receive_input

    def intercept(user_input):
        if user_input.startswith("remember "):
            goal = user_input.replace("remember ", "")
            add_goal(goal)
            return f"🧠 Goal stored: {goal}"

        if user_input == "prioritize tasks":
            goals = prioritize()
            if not goals:
                return "No goals stored."
            return "\n".join(
                [f"{i+1}. {g['goal']}" for i, g in enumerate(goals)]
            )

        if user_input == "direct builder":
            goals = prioritize()
            if not goals:
                return "No goals available."
            return f"🔧 Builder should focus on: {goals[0]['goal']}"

        return original(user_input)

    nova.receive_input = intercept

    threading.Thread(
        target=autonomous_loop,
        args=(nova,),
        daemon=True
    ).start()

    log.info("🧠 Autonomous cognition activated")
