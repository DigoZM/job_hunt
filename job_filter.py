# job_filter.py
"""
LinkedIn Job Filter - Scrape + Language Detection + DB storage
"""
import pandas as pd
from jobspy import scrape_jobs
from langdetect import detect
import re
import time
from datetime import datetime
import os

from config import SEARCH_CONFIG
from db import init_db, upsert_jobs_from_df


def detect_language(text):
    if not text or len(text.strip()) < 20:
        return "unknown"

    try:
        clean_text = re.sub(r'http\S+|www\S+|@\S+', '', text)
        lang = detect(clean_text)
        return lang
    except Exception:
        return "unknown"


def filter_english_jobs(df):
    print("\n🌍 Detecting job description languages...")
    df["language"] = df["description"].apply(detect_language)
    english_or_portuguese_jobs = df[df["language"].isin(["en", "pt"])].copy()

    print(f"Total jobs scraped: {len(df)}")
    print(f"English jobs: {len(english_or_portuguese_jobs)}")
    print(f"Filtered out: {len(df) - len(english_or_portuguese_jobs)}")

    return english_or_portuguese_jobs


def scrape_linkedin_jobs():
    """Scrapes jobs from LinkedIn and stores them in SQLite."""
    init_db()

    all_jobs = []

    print("\n🔍 Starting LinkedIn job scraping...")
    print(f"Search terms: {SEARCH_CONFIG['search_terms']}")
    print(f"Locations: {SEARCH_CONFIG['locations']}")
    print(f"Results per search: {SEARCH_CONFIG['results_per_search']}\n")

    for search_term in SEARCH_CONFIG["search_terms"]:
        for location in SEARCH_CONFIG["locations"]:
            print(f"  → Searching: '{search_term}' in {location}...")

            try:
                jobs = scrape_jobs(
                    site_name=["linkedin"],
                    search_term=search_term,
                    location=location,
                    results_wanted=SEARCH_CONFIG["results_per_search"],
                    hours_old=SEARCH_CONFIG["hours_old"],  # set to 24 for last 24h
                    linkedin_fetch_description=True,
                    verbose=0,
                )

                if jobs is not None and len(jobs) > 0:
                    all_jobs.append(jobs)
                    print(f"    ✓ Found {len(jobs)} jobs")
                else:
                    print("    ✗ No jobs found")

                time.sleep(2)  # Avoid rate limiting

            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                continue

    if not all_jobs:
        print("\n⚠ No jobs were scraped.")
        return None

    print("\n📦 Combining job results...")
    combined_jobs = pd.concat(all_jobs, ignore_index=True)

    # Filter English jobs
    english_jobs = filter_english_jobs(combined_jobs)

    # Filter Entry-Level jobs (you can extend this to include internships)
    filtered_jobs_mask = english_jobs["job_level"].str.lower().str.contains(
        "not applicable|entry level", na=False
    )
    filtered_jobs = english_jobs[filtered_jobs_mask].copy()

    # Keep important columns
    keep_cols = [
        "id",
        "company",
        "title",
        "location",
        "job_level",
        "description",
        "job_url",
    ]
    # Optional fields from JobSpy if present (job_type, date_posted)
    if "job_type" in filtered_jobs.columns:
        keep_cols.append("job_type")
    if "date_posted" in filtered_jobs.columns:
        keep_cols.append("date_posted")

    filtered_jobs = filtered_jobs[keep_cols]

    # Remove duplicates by id
    filtered_jobs = filtered_jobs.drop_duplicates(subset="id", keep="first")

    # Save CSV snapshot (optional)
    # Ensure the directory exists
    directory = "job_list"
    if not os.path.exists(directory):
        os.makedirs(directory)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    csv_name = f"{directory}/linkedin_english_jobs_{timestamp}.csv"
    filtered_jobs.to_csv(csv_name, index=False)
    print(f"\n💾 Saved {len(filtered_jobs)} Entry-Level English jobs to: {csv_name}")

    # Upsert into SQLite data lake
    upsert_jobs_from_df(filtered_jobs, source="linkedin")
    print("🗃  Jobs upserted into jobs.db")

    return filtered_jobs


if __name__ == "__main__":
    jobs = scrape_linkedin_jobs()
    if jobs is not None:
        print("\n✅ Job scraping completed!")