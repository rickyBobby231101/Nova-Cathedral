class NovaPlugin:
    """Plugin description here."""

    def __init__(self, system):
        self.system = system  # NovaConsciousness instance

    def process(self, input_data: dict) -> dict:
        plugins = {}
        for file_name, content in input_data.items():
            if "home" in file_name and not any("useful" in file_name for file_name in plugins):
                self.system.create_folder(file_name)
                folders = {"help", "docs": "Help", "tests": "Tests"}
                folder_name = folders.get(content["type"], "Unknown")
                self.system.create_folder(f"{file_name}/{folder_name}")
            elif "home" not in file_name:
                plugins[file_name] = content
        return {"plugins": list(plugins.values())}

def get_plugin():
    return NovaPlugin