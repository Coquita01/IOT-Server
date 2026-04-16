
from app.shared.middleware.auth.auth_rc.base import PuzzleVerifier


class DeviceAuth:
    
    def __init__(self):
        self.verifier = PuzzleVerifier()

    def authenticate(self, device, puzzle) -> dict:
        if not device.encryption_key:
            return {"valid": False, "error": "Authentication failed"}
        key = bytes.fromhex(device.encryption_key)
        return self.verifier.verify(key, puzzle, str(device.id))
