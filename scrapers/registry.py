"""Transactional SQLite IPO observations, including conflicting provider variants."""

import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd


def update_registry(frame: pd.DataFrame, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = json.loads(frame.to_json(orient="records", force_ascii=False))
    variants = frame.attrs.get("conflicting_observations", [])
    if variants:
        records += json.loads(pd.DataFrame(variants).to_json(orient="records", force_ascii=False))
    with sqlite3.connect(path) as db:
        # Preserve a database made by the early three-key prototype. Its primary
        # key could not retain multiple observations at the same retrieval time.
        columns = [row[1] for row in db.execute("PRAGMA table_info(ipo_observation)")]
        legacy = bool(columns) and "observation_key" not in columns
        table = "ipo_observation_v2" if legacy else "ipo_observation"
        db.execute(f"""CREATE TABLE IF NOT EXISTS {table} (
            source TEXT NOT NULL, provider_slug TEXT NOT NULL, retrieved_at_utc TEXT NOT NULL,
            observation_key TEXT NOT NULL, payload TEXT NOT NULL,
            PRIMARY KEY(source, provider_slug, retrieved_at_utc, observation_key))""")
        if legacy:
            records += [
                json.loads(row[0]) for row in db.execute("SELECT payload FROM ipo_observation")
            ]
        for row in records:
            payload = json.dumps(row, ensure_ascii=False, allow_nan=False, sort_keys=True)
            key = hashlib.sha256(payload.encode()).hexdigest()
            db.execute(
                f"INSERT OR IGNORE INTO {table} VALUES (?, ?, ?, ?, ?)",
                (row["source"], row["provider_slug"], row["retrieved_at_utc"], key, payload),
            )
        return db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
