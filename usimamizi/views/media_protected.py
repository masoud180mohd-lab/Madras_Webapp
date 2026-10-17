"""Serve MEDIA_ROOT files only to authenticated users via signed Cloudinary URLs."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cloudinary
import cloudinary.utils
from django.conf import settings
from django.http import JsonResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_GET
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError

from usimamizi.cloudinary_utils import IMAGE_EXTENSIONS, is_cloudinary_enabled, ensure_cloudinary_config


def _authenticate_user(request):
    """
    Authenticate user via session or JWT Bearer token.
    Returns: (user, error_response)
      - (user, None) if authenticated
      - (None, response) if authentication failed (response is ready to return)
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user, None

    # Try JWT Bearer token
    auth = request.META.get("HTTP_AUTHORIZATION") or ""
    if not auth.startswith("Bearer "):
        # No credentials — redirect to login
        login_url = f"{reverse('ingia')}?next={request.path}"
        return None, redirect(login_url)

    try:
        pair = JWTAuthentication().authenticate(request)
    except (InvalidToken, AuthenticationFailed, TokenError, Exception):
        return None, JsonResponse(
            {"detail": "Token si sahihi au imeisha muda."},
            status=401,
        )

    if pair is None:
        return None, JsonResponse(
            {"detail": "Token si sahihi au imeisha muda."},
            status=401,
        )

    return pair[0], None


def _generate_signed_url(public_id: str, resource_type: str = "image") -> Optional[str]:
    """
    Generate a signed Cloudinary URL with expiry.

    Args:
        public_id: Cloudinary public ID (e.g., "student_photos/123.jpg")
        resource_type: "image" or "raw" (for non-image files)

    Returns:
        Signed URL string, or None if generation failed
    """
    if not ensure_cloudinary_config():
        return None

    try:
        # Expire in 5 minutes (300 seconds)
        # Signature type: "signature" for secure delivery
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            type="upload",
            sign_url=True,
            expires_at=int(time.time()) + 300,  # 5 minutes from now
        )
        return url
    except Exception:
        return None


def _media_field_registry():
    """
    Media-bearing model fields and their Cloudinary resource_type.

    Imported lazily so this module stays importable without the models (and so
    the registry always reflects the live app registry).
    """
    from usimamizi.models import Mwalimu, Mwanafunzi, Nyenzo

    return (
        (Mwanafunzi, "picha", "image"),
        (Mwalimu, "picha", "image"),
        (Nyenzo, "faili", "raw"),
    )


def _resolve_public_id(rel: str):
    """
    Map a stored /media/<path> to (public_id, resource_type).

    The value captured by /media/<path> IS the exact stored field name. When a
    Cloudinary-backed storage is used, that stored name is already the true
    public_id returned by Cloudinary on upload (including any uniqueness suffix,
    and without the extension for image resources). We therefore use it verbatim
    instead of reconstructing it, and take resource_type from the owning field
    rather than guessing from a file extension that images no longer carry.

    Returns (public_id, resource_type), or (None, None) when no record matches.
    """
    for model, field, resource_type in _media_field_registry():
        try:
            if model.objects.filter(**{field: rel}).exists():
                return rel, resource_type
        except Exception:
            # A misconfigured/unmigrated field must never take media offline.
            continue
    return None, None


def _trailing_extension(name: str) -> str:
    """
    Lowercased trailing extension of the final path segment.

    Uses string slicing (not pathlib) so forward slashes in the folder path are
    preserved exactly. Returns "" when the final segment has no dot, or when the
    only dot belongs to an earlier folder segment (e.g. "v1.2/photo").
    """
    dot = name.rfind(".")
    slash = name.rfind("/")
    if dot == -1 or dot < slash:
        return ""
    return name[dot:].lower()


def _strip_image_extension(public_id: str) -> str:
    """
    Remove a single trailing known image extension from a Cloudinary public_id.

    Cloudinary image resources are addressed by extensionless public IDs, but
    legacy rows may still store a filename such as "picha_za_wanafunzi/photo.jpg".
    Stripping is case-insensitive, removes only the final extension, and leaves an
    already-extensionless ID unchanged. Only call this for resource_type "image" —
    raw public IDs must keep their extension.
    """
    ext = _trailing_extension(public_id)
    if ext in IMAGE_EXTENSIONS:
        return public_id[: -len(ext)]
    return public_id


def _normalize_media_path(path: str) -> Optional[str]:
    """
    Normalize a /media/<path> value the same way protected_media does.

    Collapses backslashes to forward slashes and strips leading slashes, then
    rejects empty paths or any path traversal (".." segment). Returns the
    normalized relative path, or None when it is empty/unsafe.
    """
    rel = (path or "").replace("\\", "/").lstrip("/")
    if not rel or ".." in Path(rel).parts:
        return None
    return rel


def _resolve_public_id_and_type(rel: str) -> tuple[str, str]:
    """
    Resolve a normalized media path to (public_id, resource_type).

    Uses the DB-backed resolver first, then falls back to extension inference
    for paths not covered by the registry. Image public IDs are normalized to
    Cloudinary's extensionless form; raw public IDs keep their extension.
    """
    public_id, resource_type = _resolve_public_id(rel)
    if public_id is None:
        # Safety net for paths not covered by the registry (e.g. legacy or
        # ad-hoc files): infer resource_type from the trailing extension.
        ext = _trailing_extension(rel)
        resource_type = "image" if ext in IMAGE_EXTENSIONS else "raw"
        public_id = rel

    # Cloudinary image resources use extensionless public IDs, but mapped legacy
    # rows (and inferred fallback paths) may still carry a filename extension.
    # Strip a single trailing known image extension for image resources only;
    # raw public IDs keep theirs.
    if resource_type == "image":
        public_id = _strip_image_extension(public_id)

    return public_id, resource_type


@require_GET
def protected_media(request, path):
    """
    Gate /media/... behind session login or JWT Bearer.

    If Cloudinary is enabled:
      - JSON clients (Accept: application/json) get the signed Cloudinary URL
        in the response body; browsers get a 302 redirect to it
      - Either way the client fetches the file directly from Cloudinary

    If Cloudinary is disabled (development/fallback):
      - Serves file from local MEDIA_ROOT via FileResponse
      - Used for local development without Cloudinary credentials
    """
    # Authenticate user
    user, error_response = _authenticate_user(request)
    if error_response:
        return error_response

    # Normalize path (remove leading slashes, prevent traversal)
    rel = _normalize_media_path(path)
    if rel is None:
        raise Http404("Faili halipatikani.")

    if is_cloudinary_enabled():
        # Cloudinary mode: resolve the exact stored public_id + resource_type
        # (see _resolve_public_id_and_type) and hand back a short-lived signed
        # URL. JSON clients (Flutter/API) receive it in the body; browsers
        # (<img>, <a>, direct navigation) get a 302 redirect so the file loads
        # without a client-side JSON round-trip.
        public_id, resource_type = _resolve_public_id_and_type(rel)

        wants_json = "application/json" in (request.META.get("HTTP_ACCEPT") or "")

        signed_url = _generate_signed_url(public_id, resource_type)
        if signed_url is None:
            if wants_json:
                return JsonResponse(
                    {"detail": "Imeshindikana kutengeneza URL ya picha."},
                    status=404,
                )
            raise Http404("Faili halipatikani.")

        if wants_json:
            return JsonResponse({
                "url": signed_url,
                "public_id": public_id,
                "resource_type": resource_type,
            })

        response = redirect(signed_url)
        response["Cache-Control"] = "private, no-store"
        return response

    # Fallback: serve from local disk (development mode / Cloudinary not set)
    media_root = Path(settings.MEDIA_ROOT).resolve()
    candidate = (media_root / rel).resolve()

    try:
        candidate.relative_to(media_root)
    except ValueError as exc:
        raise Http404("Faili halipatikani.") from exc

    if not candidate.is_file():
        raise Http404("Faili halipatikani.")

    from django.http import FileResponse
    response = FileResponse(candidate.open("rb"), as_attachment=False)
    response["Content-Disposition"] = f'inline; filename="{candidate.name}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


def signed_media_url_for_path(path: str) -> str | None:
    """
    Return a short-lived signed Cloudinary URL for a stored /media/<path>.

    Intended for server-side code that has no HTTP request object (e.g. PDF
    generation with xhtml2pdf, which must embed absolute image URLs). It reuses
    the same path normalization, DB-backed public_id resolution, image-extension
    handling, and signing as protected_media, but performs no authentication and
    returns no HTTP response.

    Returns the signed URL string on success, or None when Cloudinary is
    disabled, the path is empty/unsafe, or signing fails.
    """
    if not is_cloudinary_enabled():
        return None

    rel = _normalize_media_path(path)
    if rel is None:
        return None

    public_id, resource_type = _resolve_public_id_and_type(rel)
    return _generate_signed_url(public_id, resource_type)
