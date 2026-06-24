# db.py
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path("jobs.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            source TEXT,
            company TEXT,
            title TEXT,
            location TEXT,
            country TEXT,
            job_level TEXT,
            job_type TEXT,
            date_posted TEXT,
            scraped_at TEXT,
            description TEXT,
            job_url TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            saved_at TEXT NOT NULL,
            status TEXT NOT NULL,
            reached_out INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


def normalize_country(location_value: str) -> str:
    if not location_value:
        return None
    # Very simple heuristic – you can improve this as needed
    # Often LinkedIn location strings end with ", Country"
    parts = [p.strip() for p in location_value.split(",")]
    if len(parts) >= 2:
        return parts[-1]
    return location_value.strip()


def upsert_jobs_from_df(df: pd.DataFrame, source: str = "linkedin"):
    """
    Upsert jobs into jobs table, based on JobSpy DataFrame.
    Assumes df has: id, company, title, location, job_level, description, job_url, job_type, date_posted (if available).
    """
    if df.empty:
        return

    conn = get_connection()
    cur = conn.cursor()
    scraped_at = datetime.utcnow().isoformat(timespec="seconds")

    records = []
    for _, row in df.iterrows():
        job_id = str(row["id"])
        company = str(row.get("company", "")).strip()
        title = str(row.get("title", "")).strip()
        location = str(row.get("location", "")).strip()
        country = normalize_country(location)
        job_level = str(row.get("job_level", "")).strip()
        description = str(row.get("description", "")).strip()
        job_url = str(row.get("job_url", "")).strip()
        job_type = str(row.get("job_type", "")).strip() if "job_type" in df.columns else None
        date_posted = str(row.get("date_posted", "")).strip() if "date_posted" in df.columns else None

        records.append(
            (
                job_id,
                source,
                company,
                title,
                location,
                country,
                job_level,
                job_type,
                date_posted,
                scraped_at,
                description,
                job_url,
            )
        )

    cur.executemany(
        """
        INSERT INTO jobs (
            id, source, company, title, location, country,
            job_level, job_type, date_posted, scraped_at,
            description, job_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source=excluded.source,
            company=excluded.company,
            title=excluded.title,
            location=excluded.location,
            country=excluded.country,
            job_level=excluded.job_level,
            job_type=excluded.job_type,
            date_posted=excluded.date_posted,
            scraped_at=excluded.scraped_at,
            description=excluded.description,
            job_url=excluded.job_url;
        """,
        records,
    )

    conn.commit()
    conn.close()


def add_application(job_id: str, status: str = "saved"):
    conn = get_connection()
    cur = conn.cursor()
    saved_at = datetime.utcnow().isoformat(timespec="seconds")
    cur.execute(
        """
        INSERT INTO applications (job_id, saved_at, status, reached_out)
        VALUES (?, ?, ?, 0);
        """,
        (job_id, saved_at, status),
    )
    conn.commit()
    conn.close()


def update_application(application_id: int, status: str = None, reached_out: bool = None):
    conn = get_connection()
    cur = conn.cursor()
    fields = []
    params = []

    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if reached_out is not None:
        fields.append("reached_out = ?")
        params.append(1 if reached_out else 0)

    if not fields:
        conn.close()
        return

    params.append(application_id)
    cur.execute(f"UPDATE applications SET {', '.join(fields)} WHERE application_id = ?;", params)
    conn.commit()
    conn.close()