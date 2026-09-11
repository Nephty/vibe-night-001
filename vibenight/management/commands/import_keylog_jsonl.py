import json
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from vibenight.models import KeylogEntry


class Command(BaseCommand):
    help = (
        "One-time backfill: import entries from the legacy keylog.jsonl file "
        "(VIBENIGHT_KEYLOG_PATH) into the KeylogEntry table."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Import even if KeylogEntry rows already exist.",
        )

    def handle(self, *args, **options):
        if KeylogEntry.objects.exists() and not options["force"]:
            self.stdout.write(self.style.WARNING(
                "KeylogEntry already has rows — pass --force to import anyway."
            ))
            return

        log_path = Path(settings.VIBENIGHT_KEYLOG_PATH)
        if not log_path.exists():
            self.stdout.write(self.style.WARNING(f"No file at {log_path}, nothing to import."))
            return

        created = 0
        skipped = 0
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    skipped += 1
                    continue

                received_at = entry.get("received_at")
                KeylogEntry.objects.create(
                    received_at=(
                        datetime.fromtimestamp(received_at, tz=timezone.utc)
                        if received_at
                        else datetime.now(tz=timezone.utc)
                    ),
                    device_id=str(entry.get("device_id", ""))[:200],
                    page=str(entry.get("page", ""))[:500],
                    ip=entry.get("ip") or None,
                    user_agent=str(entry.get("user_agent", ""))[:300],
                    buffer=entry.get("buffer", ""),
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created} entries ({skipped} skipped)."))
