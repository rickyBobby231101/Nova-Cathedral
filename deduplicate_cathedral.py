import hashlib
from pathlib import Path
from collections import defaultdict

base_dir = Path.home() / "Cathedral"
exts = [".py", ".json", ".html", ".md"]  # You can add other types here

hash_map = defaultdict(list)

def hash_file(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

# Scan files
for file in base_dir.rglob("*"):
    if file.is_file() and file.suffix in exts:
        try:
            file_hash = hash_file(file)
            hash_map[file_hash].append(file)
        except Exception as e:
            print(f"⚠️ Skipped {file}: {e}")

# Prompt for duplicates
total_removed = 0
for file_hash, files in hash_map.items():
    if len(files) > 1:
        print(f"\n🔁 Duplicate group ({len(files)} files):")
        for idx, f in enumerate(files):
            print(f"  [{idx}] {f}")
        keep = input("👉 Which one to keep? Enter index (or 's' to skip): ")
        if keep.isdigit():
            keep = int(keep)
            for idx, f in enumerate(files):
                if idx != keep:
                    try:
                        f.unlink()
                        print(f"🗑️ Deleted: {f}")
                        total_removed += 1
                    except Exception as e:
                        print(f"❌ Failed to delete {f}: {e}")
        else:
            print("⏩ Skipped this group.")

print(f"\n✅ Deduplication complete. {total_removed} files removed.")
