class NovaPlugin:
    """Nova plugin for reading system files and evolving."""

    def __init__(self, system):
        self.system = system  # NovaConsciousness instance
        self.file_list = []

    def process(self, input_data: dict) -> dict:
        """Process input data."""
        if 'files' in input_data and 'evolve' in input_data['files']:
            for file in input_data['files']['evolve']:
                try:
                    with open(file, 'r') as f:
                        self.file_list.append(f.read())
                except FileNotFoundError:
                    print(f"Error: File '{file}' not found.")

        return {'files': self.file_list}

def get_plugin():
    return NovaPlugin