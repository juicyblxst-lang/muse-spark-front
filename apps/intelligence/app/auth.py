from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None = None

class AuthenticationProvider(Protocol):
    def authenticate(self, authorization: str | None) -> AuthenticatedUser | None: ...

class UnconfiguredAuthenticationProvider:
    """Explicit safe default until the deployment supplies its auth adapter."""
    def authenticate(self, authorization: str | None) -> AuthenticatedUser | None:
        return None

def authenticate(provider: AuthenticationProvider, authorization: str | None) -> AuthenticatedUser:
    user = provider.authenticate(authorization)
    if user is None:
        raise PermissionError("Authentication is required")
    return user
