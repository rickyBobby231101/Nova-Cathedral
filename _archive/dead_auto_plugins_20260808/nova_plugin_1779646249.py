class NovaPlugin:
    def __init__(self, system):
        self.system = system

    def process(self, input_data: dict) -> dict:
        return {}

def get_plugin():
    return NovaPlugin