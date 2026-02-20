"""
Minimal database / storage init for brand registration and campaign data.
Uses JSON file storage; this module ensures required directories exist.
"""
import os
from pathlib import Path


def init_db():
    """Ensure brand registration and campaign data directories exist."""
    # Resolve paths relative to project root (parent of backend)
    backend_dir = Path(__file__).resolve().parent.parent
    root = backend_dir.parent

    # Brand registration: uploads and data dir
    brand_uploads = root / "brand registration" / "uploads"
    brand_uploads.mkdir(parents=True, exist_ok=True)

    # Campaign module dirs (used by lifespan in server.py)
    for name in ("data/campaigns", "data/brands", "data/settings", "data/inspire", "data/engage", "uploads"):
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
