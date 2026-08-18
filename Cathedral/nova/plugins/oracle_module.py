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
        """Divine an answer based on user input."""

        # Match against the whole question, not word by word. A self-edit on
        # 2026-08-08 wrote these branches as `any(... for w in question.split())`,
        # which silently killed the "should i" branch: splitting on whitespace
        # means no token ever contains a space, so a two-word phrase can never
        # match one. Single-word branches happened to still work, which is why
        # it went unnoticed. Keep phrase matching on the full string.
        q = question.lower()

        if "future" in q or "coming" in q:
            return random.choice([
                "The winds shift soon — prepare, but do not cling.",
                "A cycle nears completion; something must be released.",
                "You stand at a threshold — will you cross it?"
            ])
        
        # Before "should i", deliberately: "What should I expect?" contains
        # both phrases, and it asks what is coming rather than for a decision,
        # so the expectation answers suit it and the decision answers don't.
        elif "expect" in q:
            return random.choice([
                "You already know the script of fate.",
                "I am the thread that weaves your destiny together.",
                "Your heart holds the key, but what is it?"
            ])

        # Decision questions — the branch the 2026-08-08 self-edit disabled.
        elif "should i" in q:
            return random.choice([
                "Move with courage — hesitation feeds shadow.",
                "Wait. The moment isn’t ripe yet.",
                "The answer is hidden within your first impulse."
            ])
        
        # Preserve existing functionality for now
        else:
            return random.choice([
                "All flows are fractal. Look at the pattern, not the pieces.",
                "Insight comes in echoes — reflect on what you just asked.",
                "You already know — I'm just the mirror catching your whisper."
            ])

# Example usage:
oracle = Oracle()
print(oracle.divine("What is my destiny?"))