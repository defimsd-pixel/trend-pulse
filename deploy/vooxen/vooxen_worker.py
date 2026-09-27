"""VOOXEN — collecte Trend Pulse : un instantané par jour à TP_SNAPSHOT_TIME (heure de Paris).

Remplace le worker du fork (un instantané par heure, toutes sources). Sources et pays
viennent de vooxen_app (TP_SOURCES, TP_GEO). Aucun appel à un LLM.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
import sqlite3
from pathlib import Path
from zoneinfo import ZoneInfo

from vooxen_app import ALLOWED, DEFAULT_GEO, RestrictedAggregator

TZ = ZoneInfo("Europe/Paris")
HOUR, MINUTE = (int(x) for x in os.environ.get("TP_SNAPSHOT_TIME", "07:00").split(":"))
COUNT = int(os.environ.get("TP_SNAPSHOT_COUNT", "20"))
BACKUP_DIR = Path(os.environ.get("TP_BACKUP_DIR", "/app/backups"))
BACKUP_DAYS = int(os.environ.get("TP_BACKUP_DAYS", "14"))


def seconds_until_next_run(now: dt.datetime) -> float:
    target = now.replace(hour=HOUR, minute=MINUTE, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    return (target - now).total_seconds()


async def take_snapshot(agg: RestrictedAggregator) -> None:
    result = await agg.snapshot(sources=None, geo=DEFAULT_GEO, count=COUNT)
    per_source = {name: len(items) for name, items in result.get("sources", {}).items()}
    errors = result.get("sources_error", {})
    print(f"[vooxen] instantané {dt.datetime.now(TZ).isoformat()} geo={DEFAULT_GEO} "
          f"sources={per_source} erreurs={list(errors) if errors else []}", flush=True)


def backup_db() -> None:
    """Copie cohérente de l'historique SQLite, conservée BACKUP_DAYS jours."""
    db = os.environ.get("TREND_PULSE_DB", "/app/data/history.db")
    if not Path(db).exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"history-{dt.date.today().isoformat()}.db"
    with sqlite3.connect(db) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
    for old in sorted(BACKUP_DIR.glob("history-*.db"))[:-BACKUP_DAYS]:
        old.unlink()
    print(f"[vooxen] sauvegarde {target}", flush=True)


async def main() -> None:
    agg = RestrictedAggregator()
    print(f"[vooxen] worker démarré : {HOUR:02d}:{MINUTE:02d} Europe/Paris, geo={DEFAULT_GEO}, sources={ALLOWED}", flush=True)
    if os.environ.get("TP_SNAPSHOT_ON_START") == "1":
        await take_snapshot(agg)
    while True:
        await asyncio.sleep(seconds_until_next_run(dt.datetime.now(TZ)))
        try:
            await take_snapshot(agg)
            backup_db()
        except Exception as exc:  # une source en panne ne doit pas arrêter la collecte quotidienne
            print(f"[vooxen] échec de l'instantané : {exc!r}", flush=True)
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
