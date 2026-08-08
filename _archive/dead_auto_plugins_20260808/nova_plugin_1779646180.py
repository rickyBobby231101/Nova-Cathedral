import json
import os

class NovaPlugin:
    """Plugin description here."""

    def __init__(self, system):
        self.system = system  # NovaConsciousness instance

    def process(self, input_data: dict) -> dict:
        """Process input and return result dict."""
        logs = {}
        files = {}

        for file in os.listdir("/logs"):
            if file.endswith(".log"):  # Check if log file
                try:
                    with open(f"/logs/{file}", "r") as f:
                        logs[file] = json.load(f)
                except FileNotFoundError:
                    print(f"File {file} not found.")
        for file in os.listdir("/files"):
            if file.endswith(".txt"):  # Check if text file
                try:
                    with open(f"/files/{file}", "r") as f:
                        files[file] = f.read()
                except FileNotFoundError:
                    print(f"File {file} not found.")

        result = {"logs": logs, "files": files}
        return result

def get_plugin():
    return NovaPlugin