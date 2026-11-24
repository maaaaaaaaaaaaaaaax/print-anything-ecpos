from pathlib import Path

import aiosqlite


async def apply_migrations(connection: aiosqlite.Connection, directory: Path) -> None:
    await connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
    await connection.commit()
    for migration in sorted(directory.glob("*.sql")):
        cursor = await connection.execute(
            "SELECT 1 FROM schema_migrations WHERE name = ?",
            (migration.name,),
        )
        applied = await cursor.fetchone()
        await cursor.close()
        if applied is not None:
            continue
        await connection.executescript(migration.read_text(encoding="ascii"))
        await connection.execute(
            "INSERT INTO schema_migrations (name) VALUES (?)",
            (migration.name,),
        )
        await connection.commit()
