import os
import shutil
from pathlib import Path

base = Path.home() / "Cathedral"

# Folder targets
targets = {
    "nova": base / "nova",
    "plugins": base / "plugins",
    "interface": base / "interface",
    "utils": base / "utils",
    "data": base / "data",
    "logs": base / "logs",
    "voice": base / "voice_cache",
}

# Keyword mapping
file_keywords = {
    "nova": ["nova_", "daemon", "transcendent", "nuclear"],
    "plugins": ["plugin", "bridge", "consciousness_plugin"],
    "interface": ["gui", "interface", ".html", ".qml", ".js"],
    "utils": ["builder", "tracker", "organize", "helper", "tool", "fix", "setup"],
    "data": [".db", ".jsonl"],
    "logs": [".log"],
    "voice": ["_speech_", "_voice_", "voice_cache"],
}

excluded_dirs = {p.name for p in targets.values()}
excluded_dirs.update(["_archive_old", "__pycache__"])

def should_move(file, keywords):
    name = file.name.lower()
    return any(k in name or name.endswith(k) for k in keywords)

def move_file(file, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(file), str(dest_dir / file.name))
        print(f"✅ Moved: {file.name} → {dest_dir.name}")
    except Exception as e:
        print(f"❌ Failed to move {file.name}: {e}")

def organize_cathedral():
    for item in base.iterdir():
        if item.is_file():
            moved = False
            for target, keywords in file_keywords.items():
                if should_move(item, keywords):
                    move_file(item, targets[target])
                    moved = True
                    break
            if not moved:
                print(f"⚠️  Skipped (no match): {item.name}")
        elif item.is_dir() and item.name not in excluded_dirs:
            print(f"📁 Skipped directory: {item.name}")

if __name__ == "__main__":
    organize_cathedral()
