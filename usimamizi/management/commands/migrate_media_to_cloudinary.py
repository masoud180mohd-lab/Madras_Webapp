"""Hamisha faili za media za zamani kutoka MEDIA_ROOT kwenda Cloudinary.

Command hii inatumika kabla ya kubadili storage kwenda Cloudinary (Render).
Haibadilishi records za database; inapakia faili tu kwa public IDs ambazo
usimamizi.views.media_protected inazitambua.

Usage:
    python manage.py migrate_media_to_cloudinary [--dry-run] [--overwrite] [--limit N] [--verbose]
"""

from __future__ import annotations

from pathlib import Path

import cloudinary.api
import cloudinary.uploader
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from usimamizi.cloudinary_utils import IMAGE_EXTENSIONS, ensure_cloudinary_config


class Command(BaseCommand):
    help = "Hamisha faili za media za zamani (MEDIA_ROOT) kwenda Cloudinary."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Onyesha mpango tu bila kupakia chochote.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Andika juu ya assets zilizopo tayari Cloudinary.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Idadi ya juu ya faili za kupakia (baada ya deduplication).",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Chapisha kila faili iliyopangwa au iliyopakiwa.",
        )

    def _normalize_name(self, name):
        """Normalize stored field name: backslashes -> '/', no leading '/'."""
        normalized = (name or "").replace("\\", "/").lstrip("/")
        if not normalized:
            return None
        parts = normalized.split("/")
        if any(part in ("", ".", "..") for part in parts):
            return None
        return normalized

    def _public_id(self, normalized, resource_type):
        """Build the Cloudinary public id from a normalized field name.

        Image assets are stored without extension (media_protected convention),
        so strip one trailing known image extension, case-insensitive. Raw
        files keep their extension. String slicing only, so forward slashes
        and folder dots (e.g. v1.2/...) are preserved untouched.
        """
        if resource_type != "image":
            return normalized
        lowered = normalized.lower()
        for ext in sorted(IMAGE_EXTENSIONS, key=len, reverse=True):
            if lowered.endswith(ext) and len(normalized) > len(ext):
                return normalized[: -len(ext)]
        return normalized

    def _resolve_source(self, media_root, normalized):
        """Resolve candidate under MEDIA_ROOT; never read outside it.

        Returns ("ok", path), ("missing", None) or ("invalid", None).
        """
        candidate = (media_root / normalized).resolve()
        if not candidate.is_relative_to(media_root):
            return "invalid", None
        if not candidate.is_file():
            return "missing", None
        return "ok", candidate

    def _asset_exists(self, public_id, resource_type, stats):
        """Return True/False, or None when the API call itself failed."""
        try:
            cloudinary.api.resource(public_id, resource_type=resource_type)
            return True
        except Exception as exc:
            if "NotFound" in type(exc).__name__ or "not found" in str(exc).lower():
                return False
            stats["errors"] += 1
            self.stdout.write(
                self.style.ERROR(f"Hitilafu kuangalia {public_id} Cloudinary: {exc}")
            )
            return None

    def _print_summary(self, stats):
        self.stdout.write("Muhtasari wa uhamishaji:")
        for label, key in (
            ("Zilizopangwa (planned)", "planned"),
            ("Zilizopakiwa (uploaded)", "uploaded"),
            ("Zilizorukwa - zilizopo (skipped_existing)", "skipped_existing"),
            ("Duplicate sawa (duplicate_same)", "duplicate_same"),
            ("Duplicate mgongano (duplicate_conflict)", "duplicate_conflict"),
            ("Faili hazipo (missing_file)", "missing_file"),
            ("Njia batili (invalid_path)", "invalid_path"),
            ("Hitilafu (errors)", "errors"),
        ):
            self.stdout.write(f"  {label}: {stats[key]}")

    def handle(self, *args, **options):
        if not ensure_cloudinary_config():
            raise CommandError(
                "Cloudinary haijasanidiwa. Weka CLOUDINARY_URL au "
                "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY na CLOUDINARY_API_SECRET."
            )

        dry_run = options["dry_run"]
        overwrite = options["overwrite"]
        verbose = options["verbose"]
        limit = options["limit"]
        if limit is not None and limit < 1:
            raise CommandError("--limit lazima iwe namba chanya (1 au zaidi).")

        # Imported here so the app registry is ready (no import-time issues).
        from usimamizi.models import Mwanafunzi, Mwalimu, Nyenzo

        stats = {
            "planned": 0,
            "uploaded": 0,
            "skipped_existing": 0,
            "duplicate_same": 0,
            "duplicate_conflict": 0,
            "missing_file": 0,
            "invalid_path": 0,
            "errors": 0,
        }

        media_root = Path(settings.MEDIA_ROOT).resolve()

        # (resource_type, model, field) — matches the folder-based resource
        # type mapping used by ProtectedCloudinaryStorage and media_protected.
        candidates = (
            ("image", Mwanafunzi, "picha"),
            ("image", Mwalimu, "picha"),
            ("raw", Nyenzo, "faili"),
        )

        plan_map = {}
        conflicts = set()
        for resource_type, model, field_name in candidates:
            model_label = model._meta.label
            for obj in model.objects.iterator():
                stored = getattr(obj, field_name).name
                if not stored:
                    continue

                normalized = self._normalize_name(stored)
                if normalized is None:
                    stats["invalid_path"] += 1
                    continue

                status, source_path = self._resolve_source(media_root, normalized)
                if status == "invalid":
                    stats["invalid_path"] += 1
                    continue
                if status == "missing":
                    stats["missing_file"] += 1
                    continue

                public_id = self._public_id(normalized, resource_type)
                if not public_id:
                    stats["invalid_path"] += 1
                    continue

                key = (resource_type, public_id)
                entry = (resource_type, public_id, source_path, model_label, obj.pk)
                if key in plan_map:
                    first_source, _ = plan_map[key]
                    if first_source == source_path:
                        stats["duplicate_same"] += 1
                        continue
                    stats["duplicate_conflict"] += 1
                    conflicts.add(key)
                    plan_map[key] = (first_source, None)
                    continue
                plan_map[key] = (source_path, entry)

        plan = [entry for _source, entry in plan_map.values() if entry is not None]
        if limit is not None:
            plan = plan[:limit]
        stats["planned"] = len(plan)

        for resource_type, public_id in sorted(conflicts):
            self.stdout.write(
                self.style.WARNING(
                    f"MGONGANO (duplicate_conflict): {public_id} "
                    f"(resource_type={resource_type}) - rekodi mbili zinaelekeza "
                    f"kwenye public_id hii lakini kwa faili tofauti; haitapakiwa."
                )
            )

        if dry_run:
            if verbose:
                for resource_type, public_id, source_path, _model_label, _pk in plan:
                    self.stdout.write(
                        f"PLAN {resource_type} {public_id} <- {source_path}"
                    )
            self._print_summary(stats)
            return

        for resource_type, public_id, source_path, _model_label, _pk in plan:
            if verbose:
                self.stdout.write(
                    f"UPLOAD {resource_type} {public_id} <- {source_path}"
                )

            exists = self._asset_exists(public_id, resource_type, stats)
            if exists is None:
                continue

            if exists and not overwrite:
                stats["skipped_existing"] += 1
                continue

            upload_overwrite = overwrite if exists else False
            try:
                with open(source_path, "rb") as file_object:
                    cloudinary.uploader.upload(
                        file_object,
                        public_id=public_id,
                        resource_type=resource_type,
                        overwrite=upload_overwrite,
                        unique_filename=False,
                    )
                stats["uploaded"] += 1
            except Exception as exc:
                stats["errors"] += 1
                self.stdout.write(
                    self.style.ERROR(f"Imeshindikana kupakia {public_id}: {exc}")
                )

        self._print_summary(stats)
        if stats["errors"] > 0:
            raise CommandError("Uhamishaji ulikamilika na hitilafu (errors > 0).")
