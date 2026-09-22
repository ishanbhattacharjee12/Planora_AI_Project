"""Lightweight schema sync for existing SQLite databases.

SQLAlchemy's create_all only creates missing tables; it does not add new columns
to tables that already exist. This helper aligns the live schema with models.
"""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from app.database import Base
import app.models  # noqa: F401 - register ORM tables with metadata


def sync_missing_columns(connection: Connection) -> None:
    inspector = inspect(connection)
    dialect = connection.dialect

    for table_name, table in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue

        existing = {column["name"] for column in inspector.get_columns(table_name)}

        for column in table.columns:
            if column.name in existing:
                continue

            col_type = column.type.compile(dialect=dialect)
            statement = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"

            if column.server_default is not None:
                default = column.server_default.arg
                if isinstance(default, str):
                    statement += f" DEFAULT '{default}'"
                else:
                    statement += f" DEFAULT {default}"
            elif not column.nullable and column.default is None:
                # SQLite needs a default when adding NOT NULL to a populated table.
                statement += " DEFAULT ''"

            connection.execute(text(statement))
