"""
profiler.py - Step 2: profile the source PostgreSQL database before migrating it.

For every table in the `public` schema it records:
  - row count
  - each column's PostgreSQL type, nullability and null count
  - primary key columns
  - the BigQuery type it will map to (from config/schema_map.json)

Outputs:
  docs/profile_report.csv  - one row per column (easy to open in Excel)
  docs/profile_report.md   - readable summary for your README / GitHub

Run from the repo root:
  python scripts/profiler.py
"""

import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SCHEMA_MAP_PATH = ROOT / "config" / "schema_map.json"


def get_engine():
    load_dotenv(ROOT / ".env")
    url = (
        f"postgresql+psycopg2://{os.getenv('PG_USER', 'postgres')}:"
        f"{os.getenv('PG_PASSWORD', 'mysecretpassword')}@"
        f"{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5432')}/"
        f"{os.getenv('PG_DATABASE', 'dvdrental')}"
    )
    return create_engine(url)


def load_schema_map():
    with open(SCHEMA_MAP_PATH) as f:
        return json.load(f)


def map_type(pg_type, schema_map):
    """Return (bigquery_type, mode, note) for a PostgreSQL data type."""
    if pg_type in schema_map["type_map"]:
        return schema_map["type_map"][pg_type], "NULLABLE", ""
    special = schema_map["special_cases"].get(pg_type)
    if special:
        if special.get("action") == "DROP":
            return "-", "DROP", special["note"]
        return special["bigquery_type"], special.get("mode", "NULLABLE"), special["note"]
    return "UNMAPPED", "?", "Add this type to config/schema_map.json"


def get_tables(conn):
    rows = conn.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """))
    return [r[0] for r in rows]


def get_columns(conn, table):
    rows = conn.execute(text("""
        SELECT column_name, data_type, udt_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :t
        ORDER BY ordinal_position
    """), {"t": table})
    return rows.fetchall()


def get_primary_keys(conn, table):
    rows = conn.execute(text("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.table_name = :t
          AND tc.constraint_type = 'PRIMARY KEY'
    """), {"t": table})
    return {r[0] for r in rows}


def profile():
    engine = get_engine()
    schema_map = load_schema_map()
    column_rows, table_rows = [], []

    with engine.connect() as conn:
        tables = get_tables(conn)
        print(f"Found {len(tables)} tables\n")

        for table in tables:
            row_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
            columns = get_columns(conn, table)
            pks = get_primary_keys(conn, table)

            # Count nulls for every column in a single query
            null_exprs = ", ".join(
                f'COUNT(*) - COUNT("{c.column_name}") AS "{c.column_name}"' for c in columns
            )
            nulls = conn.execute(text(f'SELECT {null_exprs} FROM "{table}"')).mappings().one()

            for c in columns:
                bq_type, mode, note = map_type(c.data_type, schema_map)
                column_rows.append({
                    "table": table,
                    "column": c.column_name,
                    "pg_type": c.data_type if c.data_type not in ("USER-DEFINED", "ARRAY") else f"{c.data_type} ({c.udt_name})",
                    "nullable": c.is_nullable,
                    "null_count": nulls[c.column_name],
                    "primary_key": "yes" if c.column_name in pks else "",
                    "bigquery_type": bq_type,
                    "bigquery_mode": mode,
                    "note": note,
                })

            table_rows.append({
                "table": table,
                "row_count": row_count,
                "columns": len(columns),
                "primary_key": ", ".join(sorted(pks)) or "NONE",
            })
            print(f"  {table:<15} {row_count:>7,} rows  {len(columns):>2} columns")

    DOCS.mkdir(exist_ok=True)
    col_df = pd.DataFrame(column_rows)
    tbl_df = pd.DataFrame(table_rows)
    col_df.to_csv(DOCS / "profile_report.csv", index=False)

    flagged = col_df[col_df["note"] != ""]
    with open(DOCS / "profile_report.md", "w") as f:
        f.write("# Source Database Profile (dvdrental)\n\n")
        f.write(f"Tables: {len(tbl_df)}  |  Total rows: {tbl_df['row_count'].sum():,}\n\n")
        f.write("## Tables\n\n")
        f.write(tbl_df.to_markdown(index=False))
        f.write("\n\n## Columns needing special handling\n\n")
        f.write(flagged[["table", "column", "pg_type", "bigquery_type", "bigquery_mode", "note"]]
                .to_markdown(index=False) if not flagged.empty else "None\n")
        f.write("\n\n## All columns\n\n")
        f.write(col_df.to_markdown(index=False))
        f.write("\n")

    print(f"\nTotal rows: {tbl_df['row_count'].sum():,}")
    if not flagged.empty:
        print(f"{len(flagged)} column(s) need special handling - see docs/profile_report.md")
    print("Saved docs/profile_report.csv and docs/profile_report.md")


if __name__ == "__main__":
    profile()
