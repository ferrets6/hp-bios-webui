import hashlib
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import nas_client, schema

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bios-webui")

app = FastAPI(title="HP ProDesk 400 G5 - BIOS Web UI")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def _compute_asset_version() -> str:
    """Hash of the frontend assets, computed once at process start. Used to
    cache-bust asset URLs so a redeploy can never leave a browser rendering
    a stale mix of HTML/CSS/JS regardless of HTTP caching semantics."""
    digest = hashlib.sha256()
    for filename in ("style.css", "app.js"):
        digest.update((FRONTEND_DIR / filename).read_bytes())
    return digest.hexdigest()[:10]


ASSET_VERSION = _compute_asset_version()


@app.middleware("http")
async def no_cache_static(request, call_next):
    """This is a low-traffic internal tool, not a CDN-fronted site - always
    revalidate the frontend so a redeploy doesn't leave browsers rendering a
    stale HTML/CSS/JS mix indefinitely."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


class WriteRequest(BaseModel):
    name: str
    value: str


class ApplyRequest(BaseModel):
    changes: list[WriteRequest]


class PasswordRequest(BaseModel):
    role: str
    new_password: str
    current_password: str = ""


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/menu")
def get_menu():
    """Static menu layout the frontend renders tabs/sections from."""
    return {
        "sections": schema.SECTIONS,
        "action_attributes": sorted(schema.ACTION_ATTRIBUTES),
        "read_only_hints": sorted(schema.READ_ONLY_HINTS),
        "password_roles": schema.PASSWORD_ROLES,
    }


@app.get("/api/attributes")
def get_attributes():
    try:
        attrs = nas_client.read_all_attributes()
    except nas_client.NasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    known = schema.flatten_known_names()
    for name, attr in attrs.items():
        attr["widget"] = schema.widget_for(attr["type"], attr["possible_values"])
        attr["known"] = name in known

    try:
        password_status = nas_client.read_password_status()
    except nas_client.NasError:
        password_status = {}

    try:
        pending_reboot = nas_client.read_pending_reboot()
    except nas_client.NasError:
        pending_reboot = None

    return {
        "attributes": attrs,
        "password_status": password_status,
        "pending_reboot": pending_reboot,
    }


@app.post("/api/apply")
def apply_changes(req: ApplyRequest):
    results = []
    for change in req.changes:
        try:
            nas_client.write_attribute(change.name, change.value)
            results.append({"name": change.name, "ok": True})
        except nas_client.NasError as exc:
            results.append({"name": change.name, "ok": False, "error": str(exc)})

    try:
        pending_reboot = nas_client.read_pending_reboot()
    except nas_client.NasError:
        pending_reboot = None

    return {"results": results, "pending_reboot": pending_reboot}


@app.post("/api/password")
def set_password(req: PasswordRequest):
    if req.role not in schema.PASSWORD_ROLES:
        raise HTTPException(status_code=400, detail=f"unknown role: {req.role}")
    try:
        nas_client.set_password(req.role, req.new_password, req.current_password)
    except nas_client.NasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True}


@app.post("/api/reboot")
def do_reboot():
    try:
        nas_client.reboot()
    except nas_client.NasError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True}


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/")
def index():
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace(
        'href="assets/style.css"', f'href="assets/style.css?v={ASSET_VERSION}"'
    )
    html = html.replace(
        'src="assets/app.js"', f'src="assets/app.js?v={ASSET_VERSION}"'
    )
    return HTMLResponse(html)
