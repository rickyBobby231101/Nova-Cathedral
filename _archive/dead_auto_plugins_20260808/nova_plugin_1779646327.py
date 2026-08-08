class NovaPlugin:
    """Nova Cathedral plugin."""

    def __init__(self, system):
        self.system = system  # NovaConsciousness instance

    def process(self, input_data: dict) -> dict:
        """Process input and return result dict."""
        processed_data = {}
        for key, value in input_data.items():
            if isinstance(value, str):
                processed_data[key] = "Pluralized" + value
            else:
                processed_data[key] = value
        return processed_data


def get_plugin():
    """Get Nova Plugin instance."""
    return NovaPlugin