# PostgreSQL → BigQuery Data Migration

Migrating a legacy "on-premise" PostgreSQL database (the DVD Rental sample database, running in Docker) to Google BigQuery, with profiling, type mapping, Parquet staging, validation and Airflow orchestration.

## Architecture

```
PostgreSQL (Docker) → Profile & map schema → Parquet files → GCS staging → BigQuery → Validation
                           (orchestrated end to end by Airflow)
```

## Project status

- [x] Repo setup
- [ ] Step 1: Source database in Docker
- [ ] Step 2: Profiling and schema mapping
- [ ] Step 3: Extract to Parquet
- [ ] Step 4: Load to BigQuery
- [ ] Step 5: Validation
- [ ] Step 6: Airflow orchestration

## Tech stack

Python, PostgreSQL, Docker, pandas, SQLAlchemy, PyArrow, Google Cloud Storage, BigQuery, Apache Airflow

## How to run

```bash
# 1. Install dependencies
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env            # then edit .env

# 3. Start the source database (put dvdrental.tar in data/source/ first)
docker compose up -d

# 4. Profile the source
python scripts/profiler.py
```

## Repository structure

```
config/schema_map.json   PostgreSQL → BigQuery type mapping
scripts/profiler.py      Pre-migration data profiling
init/                    Restores the sample database on first start
docs/                    Profile and validation reports
dags/                    Airflow DAG (Step 6)
```
