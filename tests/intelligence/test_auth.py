import pytest

from app.auth import UnconfiguredAuthenticationProvider, authenticate

def test_unconfigured_auth_never_creates_identity():
    with pytest.raises(PermissionError, match="Authentication is required"):
        authenticate(UnconfiguredAuthenticationProvider(), None)
