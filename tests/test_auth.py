import asyncio
from office_agent.auth import OIDCJWTTokenVerifier

def test_oidc_verifier_maps_scope_claims_without_network(monkeypatch):
    class FakeKey:
        key = "key"
    class FakeJWK:
        def __init__(self, url): pass
        def get_signing_key_from_jwt(self, token): return FakeKey()
    monkeypatch.setattr("jwt.PyJWKClient", FakeJWK)
    verifier = OIDCJWTTokenVerifier("https://issuer.example", "office-agent", "https://issuer.example/jwks", ["catalog:read"])
    monkeypatch.setattr("jwt.decode", lambda *args, **kwargs: {"sub": "user-1", "azp": "chatgpt", "scope": "catalog:read bom:write", "exp": 2000000000})
    token = asyncio.run(verifier.verify_token("token"))
    assert token is not None and token.subject == "user-1" and "bom:write" in token.scopes
