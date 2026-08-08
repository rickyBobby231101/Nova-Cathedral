class NovaPlugin:
    """Gematria / numerology for a word or phrase — a real esoteric practice
    (Hermetic, Kabbalistic) of mapping letters to numbers. Pure calculation.

    input_data: {"text": "cathedral", "method": "ordinal"|"pythagorean"|"reduction"}
    returns:    {"text","method","value","reduced","letters"}
    """

    def __init__(self, system):
        self.system = system

    @staticmethod
    def _reduce(n: int) -> int:
        """Repeatedly sum digits down to a single digit, preserving the
        master numbers 11, 22, 33 as numerology convention does."""
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n

    def process(self, input_data: dict) -> dict:
        text = (input_data or {}).get("text", "")
        method = (input_data or {}).get("method", "ordinal").lower()
        if not text:
            return {"error": "missing 'text'"}

        letters = [c for c in text.lower() if c.isalpha()]
        if not letters:
            return {"error": "no letters in input"}

        if method == "ordinal":
            # a=1 ... z=26
            per = {c: (ord(c) - 96) for c in set(letters)}
        elif method in ("pythagorean", "reduction"):
            # a=1..i=9, j=1..r=9, s=1..z=8 (digital root of ordinal)
            per = {c: ((ord(c) - 97) % 9) + 1 for c in set(letters)}
        else:
            return {"error": f"unknown method '{method}' "
                             "(use ordinal|pythagorean|reduction)"}

        value = sum(per[c] for c in letters)
        return {
            "text":    text,
            "method":  method,
            "value":   value,
            "reduced": self._reduce(value),
            "letters": len(letters),
        }


def get_plugin():
    return NovaPlugin
