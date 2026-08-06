#!/usr/bin/env python3
"""
Engangs-migrering: kopier data/*.json (Railway Volume) -> Postgres (app_store).

Bruk (i miljø der BÅDE volumet og DATABASE_URL finnes, f.eks. Railway-konsollen):
    USE_DB=true python migrate_json_to_db.py

NB: Appen gjør normalt dette automatisk ved første oppstart med tom DB
(_auto_import_from_json). Dette scriptet er for manuell/eksplisitt kjøring.
Idempotent nok: det overskriver samlingene i DB med innholdet fra JSON-filene.
"""
import os
import json
from pathlib import Path

os.environ.setdefault('USE_DB', 'true')
os.environ.setdefault('TESTING', '1')  # unngå å starte scheduler ved import

from app import dm, DataManager  # noqa: E402

if not getattr(dm, 'use_db', False):
    raise SystemExit("DataManager kjører IKKE mot Postgres. Sett USE_DB=true og DATABASE_URL, og prøv igjen.")

src = Path(os.environ.get('DATA_DIR') or os.environ.get('RAILWAY_VOLUME_MOUNT_PATH') or 'data')
print(f"Leser JSON fra: {src.resolve()}")

total = 0
for name in DataManager._COLLECTIONS:
    fp = src / f"{name}.json"
    if not fp.exists():
        print(f"  - {name}: (ingen fil, hopper over)")
        continue
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    dm.save_data(name, data)
    n = len(data) if hasattr(data, '__len__') else 1
    total += n
    print(f"  ✓ {name}: {n} elementer migrert")

print(f"Ferdig. {total} elementer totalt migrert til Postgres.")
