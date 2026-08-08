import math
from datetime import datetime, timezone


class NovaPlugin:
    """Moon phase for a given date (or now). Pure calculation, no network —
    fits Zorya's domain of sacred time and thresholds.

    input_data: {"date": "YYYY-MM-DD"}  (optional; defaults to today, UTC)
    returns:    {"date","phase_name","illumination_pct","age_days","emoji"}
    """

    _PHASES = [
        (0.0,   "New Moon",        "🌑"),
        (0.125, "Waxing Crescent", "🌒"),
        (0.25,  "First Quarter",   "🌓"),
        (0.375, "Waxing Gibbous",  "🌔"),
        (0.5,   "Full Moon",       "🌕"),
        (0.625, "Waning Gibbous",  "🌖"),
        (0.75,  "Last Quarter",    "🌗"),
        (0.875, "Waning Crescent", "🌘"),
    ]
    _SYNODIC = 29.53058867          # mean length of a lunar cycle, days
    # A known new moon reference: 2000-01-06 18:14 UTC (Julian-ish anchor).
    _KNOWN_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

    def __init__(self, system):
        self.system = system

    def process(self, input_data: dict) -> dict:
        raw = (input_data or {}).get("date")
        if raw:
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                return {"error": f"bad date '{raw}', expected YYYY-MM-DD"}
        else:
            dt = datetime.now(timezone.utc)

        elapsed_days = (dt - self._KNOWN_NEW_MOON).total_seconds() / 86400.0
        age = elapsed_days % self._SYNODIC
        frac = age / self._SYNODIC                       # 0..1 through the cycle

        # Illumination follows a cosine: 0% at new, 100% at full.
        illum = (1 - math.cos(2 * math.pi * frac)) / 2 * 100

        # Nearest named phase by cycle fraction (wrap-around aware).
        name, emoji = min(
            self._PHASES,
            key=lambda p: min(abs(frac - p[0]), 1 - abs(frac - p[0]))
        )[1:]

        return {
            "date":             dt.strftime("%Y-%m-%d"),
            "phase_name":       name,
            "emoji":            emoji,
            "illumination_pct": round(illum, 1),
            "age_days":         round(age, 1),
        }


def get_plugin():
    return NovaPlugin
