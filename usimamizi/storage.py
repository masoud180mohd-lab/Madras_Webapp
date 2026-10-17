"""Cloudinary storage backends that keep /media/ as the authenticated entry point.

Why this module exists
----------------------
``django-cloudinary-storage``'s ``MediaCloudinaryStorage.url()`` returns a direct
(public) Cloudinary CDN URL. If that backend were wired in as-is, ``field.url``
would bypass ``usimamizi.views.media_protected.protected_media`` entirely, so the
JWT/session gate and the short-lived signed URLs would be lost (Task 4c Caveat 2).

Because ``MediaCloudinaryStorage._save()`` stores Cloudinary's returned
``public_id`` as the field name, the value captured by ``/media/<path>`` IS the
exact public_id (uniqueness suffix included, extension already omitted for
images). ``protected_media._resolve_public_id`` relies on that — no fragile
reconstruction from the path (Task 4c Caveat 1).

Recommended backend: ``ProtectedCloudinaryStorage``
---------------------------------------------------
``ProtectedCloudinaryStorage`` is a single default backend meant to be wired via
``STORAGES["default"]["BACKEND"]`` in production settings — no per-field
``storage=`` arguments, so no model changes and no migrations. It:

* overrides ``url()`` to return ``MEDIA_URL + quote(name, safe="/")`` so every
  media request still flows through ``protected_media`` (authenticated, signed,
  short-lived) instead of the public CDN;
* picks the Cloudinary ``resource_type`` from the upload **folder** (not the file
  extension) so it always agrees with ``media_protected``'s field registry;
* uploads with ``use_filename=True, unique_filename=True`` (collision-safe
  public_id) and returns Cloudinary's ``public_id`` as the stored name —
  extensionless for images, extension kept for raw — exactly the value
  ``protected_media._resolve_public_id`` matches against the database.

Enable it in production by pointing the default storage at this class when
Cloudinary credentials are present, e.g. ``madrasa_sys/settings/production.py``::

    STORAGES = {
        "default": {"BACKEND": "usimamizi.storage.ProtectedCloudinaryStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

This class subclasses ``MediaCloudinaryStorage`` at import time, so the module
requires ``django-cloudinary-storage`` (already pinned in requirements.txt).

Alternative: per-field backends (legacy)
----------------------------------------
``media_storage`` / ``raw_media_storage`` return a url-preserving Cloudinary
backend per resource type for wiring directly onto fields (``storage=...``). That
approach needs a model change plus ``makemigrations`` (a no-op at the DB level),
so prefer ``ProtectedCloudinaryStorage`` unless you want explicit per-field
control. When Cloudinary is not configured they fall back to ``FileSystemStorage``
so local development and the test suite keep using the disk and
``protected_media``'s local fallback.
"""

from __future__ import annotations

import os
from urllib.parse import quote

import cloudinary
import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage, RawMediaCloudinaryStorage
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, Storage

from usimamizi.cloudinary_utils import ensure_cloudinary_config, is_cloudinary_enabled

# upload_to folder prefix -> Cloudinary resource_type. Mirrors the owning model
# field so the storage decision always matches media_protected's field registry:
# Mwanafunzi.picha / Mwalimu.picha -> "image", Nyenzo.faili -> "raw".
_FOLDER_RESOURCE_TYPE = (
    ("nyenzo_masomo/", "raw"),
    ("picha_za_wanafunzi/", "image"),
    ("picha_za_walimu/", "image"),
)


class ProtectedCloudinaryStorage(MediaCloudinaryStorage):
    """
    Default Cloudinary backend that keeps /media/ as the authenticated entry point.

    Wire it via ``STORAGES["default"]["BACKEND"]`` (see the module docstring). It
    differs from the stock ``MediaCloudinaryStorage`` in three ways:

    * ``url()`` returns ``MEDIA_URL + name`` (URL-encoded, slashes preserved) so
      requests go through ``protected_media`` instead of the public CDN;
    * ``_get_resource_type()`` is folder-based, so images saved under the raw
      ``nyenzo_masomo/`` folder stay ``raw`` and match the field registry;
    * ``_upload()`` configures the SDK lazily and adds ``unique_filename=True``
      for collision-safe public_ids.

    ``exists`` / ``size`` / ``delete`` / ``open`` are inherited unchanged: the
    library routes all of them through ``_get_resource_type`` (``delete`` directly,
    the others via ``_get_url``), so they automatically use the folder-based
    resource type.
    """

    def __init__(self, *args, **kwargs):
        # Configure the SDK from CLOUDINARY_URL or the discrete trio before use.
        ensure_cloudinary_config()
        super().__init__(*args, **kwargs)

    def url(self, name):
        # Never expose the direct CDN URL; route through the protected endpoint.
        if not name:
            return name
        return f"{settings.MEDIA_URL}{quote(name, safe='/')}"

    def _get_resource_type(self, name):
        # Folder-based on purpose (NOT extension-based): Nyenzo.faili may hold
        # jpg/png/webp, but it must remain resource_type="raw" to match the field
        # registry in media_protected._resolve_public_id (Nyenzo -> raw). If we
        # detected by extension, an image saved under nyenzo_masomo/ would be
        # stored as an extensionless "image" public_id, while protected_media
        # would sign it as "raw" and 404. Each upload_to folder maps 1:1 to the
        # owning field, so the folder is the reliable signal.
        normalized = (name or "").replace("\\", "/").lstrip("/")
        for prefix, resource_type in _FOLDER_RESOURCE_TYPE:
            if normalized.startswith(prefix):
                return resource_type
        return "raw"

    def _upload(self, name, content):
        # Signature matches MediaCloudinaryStorage._upload(self, name, content).
        if not ensure_cloudinary_config():
            raise ImproperlyConfigured(
                "Cloudinary haijasanidiwa. Weka CLOUDINARY_URL au "
                "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY na CLOUDINARY_API_SECRET."
            )
        normalized = (name or "").replace("\\", "/")
        options = {
            "use_filename": True,
            # Random suffix on the public_id so same-named uploads never collide.
            "unique_filename": True,
            "resource_type": self._get_resource_type(name),
        }
        # Mirror the library: tag only when the backend exposes a TAG attribute.
        if hasattr(self, "TAG"):
            options["tags"] = self.TAG
        folder = os.path.dirname(normalized)
        if folder:
            options["folder"] = folder
        return cloudinary.uploader.upload(content, **options)


def cloudinary_is_configured() -> bool:
    """True when Cloudinary credentials are present in the environment.

    Thin wrapper over :func:`usimamizi.cloudinary_utils.is_cloudinary_enabled`,
    kept for the legacy per-field callables below so there is a single source of
    truth for environment detection.
    """
    return is_cloudinary_enabled()


class ProtectedMediaCloudinaryStorageMixin:
    """Route ``.url`` through the protected /media/ endpoint, not the CDN."""

    def url(self, name):
        if not name:
            return name
        return f"{settings.MEDIA_URL}{name}"


def _build_cloudinary_storage(resource_type: str) -> Storage:
    """Construct a url-preserving Cloudinary storage for the given resource type."""
    base = RawMediaCloudinaryStorage if resource_type == "raw" else MediaCloudinaryStorage
    return type(
        f"Protected{base.__name__}",
        (ProtectedMediaCloudinaryStorageMixin, base),
        {},
    )()


def media_storage() -> Storage:
    """Storage for image fields (Cloudinary when configured, else default)."""
    if cloudinary_is_configured():
        return _build_cloudinary_storage("image")
    return FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)


def raw_media_storage() -> Storage:
    """Storage for non-image documents (Cloudinary 'raw' when configured)."""
    if cloudinary_is_configured():
        return _build_cloudinary_storage("raw")
    return FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
