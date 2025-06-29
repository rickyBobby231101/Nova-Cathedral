import os
import importlib.util
import traceback
import datetime
import uuid

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), '..', 'plugins')


def load_plugins():
    plugins = []
    for filename in os.listdir(PLUGIN_DIR):
        if filename.endswith(".py") and not filename.startswith("_"):
            path = os.path.join(PLUGIN_DIR, filename)
            name = os.path.splitext(filename)[0]

            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, "run"):
                    plugins.append((name, module))
                    print(f"[✔] Loaded plugin: {name}")
                else:
                    print(f"[!] Skipped {name}: no `run(context)` function")
            except Exception as e:
                print(f"[X] Failed to load {name}: {e}")
                traceback.print_exc()
    return plugins


def build_context():
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "system": "NovaDaemon",
        "source": "engine.py"
    }


def main():
    print("[Nova Engine] Booting up daemon core...")
    plugins = load_plugins()
    context = build_context()

    for name, plugin in plugins:
        try:
            print(f"[↪] Running plugin: {name}")
            plugin.run(context)
        except Exception as e:
            print(f"[‼] Plugin {name} threw an error:")
            traceback.print_exc()


if __name__ == "__main__":
    main()
