import functools
import json

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import (
    UnauthorizedError,
)
from jose import jwt
from six.moves.urllib.request import urlopen


class Authorizer:
    def __init__(self, auth0_domain: str, auth0_audience: str, algorithms=None):
        if algorithms is None:
            algorithms = ["RS256"]
        self.auth0_domain = auth0_domain
        self.auth0_audience = auth0_audience
        self.algorithms = algorithms

    @staticmethod
    def _extract_token(auth_header: str) -> str:
        """Obtains the Access Token from the Authorization Header"""
        if not auth_header:
            raise UnauthorizedError("Authorization header is missing")

        parts = auth_header.split()

        if parts[0].lower() != "bearer":
            raise UnauthorizedError("Authorization header must start with Bearer")
        elif len(parts) == 1:
            raise UnauthorizedError("No JWT token found in the Authorization header")
        elif len(parts) > 2:
            raise UnauthorizedError("Authorization header must be Bearer {token}")
        token = parts[1]
        return token

    def _verify(self, token: str) -> dict:
        jsonurl = urlopen("https://" + self.auth0_domain + "/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
        if not rsa_key:
            raise UnauthorizedError("Could not verify token due to missing public keys")
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self.algorithms,
                audience=self.auth0_audience,
                issuer="https://" + self.auth0_domain + "/",
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token is expired")
        except jwt.JWTClaimsError:
            raise UnauthorizedError("Invalid claims")
        except Exception:
            raise UnauthorizedError("Invalid header, unable to parse JWT token")
        return payload

    def requires_auth(self, app: APIGatewayRestResolver):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                auth_header = app.current_event.headers.get("authorization")
                auth_header = auth_header if auth_header else app.current_event.headers.get("Authorization")
                token = self._extract_token(auth_header)
                claims = self._verify(token)
                app.append_context(claims=claims)
                return func(*args, **kwargs)

            return wrapper

        return decorator
