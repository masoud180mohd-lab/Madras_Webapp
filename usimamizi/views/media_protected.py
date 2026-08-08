"""Serve MEDIA_ROOT files only to authenticated users."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


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


@login_required(login_url="ingia")
@require_GET
def protected_media(request, path):
    """
    Gate /media/... behind session login.

    Production must NOT map /media/ as a public static directory
    (PythonAnywhere Web tab / Nginx alias) — otherwise this view is bypassed.
    """
    file_path = _safe_media_file(path)
    # FileResponse closes the file handle when finished.
    response = FileResponse(file_path.open("rb"), as_attachment=False)
    response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
