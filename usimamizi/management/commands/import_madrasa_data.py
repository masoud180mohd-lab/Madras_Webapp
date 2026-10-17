"""Rejesha data ya madrasa kutoka faili la JSON la backup.

Usage:
    python manage.py import_madrasa_data [--input madrasa_backup.json] [--migrate] [--no-reset-sequences]
"""

from __future__ import annotations

import os

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

# Primary key internal types backed by a PostgreSQL serial sequence. loaddata
# inserts explicit ids without advancing the sequence, so these are the only
# tables whose sequence needs a post-load reset.
_AUTO_PK_TYPES = {"AutoField", "BigAutoField", "SmallAutoField"}


class Command(BaseCommand):
    """Restore madrasa data from a JSON backup file."""

    help = "Rejesha data ya madrasa kutoka faili la JSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            default="madrasa_backup.json",
            help="Njia ya faili la input (default: madrasa_backup.json).",
        )
        parser.add_argument(
            "--migrate",
            action="store_true",
            help="Run migrate --noinput before loading the data.",
        )
        parser.add_argument(
            "--no-reset-sequences",
            action="store_true",
            help="Skip resetting PostgreSQL sequences after loading.",
        )

    def handle(self, *args, **options):
        input_path = options["input"]

        if not os.path.isfile(input_path):
            raise CommandError(f"Faili halipatikani: {input_path}")

        if options["migrate"]:
            self.stdout.write("Inaendesha migrate --noinput ...")
            call_command("migrate", interactive=False)

        try:
            call_command("loaddata", input_path)
        except Exception as exc:
            raise CommandError(f"loaddata imeshindwa: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(f"Data imerejeshwa kwa mafanikio kutoka: {input_path}")
        )

        if options["no_reset_sequences"]:
            self.stdout.write("Reset ya sequences imerukwa (--no-reset-sequences).")
            return

        self._reset_postgres_sequences()

    def _reset_postgres_sequences(self):
        """Reset PostgreSQL serial sequences past the highest primary key.

        loaddata inserts rows with explicit primary keys, which never advances
        the serial sequence. Without this reset the next INSERT would reuse an
        existing id and fail with a unique violation. Only runs on PostgreSQL;
        SQLite and MySQL are unaffected.
        """
        if connection.vendor != "postgresql":
            self.stdout.write("Reset ya sequences imerukwa: database si PostgreSQL.")
            return

        reset = 0
        skipped = 0
        table_names = set(connection.introspection.table_names())

        with connection.cursor() as cursor:
            for model in apps.get_models(include_auto_created=True):
                meta = model._meta
                # Abstract, proxy and swapped-out models have no table of their own.
                if meta.abstract or meta.proxy or meta.swapped:
                    skipped += 1
                    continue

                pk_field = meta.pk
                if pk_field is None or pk_field.get_internal_type() not in _AUTO_PK_TYPES:
                    skipped += 1
                    continue

                db_table = meta.db_table
                pk_column = pk_field.column
                if db_table not in table_names:
                    skipped += 1
                    continue

                # pg_get_serial_sequence returns NULL for tables without a serial.
                cursor.execute(
                    "SELECT pg_get_serial_sequence(%s, %s)", [db_table, pk_column]
                )
                row = cursor.fetchone()
                if row is None or row[0] is None:
                    skipped += 1
                    continue

                quoted_table = connection.ops.quote_name(db_table)
                quoted_column = connection.ops.quote_name(pk_column)
                cursor.execute(
                    "SELECT setval(pg_get_serial_sequence(%s, %s), "
                    f"COALESCE(MAX({quoted_column}), 0) + 1, false) "
                    f"FROM {quoted_table}",
                    [db_table, pk_column],
                )
                cursor.fetchall()
                reset += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sequences za PostgreSQL zilizorekebishwa: {reset}, zilizorukwa: {skipped}."
            )
        )
