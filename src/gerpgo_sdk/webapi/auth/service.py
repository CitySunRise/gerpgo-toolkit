from __future__ import annotations

from typing import Any

from .client import WebAuthClient
from .session_store import WebSessionStore


class WebAuthService:
    def __init__(self, client: WebAuthClient, sessions: WebSessionStore) -> None:
        self.client = client
        self.sessions = sessions

    def login(self, profile: str, username: str, password: str) -> dict[str, Any]:
        token = self.client.login(username, password)
        self.sessions.save(profile, token)
        return self.sessions.status(profile)

    def status(self, profile: str) -> dict[str, Any]:
        return self.sessions.status(profile)

    def logout(self, profile: str) -> dict[str, Any]:
        removed = self.sessions.clear(profile)
        return {"profile": profile, "authenticated": False, "session_removed": removed}
