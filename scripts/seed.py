#!/usr/bin/env python3
"""Seed the production database from data/examples/*.json.

Run once after creating a fresh database:

    python scripts/seed.py

Safe to re-run: records that already exist (matched by primary key) are
skipped, so the script never creates duplicates.
"""

import json
import sys
from pathlib import Path

# Allow running from the project root without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402  (import after sys.path change)
from app.orm_models import CarRow, CustomerRow, RentalRow  # noqa: E402
from app.settings import EXAMPLES_DIR  # noqa: E402


def seed() -> None:
    session = SessionLocal()
    try:
        _seed_table(session, EXAMPLES_DIR / "cars.json", CarRow, "car_id")
        _seed_table(session, EXAMPLES_DIR / "customers.json", CustomerRow, "customer_id")
        _seed_table(session, EXAMPLES_DIR / "rentals.json", RentalRow, "rental_number")
        session.commit()
        print("Seed complete.")
    except Exception as exc:
        session.rollback()
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


def _seed_table(session, path: Path, row_class, pk_field: str) -> None:
    records = json.loads(path.read_text(encoding="utf-8"))
    inserted = skipped = 0
    for record in records:
        if session.get(row_class, record[pk_field]) is None:
            session.add(row_class(**record))
            session.flush()
            inserted += 1
        else:
            skipped += 1
    print(f"  {row_class.__tablename__}: {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    seed()
