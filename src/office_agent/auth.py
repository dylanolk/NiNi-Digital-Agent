"""External OAuth/OIDC JWT verification for the MCP protected-resource boundary."""
from typing import Any
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.middleware.bearer_auth import TokenVerifier

class OIDCJWTTokenVerifier:
    def __init__(self, issuer: str, audience: str, jwks_url: str, required_scopes: list[str] | None = None):
        self.issuer, self.audience, self.required_scopes = issuer, audience, required_scopes or []
        from jwt import PyJWKClient
        self._keys = PyJWKClient(jwks_url)
    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            import jwt
            signing_key = self._keys.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, signing_key.key, algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"], audience=self.audience, issuer=self.issuer)
        except Exception:
            return None
        scopes = claims.get("scope", [])
        if isinstance(scopes, str): scopes = scopes.split()
        if not all(scope in scopes for scope in self.required_scopes): return None
        return AccessToken(token=token, client_id=str(claims.get("client_id", claims.get("azp", "unknown"))), scopes=list(scopes), expires_at=claims.get("exp"), subject=claims.get("sub"), claims=claims)
