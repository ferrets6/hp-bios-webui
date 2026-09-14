"""
Optional OIDC authentication (authorization code + PKCE), fully inactive
unless OIDC_ISSUER_URL is set. See the "Authentication" section in
README.md for why this exists and why it's off by default.

When enabled, RequireAuthMiddleware (installed in main.py) gates every
route - the static frontend and every /api/* endpoint - behind a valid,
non-idle-expired session. There are no exempt routes besides the ones
that make up the login flow itself.
"""
import os
import time

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

OIDC_ISSUER_URL = os.environ.get("OIDC_ISSUER_URL", "").strip()
ENABLED = bool(OIDC_ISSUER_URL)

SESSION_MAX_AGE_SECONDS = int(os.environ.get("SESSION_MAX_AGE_SECONDS", "3600"))

PUBLIC_PATHS = {"/login", "/callback", "/logout"}

oauth: OAuth | None = None
SESSION_SECRET_KEY: str | None = None

if ENABLED:
    OIDC_CLIENT_ID = os.environ["OIDC_CLIENT_ID"]
    OIDC_CLIENT_SECRET = os.environ["OIDC_CLIENT_SECRET"]
    OIDC_REDIRECT_URL = os.environ["OIDC_REDIRECT_URL"]
    SESSION_SECRET_KEY = os.environ["SESSION_SECRET_KEY"]

    oauth = OAuth()
    oauth.register(
        name="oidc",
        server_metadata_url=f"{OIDC_ISSUER_URL.rstrip('/')}/.well-known/openid-configuration",
        client_id=OIDC_CLIENT_ID,
        client_secret=OIDC_CLIENT_SECRET,
        client_kwargs={
            "scope": "openid email profile",
            "code_challenge_method": "S256",  # enables PKCE
        },
    )

router = APIRouter()


@router.get("/login")
async def login(request: Request):
    return await oauth.oidc.authorize_redirect(request, OIDC_REDIRECT_URL)


@router.get("/callback")
async def callback(request: Request):
    token = await oauth.oidc.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.oidc.userinfo(token=token)
    request.session["user"] = {"sub": userinfo.get("sub"), "email": userinfo.get("email")}
    request.session["last_seen"] = time.time()
    return RedirectResponse(url="/")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")


class RequireAuthMiddleware(BaseHTTPMiddleware):
    """Only installed when OIDC is enabled (see main.py). Sliding idle
    timeout: every authenticated request refreshes last_seen, so the
    session stays alive under active use and expires SESSION_MAX_AGE_SECONDS
    after the last request."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        session = request.session
        last_seen = session.get("last_seen")
        authenticated = (
            bool(session.get("user"))
            and last_seen is not None
            and time.time() - last_seen <= SESSION_MAX_AGE_SECONDS
        )
        if not authenticated:
            session.clear()
            if request.url.path.startswith("/api/"):
                return JSONResponse({"detail": "authentication required"}, status_code=401)
            return RedirectResponse(url="/login")

        session["last_seen"] = time.time()
        return await call_next(request)
