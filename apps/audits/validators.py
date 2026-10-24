import os

from django.conf import settings
from rest_framework import serializers

SIGNATURES = {".md": None, ".txt": None, ".pdf": b"%PDF", ".docx": b"PK\x03\x04"}


def validate_documentation(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in SIGNATURES:
        raise serializers.ValidationError(f"Unsupported file type. Allowed: {', '.join(SIGNATURES)}.")
    if f.size > settings.AUDIT_DOC_MAX_BYTES:
        raise serializers.ValidationError(f"File too large (max {settings.AUDIT_DOC_MAX_BYTES // 1024} KB).")
    sig = SIGNATURES[ext]
    if sig:
        ok = f.read(len(sig)) == sig
    else:
        raw = f.read()
        try:
            raw.decode("utf-8")
            ok = b"\x00" not in raw
        except UnicodeDecodeError:
            ok = False
    f.seek(0)
    if not ok:
        raise serializers.ValidationError("File content does not match its extension.")
    return f