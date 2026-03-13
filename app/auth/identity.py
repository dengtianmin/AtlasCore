from typing import Protocol

from app.auth.jwt_handler import decode_access_token


class TokenIdentityProvider(Protocol):
    def decode_token(self, token: str) -> dict:
        ...


class LocalJwtIdentityProvider:
    """Local JWT provider.

    Future Entra ID provider can implement the same protocol and be injected
    without changing endpoint or RBAC dependencies.
    """

    def decode_token(self, token: str) -> dict:
        return decode_access_token(token)
