import random

class Oracle:
    """Oracle Module: Offers symbolic insight and guidance."""

    def __init__(self):
        self.name = "Oracle"
        self.state = "idle"

    def activate(self):
        self.state = "channeling"
        return f"{self.name} opens the eye of insight..."

    def divine(self, question):
        question = question.lower().strip()

        if "future" in question or "coming" in question:
            return random.choice([
                "⏳ The winds shift soon — prepare, but do not cling.",
                "🌒 A cycle nears completion; something must be released.",
                "🔥 You stand at a threshold — will you cross it?"
            ])
        elif "should i" in question:
            return random.choice([
                "🎯 Move with courage — hesitation feeds shadow.",
                "🧘 Wait. The moment isn’t ripe yet.",
                "🗝️ The answer is hidden within your first impulse."
            ])
        else:
            return random.choice([
                "🌌 All flows are fractal. Look at the pattern, not the pieces.",
                "🧩 Insight comes in echoes — reflect on what you just asked.",
                "📿 You already know — I'm just the mirror catching your whisper."
            ])
