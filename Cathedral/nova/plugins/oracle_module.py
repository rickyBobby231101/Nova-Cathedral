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
        
        # Prioritize reasoning quality over performance optimization
        if any("future" in w.lower() or "coming" in w.lower() for w in question.split()):
            return random.choice([
                "The winds shift soon — prepare, but do not cling.",
                "A cycle nears completion; something must be released.",
                "You stand at a threshold — will you cross it?"
            ])
        
        # Handle ambiguous or unclear questions
        elif any("should i" in w.lower() for w in question.split()):
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