"""Persistence layer: one JSON file per resource.

This is the only module that knows the data lives in files. The service
layer talks to JsonRepository through plain dicts, so swapping it for an
ORM-backed repository later does not touch the routers or the rules.
"""

import json
import shutil
import threading
from pathlib import Path
from typing import Any, Callable

from app.settings import EXAMPLES_DIR


class JsonRepository:
    """CRUD on a list of records stored in <data_dir>/<name>.json."""

    _lock = threading.Lock()  # one writer at a time across all files

    def __init__(self, data_dir: Path, name: str, id_field: str):
        self.path = Path(data_dir) / f"{name}.json"
        self.id_field = id_field
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            seed = EXAMPLES_DIR / f"{name}.json"
            if seed.exists():
                shutil.copy(seed, self.path)
            else:
                self.path.write_text("[]", encoding="utf-8")

    # ----- low level -----

    def _load(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, records: list[dict[str, Any]]) -> None:
        # Write to a temp file first, then replace, so a crash never leaves half a file.
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)

    # ----- CRUD -----

    def all(self) -> list[dict[str, Any]]:
        return self._load()

    def get(self, record_id: Any) -> dict[str, Any] | None:
        return next((r for r in self._load() if r[self.id_field] == record_id), None)

    def add(self, record: dict[str, Any], make_id: Callable[[list[dict]], Any]) -> dict[str, Any]:
        """Store a new record. make_id picks its identifier from the existing
        records inside the lock, so two requests never get the same id."""
        with self._lock:
            records = self._load()
            record = {self.id_field: make_id(records), **record}
            records.append(record)
            self._save(records)
        return record

    def replace(self, record_id: Any, record: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            records = self._load()
            for i, r in enumerate(records):
                if r[self.id_field] == record_id:
                    records[i] = record
                    self._save(records)
                    return record
        return None

    def delete(self, record_id: Any) -> bool:
        with self._lock:
            records = self._load()
            kept = [r for r in records if r[self.id_field] != record_id]
            if len(kept) == len(records):
                return False
            self._save(kept)
        return True
