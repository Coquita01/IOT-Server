
from app.shared.middleware.auth.auth_rc.base import PuzzleVerifier


class ApplicationAuth:
    
    def __init__(self):
        self.verifier = PuzzleVerifier()

    def authenticate(self, application, puzzle) -> dict:
        if not application.api_key:
            return {"valid": False, "error": "Authentication failed"}
        key = bytes.fromhex(application.api_key)
        return self.verifier.verify(key, puzzle, str(application.id))
