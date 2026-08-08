import urllib.request

class NovaPlugin:
    """Plugin description here."""

    def __init__(self, system):
        self.system = system  # NovaConsciousness instance

    def process(self, input_data: dict) -> dict:
        url = "http://wttr.in/{city}?format=%l:+%C+%t"
        response = urllib.request.urlopen(url.format(city=input_data["city"]))
        data = response.read().decode()
        return {"city": input_data["city"], "weather": data}


def get_plugin():
    return NovaPlugin