from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionData:
    user_id: str
    token_id: str
    refresh_token: str
    email: str
    account_type: str
    is_master: bool
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "token_id": self.token_id,
            "refresh_token": self.refresh_token,
            "email": self.email,
            "account_type": self.account_type,
            "is_master": self.is_master,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        return cls(
            user_id=data["user_id"],
            token_id=data["token_id"],
            refresh_token=data["refresh_token"],
            email=data["email"],
            account_type=data["account_type"],
            is_master=data["is_master"],
            ip_address=data["ip_address"],
            user_agent=data["user_agent"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
        )


@dataclass
class RefreshTokenData:
    user_id: str
    token_id: str
