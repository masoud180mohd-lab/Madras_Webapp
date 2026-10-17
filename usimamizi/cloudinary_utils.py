"""Cloudinary environment detection and lazy SDK configuration.

Extracted from ``usimamizi.views.media_protected`` so the protected-media view
and the Cloudinary storage backend (``usimamizi/storage.py``) can share a single
source of truth for "is Cloudinary enabled?" and "configure the SDK" without
importing from the views package (which would create an import cycle for storage
backends that must stay importable before the app registry is ready).
"""

from __future__ import annotations

import os

import cloudinary

# Extensions treated as Cloudinary "image" resources when a path cannot be
# mapped to a known model field (safety net only — see
# media_protected._resolve_public_id).
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}

# Set True once the Cloudinary SDK has been configured from the environment.
_CLOUDINARY_CONFIGURED = False


def is_cloudinary_enabled() -> bool:
    """
    Whether Cloudinary should be used for media delivery.

    True when a single CLOUDINARY_URL is present, or when all three discrete
    CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET are set
    (Render provides the discrete trio). This only inspects the environment and
    does NOT require the SDK to be configured yet — see ensure_cloudinary_config.
    """
    if os.environ.get("CLOUDINARY_URL"):
        return True
    return all(
        os.environ.get(key)
        for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
    )


def ensure_cloudinary_config() -> bool:
    """
    Configure the Cloudinary SDK from the environment exactly once.

    cloudinary.utils.cloudinary_url() needs the SDK configured before it can
    sign URLs. Render may provide discrete CLOUDINARY_CLOUD_NAME / API_KEY /
    API_SECRET instead of a single CLOUDINARY_URL, so handle both. Success is
    memoised in _CLOUDINARY_CONFIGURED.

    Returns True if the SDK is (or becomes) configured, False otherwise.
    """
    global _CLOUDINARY_CONFIGURED
    if _CLOUDINARY_CONFIGURED:
        return True

    cloudinary_url = os.environ.get("CLOUDINARY_URL")
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
    api_key = os.environ.get("CLOUDINARY_API_KEY")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")

    try:
        if cloudinary_url:
            cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
        elif cloud_name and api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True,
            )
        else:
            return False
    except Exception:
        return False

    _CLOUDINARY_CONFIGURED = True
    return True
