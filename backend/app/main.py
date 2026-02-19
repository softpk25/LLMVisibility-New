"""
Brand blueprint UI and related routes (served by root server.py).
"""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

blueprint_router = APIRouter(tags=["brand-blueprint"])


@blueprint_router.get("/brand-blueprint", response_class=HTMLResponse)
async def brand_blueprint_page():
    """Serve the brand blueprint / brand registration page."""
    root = Path(__file__).resolve().parent.parent.parent
    template_path = root / "templates" / "FACEBOOK-BRAND-REGISTRATION.html"
    if not template_path.exists():
        return HTMLResponse(
            content="<h1>Brand Blueprint</h1><p>Template not found. Run from project root.</p>",
            status_code=404,
        )
    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
