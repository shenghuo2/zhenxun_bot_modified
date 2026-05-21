from __future__ import annotations

from pathlib import Path

import aiosqlite

PLUGIN_DIR = Path(__file__).parent
DATABASE_PATH = PLUGIN_DIR / "summary.db"


async def _open_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def _ensure_column(
    db: aiosqlite.Connection,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    rows = await cursor.fetchall()
    if any(row[1] == column_name for row in rows):
        return
    await db.execute(
        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
    )


async def init_db() -> None:
    db = await _open_db()
    try:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                group_name TEXT NOT NULL DEFAULT '',
                admin_user_id TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                last_pushed_hour TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_id, admin_user_id)
            );

            CREATE TABLE IF NOT EXISTS hourly_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                group_name TEXT NOT NULL DEFAULT '',
                hour_start TEXT NOT NULL,
                hour_end TEXT NOT NULL,
                message_count INTEGER NOT NULL DEFAULT 0,
                image_count INTEGER NOT NULL DEFAULT 0,
                summary_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_id, hour_start)
            );

            CREATE INDEX IF NOT EXISTS idx_subscriptions_enabled
            ON subscriptions(enabled, admin_user_id);

            CREATE INDEX IF NOT EXISTS idx_hourly_summaries_group_hour
            ON hourly_summaries(group_id, hour_start);

            CREATE TABLE IF NOT EXISTS hourly_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                hour_start TEXT NOT NULL,
                create_time TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT '',
                sender_name TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL,
                file_unique TEXT NOT NULL DEFAULT '',
                image_summary TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_hourly_images_group_hour
            ON hourly_images(group_id, hour_start);

            CREATE INDEX IF NOT EXISTS idx_hourly_images_group_time
            ON hourly_images(group_id, create_time);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_hourly_images_group_unique
            ON hourly_images(group_id, hour_start, image_url, file_unique);
            """
        )
        await _ensure_column(
            db,
            "hourly_images",
            "image_summary",
            "TEXT NOT NULL DEFAULT ''",
        )
        await db.commit()
    finally:
        await db.close()


async def enable_subscription(
    *,
    group_id: str,
    group_name: str,
    admin_user_id: str,
) -> None:
    db = await _open_db()
    try:
        await db.execute(
            """
            INSERT INTO subscriptions (
                group_id, group_name, admin_user_id, enabled, updated_at
            ) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(group_id, admin_user_id) DO UPDATE SET
                group_name = excluded.group_name,
                enabled = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (group_id, group_name, admin_user_id),
        )
        await db.commit()
    finally:
        await db.close()


async def disable_subscription(*, group_id: str, admin_user_id: str) -> int:
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            UPDATE subscriptions
            SET enabled = 0, updated_at = CURRENT_TIMESTAMP
            WHERE group_id = ? AND admin_user_id = ?
            """,
            (group_id, admin_user_id),
        )
        await db.commit()
        return cursor.rowcount
    finally:
        await db.close()


async def update_subscription_group_name(
    *,
    group_id: str,
    admin_user_id: str,
    group_name: str,
) -> None:
    db = await _open_db()
    try:
        await db.execute(
            """
            UPDATE subscriptions
            SET group_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE group_id = ? AND admin_user_id = ?
            """,
            (group_name, group_id, admin_user_id),
        )
        await db.commit()
    finally:
        await db.close()


async def set_last_pushed_hour(
    *,
    group_id: str,
    admin_user_id: str,
    hour_start: str,
) -> None:
    db = await _open_db()
    try:
        await db.execute(
            """
            UPDATE subscriptions
            SET last_pushed_hour = ?, updated_at = CURRENT_TIMESTAMP
            WHERE group_id = ? AND admin_user_id = ?
            """,
            (hour_start, group_id, admin_user_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_subscription(*, group_id: str, admin_user_id: str):
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM subscriptions
            WHERE group_id = ? AND admin_user_id = ?
            LIMIT 1
            """,
            (group_id, admin_user_id),
        )
        return await cursor.fetchone()
    finally:
        await db.close()


async def get_enabled_subscriptions() -> list[aiosqlite.Row]:
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM subscriptions
            WHERE enabled = 1
            ORDER BY admin_user_id, group_id
            """
        )
        return await cursor.fetchall()
    finally:
        await db.close()


async def get_admin_subscriptions(admin_user_id: str) -> list[aiosqlite.Row]:
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM subscriptions
            WHERE admin_user_id = ?
            ORDER BY enabled DESC, group_id ASC
            """,
            (admin_user_id,),
        )
        return await cursor.fetchall()
    finally:
        await db.close()


async def get_hourly_summary(*, group_id: str, hour_start: str):
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM hourly_summaries
            WHERE group_id = ? AND hour_start = ?
            LIMIT 1
            """,
            (group_id, hour_start),
        )
        return await cursor.fetchone()
    finally:
        await db.close()


async def save_hourly_images(*, rows: list[dict[str, str]]) -> list[aiosqlite.Row]:
    if not rows:
        return []

    inserted_rows: list[aiosqlite.Row] = []
    db = await _open_db()
    try:
        for row in rows:
            cursor = await db.execute(
                """
                INSERT OR IGNORE INTO hourly_images (
                    group_id, hour_start, create_time,
                    user_id, sender_name, image_url, file_unique
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["group_id"],
                    row["hour_start"],
                    row["create_time"],
                    row.get("user_id", ""),
                    row.get("sender_name", ""),
                    row["image_url"],
                    row.get("file_unique", ""),
                ),
            )
            if not cursor.rowcount:
                continue
            select_cursor = await db.execute(
                """
                SELECT * FROM hourly_images
                WHERE group_id = ? AND hour_start = ? AND image_url = ? AND file_unique = ?
                LIMIT 1
                """,
                (
                    row["group_id"],
                    row["hour_start"],
                    row["image_url"],
                    row.get("file_unique", ""),
                ),
            )
            saved_row = await select_cursor.fetchone()
            if saved_row:
                inserted_rows.append(saved_row)
        await db.commit()
        return inserted_rows
    finally:
        await db.close()


async def get_hourly_images(*, group_id: str, hour_start: str) -> list[aiosqlite.Row]:
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM hourly_images
            WHERE group_id = ? AND hour_start = ?
            ORDER BY create_time ASC, id ASC
            """,
            (group_id, hour_start),
        )
        return await cursor.fetchall()
    finally:
        await db.close()


async def update_hourly_image_summary(*, image_id: int, image_summary: str) -> None:
    db = await _open_db()
    try:
        await db.execute(
            """
            UPDATE hourly_images
            SET image_summary = ?
            WHERE id = ?
            """,
            (image_summary, image_id),
        )
        await db.commit()
    finally:
        await db.close()


async def save_hourly_summary(
    *,
    group_id: str,
    group_name: str,
    hour_start: str,
    hour_end: str,
    message_count: int,
    image_count: int,
    summary_text: str,
) -> None:
    db = await _open_db()
    try:
        await db.execute(
            """
            INSERT INTO hourly_summaries (
                group_id, group_name, hour_start, hour_end,
                message_count, image_count, summary_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(group_id, hour_start) DO UPDATE SET
                group_name = excluded.group_name,
                hour_end = excluded.hour_end,
                message_count = excluded.message_count,
                image_count = excluded.image_count,
                summary_text = excluded.summary_text
            """,
            (
                group_id,
                group_name,
                hour_start,
                hour_end,
                message_count,
                image_count,
                summary_text,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def get_day_summaries(
    *,
    group_id: str,
    day_start: str,
    day_end: str,
) -> list[aiosqlite.Row]:
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            SELECT * FROM hourly_summaries
            WHERE group_id = ? AND hour_start >= ? AND hour_start < ?
            ORDER BY hour_start ASC
            """,
            (group_id, day_start, day_end),
        )
        return await cursor.fetchall()
    finally:
        await db.close()


async def delete_day_summaries(
    *,
    group_id: str,
    day_start: str,
    day_end: str,
) -> int:
    db = await _open_db()
    try:
        cursor = await db.execute(
            """
            DELETE FROM hourly_summaries
            WHERE group_id = ? AND hour_start >= ? AND hour_start < ?
            """,
            (group_id, day_start, day_end),
        )
        await db.commit()
        return cursor.rowcount
    finally:
        await db.close()
