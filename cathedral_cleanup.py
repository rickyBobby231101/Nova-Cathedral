import os
import shutil
from pathlib import Path

base = Path.home() / "Cathedral"
delete_ext = [".pyc", ".pyo"]
delete_patterns = [
    lambda n: n.endswith(".py.backup"),
    lambda n: "(1)" in n,
    lambda n: "_backup_" in n,
    lambda n: n == "__pycache__"
]

# Optional: Enable if you want ZIP/log cleanup
delete_archives = False
if delete_archives:
    delete_ext += [".zip", ".log"]

deleted = []

def recursive_cleanup(folder):
    for item in folder.rglob("*"):
        name = item.name
        if item.is_file() and (item.suffix in delete_ext or any(p(name) for p in delete_patterns)):
            try:
                item.unlink()
                deleted.append(f"🗑️ Deleted file: {item}")
            except Exception as e:
                print(f"❌ Failed to delete {item}: {e}")
        elif item.is_dir() and name == "__pycache__":
            try:
                shutil.rmtree(item)
                deleted.append(f"🗑️ Deleted folder: {item}")
            except Exception as e:
                print(f"❌ Failed to delete dir {item}: {e}")

recursive_cleanup(base)

# Output summary
if deleted:
    print("\n".join(deleted))
    print(f"\n✅ Cleanup complete. Total: {len(deleted)} items deleted.")
else:
    print("🧼 No unnecessary files found to delete.")
