"""Hifadhi data yote ya madrasa kwenye faili la JSON la backup.

Usage:
    python manage.py export_madrasa_data [--output madrasa_backup.json]
"""

from __future__ import annotations

import io
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Export all madrasa data to a portable JSON backup file."""

    help = "Hamisha data yote ya madrasa kwenda faili la JSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="madrasa_backup.json",
            help="Njia ya faili la output (default: madrasa_backup.json).",
        )

    def handle(self, *args, **options):
        output_path = options["output"]

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        try:
            call_command(
                "dumpdata",
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                exclude=[
                    "contenttypes",
                    "auth.permission",
                    "sessions",
                    "admin.logentry",
                    "authtoken.Token",
                    "token_blacklist.BlacklistedToken",
                    "token_blacklist.RefreshToken",
                ],
                stdout=stdout_buffer,
                stderr=stderr_buffer,
            )
        except Exception as exc:
            detail = (stderr_buffer.getvalue() or "").strip()
            raise CommandError(f"dumpdata imeshindwa: {detail or exc}") from exc

        try:
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write(stdout_buffer.getvalue())
        except OSError as exc:
            raise CommandError(
                f"Imeshindikana kuandika faili la output {output_path}: {exc}"
            ) from exc

        size_bytes = os.path.getsize(output_path)
        self.stdout.write(
            self.style.SUCCESS(
                f"Data imehifadhiwa kwa mafanikio: {output_path} ({size_bytes:,} bytes)"
            )
        )
