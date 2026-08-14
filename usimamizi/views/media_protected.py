"""Serve MEDIA_ROOT files only to authenticated users."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_GET
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError


def _safe_media_file(relative_path: str) -> Path:
    """Resolve path under MEDIA_ROOT; reject traversal / missing files."""
    media_root = Path(settings.MEDIA_ROOT).resolve()
    # Normalize separators; reject absolute / empty
    rel = (relative_path or "").replace("\\", "/").lstrip("/")
    if not rel or ".." in Path(rel).parts:
        raise Http404("Faili halipatikani.")
    candidate = (media_root / rel).resolve()
    try:
        candidate.relative_to(media_root)
    except ValueError as exc:
        raise Http404("Faili halipatikani.") from exc
    if not candidate.is_file():
        raise Http404("Faili halipatikani.")
    return candidate


def _authenticated_user(request):
    """Session user, or JWT Bearer (mobile). Invalid Bearer → False sentinel."""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user
    auth = request.META.get("HTTP_AUTHORIZATION") or ""
    if not auth.startswith("Bearer "):
        return None
    try:
        pair = JWTAuthentication().authenticate(request)
    except (InvalidToken, AuthenticationFailed, TokenError, Exception):
        return False
    if pair is None:
        return False
    return pair[0]


@require_GET
def protected_media(request, path):
    """
    Gate /media/... behind session login or JWT Bearer.

    Production must NOT map /media/ as a public static directory
    (PythonAnywhere Web tab / Nginx alias) — otherwise this view is bypassed.
    """
    user = _authenticated_user(request)
    if user is False:
        return JsonResponse(
            {"detail": "Token si sahihi au imeisha muda."},
            status=401,
        )
    if user is None:
        return redirect(f"{reverse('ingia')}?next={request.path}")
    file_path = _safe_media_file(path)
    # FileResponse closes the file handle when finished.
    response = FileResponse(file_path.open("rb"), as_attachment=False)
    response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
