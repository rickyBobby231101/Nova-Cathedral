import urllib.request
import urllib.parse


class NovaPlugin:
    """Current weather via wttr.in — structured output, robust to a missing
    or unknown city. input: {"city": "Austin"} (defaults to Austin).
    returns: {city, location, condition, temp, feels_like, humidity, wind,
              precip, emoji} or {error}."""

    _EMOJI = {
        "sunny": "☀️", "clear": "☀️", "partly": "⛅",
        "cloud": "☁️", "overcast": "☁️", "mist": "\U0001f32b️",
        "fog": "\U0001f32b️", "rain": "\U0001f327️", "drizzle": "\U0001f326️",
        "shower": "\U0001f326️", "snow": "❄️", "sleet": "\U0001f328️",
        "thunder": "⛈️", "storm": "⛈️",
    }

    def __init__(self, system):
        self.system = system

    def _emoji_for(self, condition: str) -> str:
        c = condition.lower()
        for key, em in self._EMOJI.items():
            if key in c:
                return em
        return "\U0001f321️"

    def process(self, input_data: dict) -> dict:
        city = (input_data or {}).get("city") or "Austin"
        fmt = "%l|%C|%t|%f|%h|%w|%p"
        url = "http://wttr.in/" + urllib.parse.quote(city) + "?format=" + urllib.parse.quote(fmt)
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                raw = r.read().decode().strip()
        except Exception as e:
            return {"error": f"weather lookup failed: {e}", "city": city}

        parts = raw.split("|")
        if len(parts) < 7 or "Unknown location" in raw or not parts[1].strip():
            return {"error": f"could not read weather for '{city}'", "city": city, "raw": raw}

        location, condition, temp, feels, humidity, wind, precip = (p.strip() for p in parts[:7])
        return {
            "city":       city,
            "location":   location,
            "condition":  condition,
            "temp":       temp,
            "feels_like": feels,
            "humidity":   humidity,
            "wind":       wind,
            "precip":     precip,
            "emoji":      self._emoji_for(condition),
        }


def get_plugin():
    return NovaPlugin
