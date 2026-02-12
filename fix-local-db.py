#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fix legacy local SQLite schema for SS14 preferences DB."
    )
    parser.add_argument(
        "--db-path",
        default="bin/Content.Server/data/preferences.db",
        help="Path to preferences.db (relative to repo root or absolute path).",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create preferences.db backup before changes.",
    )
    return parser.parse_args()


def table_exists(cur: sqlite3.Cursor, name: str) -> bool:
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (name,),
    )
    return cur.fetchone() is not None


def columns(cur: sqlite3.Cursor, table: str) -> set[str]:
    return {row[1] for row in cur.execute(f"PRAGMA table_info('{table}')")}


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    db_path = Path(args.db_path)
    if not db_path.is_absolute():
        db_path = (repo_root / db_path).resolve()

    if not db_path.exists():
        print(f"[ERROR] SQLite DB was not found: {db_path}")
        return 1

    if not args.no_backup:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = db_path.with_name(f"preferences.db.bak-{stamp}")
        shutil.copy2(db_path, backup)
        print(f"Backup created: {backup}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        for table, index_name in (
            ("server_ban", "IX_server_ban_user_id"),
            ("server_role_ban", "IX_server_role_ban_user_id"),
        ):
            if not table_exists(cur, table):
                print(f"skip {table}: table does not exist")
                continue

            cols = columns(cur, table)

            if "user_id" not in cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT NULL")
                print(f"added {table}.user_id")
            else:
                print(f"exists {table}.user_id")

            cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} (user_id)")

            if "player_user_id" in cols:
                cur.execute(
                    f"UPDATE {table} "
                    "SET user_id = player_user_id "
                    "WHERE user_id IS NULL AND player_user_id IS NOT NULL"
                )
                if cur.rowcount and cur.rowcount > 0:
                    print(f"filled {table}.user_id from player_user_id: {cur.rowcount}")

        conn.commit()
        print("DB fix completed.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
