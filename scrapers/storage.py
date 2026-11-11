"""UTF-8, finite JSON and atomic replacement of each export file."""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def save(frame: pd.DataFrame, name: str, output: Path, snapshot=False) -> None:
    output.mkdir(parents=True, exist_ok=True)
    clean = frame.drop_duplicates().replace([float("inf"), -float("inf")], None)
    stem = name + (
        "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") if snapshot else ""
    )
    # Prepare both payloads before replacing either; individual files are atomic.
    payloads = {
        "csv": clean.to_csv(index=False),
        "json": clean.to_json(orient="records", indent=2, force_ascii=False, date_format="iso"),
    }
    for extension, text in payloads.items():
        fd, path = tempfile.mkstemp(dir=output, prefix="." + stem, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(path, output / f"{stem}.{extension}")
        finally:
            if os.path.exists(path):
                os.unlink(path)
