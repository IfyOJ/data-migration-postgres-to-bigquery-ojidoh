"""
extract.py - Step 3: extract every table from PostgreSQL into Parquet files.

For each table it:
  - reads rows in batches (so large tables never have to fit in memory)
  - applies config/schema_map.json: a `column_overrides` rule for that exact
    column wins, otherwise the general type rules apply
      * film.rating (enum)              -> STRING
      * film.special_features (array)   -> REPEATED STRING (a list)
      * film.fulltext (tsvector)        -> dropped
  - writes data/raw/<table>.parquet (snappy compressed, explicit schema)
  - records row counts, schema and timings in data/raw/_manifest.json
    (Step 4 uses the schema, Step 5 uses the row counts)

Incremental mode only pulls rows whose `last_update` is newer than the last run.
Tables without a `last_update` column (e.g. payment) are always extracted in full.

Run from the repo root:
  python scripts/extract.py                       # full extract of every table
  python scripts/extract.py --tables film actor   # just some tables
  python scripts/extract.py --incremental         # only changed rows
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import text

# Reuse the connection, type-mapping and table-listing logic from Step 2
from profiler import get_engine, get_tables, load_schema_map, map_type

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
INCREMENTAL_DIR = RAW_DIR / "incremental"
LOG_DIR = ROOT / "logs"
STATE_FILE = RAW_DIR / "_state.json"        # last `last_update` seen per table
MANIFEST_FILE = RAW_DIR / "_manifest.json"  # what was extracted, for Steps 4 and 5

BATCH_SIZE = 50_000
WATERMARK_COLUMN = "last_update"

# BigQuery type -> Parquet (Arrow) type
ARROW_TYPES = {
    "INT64": pa.int64(),
    "NUMERIC": pa.decimal128(38, 9),  # same precision/scale as BigQuery NUMERIC
    "FLOAT64": pa.float64(),
    "STRING": pa.string(),
    "BOOL": pa.bool_(),
    "DATE": pa.date32(),
    "DATETIME": pa.timestamp("us"),              # no time zone
    "TIMESTAMP": pa.timestamp("us", tz="UTC"),   # time zone aware
    "TIME": pa.time64("us"),
    "BYTES": pa.binary(),
    "JSON": pa.string(),
}

log = logging.getLogger("extract")


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    log.setLevel(logging.INFO)
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_DIR / "extract.log")):
        handler.setFormatter(fmt)
        log.addHandler(handler)


def read_json(path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Column planning: decide how each source column is selected and stored
# ---------------------------------------------------------------------------

def resolve_column(table, name, pg_type, schema_map):
    """
    Decide how one column is migrated. Returns (bq_type, mode, source).

    A rule in `column_overrides` for this exact table.column wins.
    Otherwise the general type rules (type_map / special_cases) apply.
    `source` records which rule was used, for the log and the manifest.
    """
    override = schema_map.get("column_overrides", {}).get(table, {}).get(name)
    if override:
        if override.get("action") == "DROP":
            return None, "DROP", "override"
        return override["bigquery_type"], override.get("mode", "NULLABLE"), "override"
    bq_type, mode, _note = map_type(pg_type, schema_map)
    return bq_type, mode, "type rule"


def plan_columns(conn, table, schema_map):
    """Return (columns_to_extract, dropped_columns) for a table."""
    rows = conn.execute(text("""
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :t
        ORDER BY ordinal_position
    """), {"t": table}).fetchall()

    # Catch typos in the config: an override naming a column that doesn't exist
    existing = {r[0] for r in rows}
    for name in schema_map.get("column_overrides", {}).get(table, {}):
        if name not in existing:
            raise ValueError(f"column_overrides mentions {table}.{name}, but that column doesn't exist")

    columns, dropped = [], []
    for name, pg_type, udt_name in rows:
        bq_type, mode, source = resolve_column(table, name, pg_type, schema_map)

        if mode == "DROP":
            dropped.append(name)
            continue
        if bq_type == "UNMAPPED":
            raise ValueError(
                f"{table}.{name} has type '{pg_type}', which is not in config/schema_map.json"
            )

        select = f'"{name}"'
        convert = None
        arrow_type = ARROW_TYPES[bq_type]

        if mode == "REPEATED":                 # arrays -> list of strings
            select = f'"{name}"::text[] AS "{name}"'
            arrow_type = pa.list_(ARROW_TYPES[bq_type])
        elif bq_type == "STRING" and pg_type not in ("character varying", "character", "text"):
            select = f'"{name}"::text AS "{name}"'   # enums and other cast-to-text columns
        elif bq_type == "BYTES":               # psycopg2 returns memoryview
            convert = bytes
        elif bq_type == "JSON":                # psycopg2 returns dict/list
            convert = lambda v: v if isinstance(v, str) else json.dumps(v)

        columns.append({
            "name": name,
            "pg_type": pg_type if pg_type not in ("USER-DEFINED", "ARRAY") else f"{pg_type} ({udt_name})",
            "bq_type": bq_type,
            "mode": "REPEATED" if mode == "REPEATED" else "NULLABLE",
            "rule": source,
            "select": select,
            "arrow_type": arrow_type,
            "convert": convert,
        })
    return columns, dropped


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_table(engine, table, columns, out_path, since=None):
    """Stream a table into a Parquet file. Returns (row_count, max_watermark)."""
    names = [c["name"] for c in columns]
    sql = f'SELECT {", ".join(c["select"] for c in columns)} FROM "{table}"'
    params = {}
    if since is not None:
        sql += f' WHERE "{WATERMARK_COLUMN}" > :since'
        params["since"] = since

    wm_index = names.index(WATERMARK_COLUMN) if WATERMARK_COLUMN in names else None
    schema = pa.schema([pa.field(c["name"], c["arrow_type"]) for c in columns])
    tmp_path = out_path.with_name(out_path.name + ".tmp")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    row_count, max_wm = 0, None
    # stream_results uses a server-side cursor, so only one batch is in memory at a time
    with engine.connect().execution_options(stream_results=True) as conn:
        result = conn.execute(text(sql), params)
        with pq.ParquetWriter(tmp_path, schema, compression="snappy") as writer:
            while True:
                batch = result.fetchmany(BATCH_SIZE)
                if not batch:
                    break
                arrays = []
                for i, col in enumerate(columns):
                    conv = col["convert"]
                    values = [r[i] if (conv is None or r[i] is None) else conv(r[i]) for r in batch]
                    arrays.append(pa.array(values, type=col["arrow_type"]))
                writer.write_table(pa.Table.from_arrays(arrays, schema=schema))

                row_count += len(batch)
                if wm_index is not None:
                    batch_max = max((r[wm_index] for r in batch if r[wm_index] is not None), default=None)
                    if batch_max is not None and (max_wm is None or batch_max > max_wm):
                        max_wm = batch_max

    if since is not None and row_count == 0:
        tmp_path.unlink()          # nothing changed: don't leave an empty file behind
        return 0, None
    tmp_path.replace(out_path)     # only replace the old file once the new one is complete
    return row_count, max_wm


def run(selected_tables=None, incremental=False):
    setup_logging()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log.info("=" * 60)
    log.info(f"Extract run {run_id}  mode={'incremental' if incremental else 'full'}")

    engine = get_engine()
    schema_map = load_schema_map()
    state = read_json(STATE_FILE, {})
    manifest = read_json(MANIFEST_FILE, {"tables": {}})

    with engine.connect() as conn:
        tables = get_tables(conn)
        if selected_tables:
            missing = set(selected_tables) - set(tables)
            if missing:
                log.error(f"Unknown table(s): {', '.join(sorted(missing))}")
                return 1
            tables = [t for t in tables if t in selected_tables]
        plans = {t: plan_columns(conn, t, schema_map) for t in tables}

    failures, summary = [], []
    for table in tables:
        columns, dropped = plans[table]
        has_wm = any(c["name"] == WATERMARK_COLUMN for c in columns)
        since = None
        if incremental and has_wm and table in state:
            since = datetime.fromisoformat(state[table])

        if since is not None:
            out_path = INCREMENTAL_DIR / f"{table}_{run_id}.parquet"
            mode = "incremental"
        else:
            out_path = RAW_DIR / f"{table}.parquet"
            mode = "full"

        start = time.perf_counter()
        try:
            rows, max_wm = extract_table(engine, table, columns, out_path, since)
        except Exception as exc:
            log.exception(f"{table}: FAILED - {exc}")
            failures.append(table)
            continue
        seconds = time.perf_counter() - start

        if max_wm is not None:
            state[table] = max_wm.isoformat()

        note = f"  dropped: {', '.join(dropped)}" if dropped else ""
        if mode == "incremental" and rows == 0:
            log.info(f"{table:<15} no changes since {since}")
        else:
            size_kb = out_path.stat().st_size / 1024
            log.info(f"{table:<15} {rows:>8,} rows  {size_kb:>8,.1f} KB  {seconds:5.2f}s  [{mode}]{note}")

        summary.append(rows)
        if mode == "full":
            manifest["tables"][table] = {
                "file": str(out_path.relative_to(ROOT)),
                "row_count": rows,
                "extracted_at": run_id,
                "dropped_columns": dropped,
                "watermark": state.get(table),
                "schema": [
                    {"name": c["name"], "pg_type": c["pg_type"], "type": c["bq_type"],
                     "mode": c["mode"], "rule": c["rule"]}
                    for c in columns
                ],
            }
        elif rows:
            manifest["tables"][table].setdefault("incremental_files", []).append(
                {"file": str(out_path.relative_to(ROOT)), "row_count": rows, "extracted_at": run_id}
            )

    # Save state and manifest so the next run (and Steps 4-5) know what happened
    write_json(STATE_FILE, state)
    manifest["last_run"] = run_id
    write_json(MANIFEST_FILE, manifest)

    log.info(f"Done: {len(tables) - len(failures)}/{len(tables)} tables, {sum(summary):,} rows extracted")
    if failures:
        log.error(f"Failed tables: {', '.join(failures)}")
        return 1   # non-zero exit code so Airflow (Step 6) marks the task as failed
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PostgreSQL tables to Parquet")
    parser.add_argument("--tables", nargs="+", help="only extract these tables")
    parser.add_argument("--incremental", action="store_true",
                        help="only extract rows changed since the last run")
    args = parser.parse_args()
    sys.exit(run(args.tables, args.incremental))
