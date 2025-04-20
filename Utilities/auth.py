from fastapi import Request, HTTPException, status, Depends
from jose import jwt, jwk
from jose.utils import base64url_decode
import requests
from Utilities.settings import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
bearer_scheme = HTTPBearer()

CLERK_ISSUER = settings.CLERK_ISSUER
CLERK_JWKS_URL = settings.CLERK_JWKS_URL
CLERK_AUDIENCE = settings.CLERK_AUDIENCE  # Optional, if you have an audience
ALGORITHMS = ["RS256"]

# Pre-fetch JWKS (or you could cache it later for production)
JWKS = requests.get(CLERK_JWKS_URL).json()

ROLE_LEVEL = {
    "student": 1,
    "teacher": 2,
    "admin": 3,
}


def get_public_key(token: str):
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    for jwk_key in JWKS["keys"]:
        if jwk_key["kid"] == kid:
            return jwk.construct(jwk_key)
    raise HTTPException(status_code=401, detail="Public key not found")


def verify_token(token: str):
    try:
        key = get_public_key(token)

        # Decode without verifying signature (for debugging)
        decoded_payload = jwt.decode(
            token,
            "",  # Pass empty string as key for no-signature verification
            options={"verify_signature": False}
        )
        print("Decoded Payload:", decoded_payload)  # Optional debug print

        # Decode with actual verification
        payload = jwt.decode(
            token,
            key,
            algorithms=ALGORITHMS,
            issuer=CLERK_ISSUER,
            audience=CLERK_AUDIENCE
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTClaimsError as e:
        raise HTTPException(status_code=401, detail=f"Invalid claims: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    return verify_token(token)


def require_min_role(min_role: str):
    async def checker(user=Depends(get_current_user)):
        user_role_data = user.get("role")
        if not user_role_data:
            raise HTTPException(status_code=403, detail="No role assigned")

        # Extract the actual role string
        user_role = user_role_data.get("role") if isinstance(user_role_data, dict) else user_role_data

        if ROLE_LEVEL.get(user_role, 0) < ROLE_LEVEL.get(min_role, 0):
            raise HTTPException(
                status_code=403,
                detail=f"{user_role} not allowed to access this"
            )
        return user
    return checker

