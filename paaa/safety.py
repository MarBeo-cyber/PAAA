class SafetyGovernor:
    forbidden_claims = [
        "diagnosis",
        "parkinson detected",
        "neurological disease",
        "treatment",
        "therapy",
    ]

    def validate_message(self, message: str) -> str:
        lower = message.lower()
        if any(term in lower for term in self.forbidden_claims):
            raise ValueError("Unsafe medicalized claim detected.")
        return message
