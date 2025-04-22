import logging
from typing import Annotated, TypeAlias, Any
import typing

import httpx
from dotenv import dotenv_values
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from ..logging.logging_config import setup_logging

setup_logging()
debug_logger = logging.getLogger("debug")

env = dotenv_values()

AUTH0_DOMAIN = env["AUTH0_DOMAIN"]
AUTH0_AUDIENCE = env["AUTH0_AUDIENCE"]
ALGORITHMS = ["RS256"]

token_auth_scheme = HTTPBearer()


async def get_auth0_public_key() -> Any:
    url = f"https://{env['AUTH0_DOMAIN']}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


CredentialsDep: TypeAlias = Annotated[
    HTTPAuthorizationCredentials, Depends(token_auth_scheme)
]


async def get_current_user(credentials: CredentialsDep) -> dict[str, str]:
    try:
        token = credentials.credentials
        jwks = await get_auth0_public_key()

        header = jwt.get_unverified_header(token)

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )

        return typing.cast(dict[str, str], payload)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        debug_logger.error(f"Unexpected error: {e}")
        raise e


CurrentUserDep: TypeAlias = Annotated[dict[str, str], Depends(get_current_user)]
