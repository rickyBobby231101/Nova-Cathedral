#!/usr/bin/env python3

import os
import shutil

# Define the base Cathedral path
BASE_PATH = os.path.expanduser("~/Cathedral")

# Define subdirectory targets
SUBDIRS = {
    "nova": ["nova", "daemon", "controller"],
    "interface": ["interface", "desktop", "ui", "html", "js", "css"],
    "logs": [".log"],
    "systemd": [".service"],
    "data": [".db", ".sqlite", ".json"],
    "plugins": ["plugin", "bridge"],
}

# Ensure subdirectories exist
for subdir in SUBDIRS:
    os.makedirs(os.path.join(BASE_PATH, subdir), exist_ok=True)

# Organize files based on name or extension
moved_files = []

for root, _, files in os.walk(BASE_PATH):
    for file in files:
        full_path = os.path.join(root, file)

        # Skip already moved files
        if any(full_path.startswith(os.path.join(BASE_PATH, s)) for s in SUBDIRS):
            continue

        lower = file.lower()
        target_dir = None

        # Match by file type or keyword
        for subdir, keywords in SUBDIRS.items():
            if any(k in lower for k in keywords):
                target_dir = subdir
                break

        if target_dir:
            dest_path = os.path.join(BASE_PATH, target_dir, file)
            try:
                shutil.move(full_path, dest_path)
                moved_files.append((file, target_dir))
            except Exception as e:
                print(f"⚠️ Could not move {file}: {e}")

# Report
print("\n✅ Organizing complete. Files moved:")
for file, target in moved_files:
    print(f"  📂 {file} → {target}/")

if not moved_files:
    print("📭 No files needed organizing.")
