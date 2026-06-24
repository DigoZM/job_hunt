# streamlit_app.py
# streamlit run streamlit_app.py
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, date

from db import get_connection, init_db, add_application, update_application

st.set_page_config(
    page_title="Job Hunting Dashboard",
    layout="wide",
)


@st.cache_data
def load_jobs():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM jobs;", conn)
    conn.close()
    return df


@st.cache_data
def load_applications():
    conn = get_connection()
    query = """
        SELECT
            a.application_id,
            a.job_id,
            a.saved_at,
            a.status,
            a.reached_out,
            j.company,
            j.title,
            j.location,
            j.country,
            j.job_level,
            j.job_type,
            j.date_posted,
            j.job_url
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        ORDER BY datetime(a.saved_at) DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def refresh_caches():
    load_jobs.clear()
    load_applications.clear()


def job_explorer():
    st.header("Job Explorer")

    jobs_df = load_jobs()
    if jobs_df.empty:
        st.info("No jobs in the database yet. Run the scraper first.")
        return

    st.sidebar.subheader("Filters")

    countries = sorted(jobs_df["country"].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect("Country", countries, default=countries)

    levels = sorted(jobs_df["job_level"].dropna().unique().tolist())
    selected_levels = st.sidebar.multiselect("Job level", levels, default=levels)

    job_types = sorted(jobs_df["job_type"].dropna().unique().tolist()) if "job_type" in jobs_df.columns else []
    selected_types = (
        st.sidebar.multiselect("Job type", job_types, default=job_types) if job_types else []
    )

    date_col = "date_posted" if "date_posted" in jobs_df.columns else "scraped_at"
    jobs_df[date_col] = pd.to_datetime(jobs_df[date_col], errors="coerce")
    min_date = jobs_df[date_col].min().date() if jobs_df[date_col].notna().any() else date.today()
    max_date = jobs_df[date_col].max().date() if jobs_df[date_col].notna().any() else date.today()

    start_date, end_date = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    df = jobs_df.copy()
    if selected_countries:
        df = df[df["country"].isin(selected_countries)]
    if selected_levels:
        df = df[df["job_level"].isin(selected_levels)]
    if selected_types:
        df = df[df["job_type"].isin(selected_types)]

    if isinstance(start_date, date) and isinstance(end_date, date):
        mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
        df = df[mask]

    st.write(f"Showing {len(df)} jobs")

    if df.empty:
        st.info("No jobs match your filters.")
        return

    if "selected_job_id" not in st.session_state or st.session_state.selected_job_id not in df["id"].tolist():
        st.session_state.selected_job_id = df.iloc[0]["id"]

    left_col, right_col = st.columns([1.4, 1])

    with left_col:
        st.subheader("Jobs")

        header_cols = st.columns([2, 3, 2, 1.5, 1.5])
        header_cols[0].markdown("**Company**")
        header_cols[1].markdown("**Title**")
        header_cols[2].markdown("**Location**")
        header_cols[3].markdown("**Level**")
        header_cols[4].markdown("**Date**")

        with st.container(height=500):
            for _, row in df.reset_index(drop=True).iterrows():
                row_cols = st.columns([2, 3, 2, 1.5, 1.5])

                selected = row["id"] == st.session_state.selected_job_id
                button_label = "▶" if selected else "View"

                with row_cols[0]:
                    if st.button(
                        f"{button_label} {row['company']}",
                        key=f"select_{row['id']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_job_id = row["id"]

                row_cols[1].write(row["title"])
                row_cols[2].write(row["location"])
                row_cols[3].write(row["job_level"])

                date_value = row[date_col]
                row_cols[4].write(
                    date_value.strftime("%Y-%m-%d") if pd.notna(date_value) else "-"
                )

    with right_col:
        st.subheader("Job details")

        selected_job = df[df["id"] == st.session_state.selected_job_id]
        if selected_job.empty:
            st.session_state.selected_job_id = df.iloc[0]["id"]
            selected_job = df[df["id"] == st.session_state.selected_job_id]

        job_row = selected_job.iloc[0]

        st.markdown(f"## {job_row['title']}")
        st.markdown(f"**Company:** {job_row['company']}")
        st.markdown(f"**Location:** {job_row['location']}")
        if "job_type" in job_row and pd.notna(job_row["job_type"]):
            st.markdown(f"**Job type:** {job_row['job_type']}")
        st.markdown(f"**Level:** {job_row['job_level']}")
        st.markdown(f"[Open job on LinkedIn]({job_row['job_url']})")

        st.markdown("### Description")
        with st.container(height=500):
            st.write(job_row["description"])

        if st.button("Mark as interested (add to Application Tracker)"):
            add_application(job_id=str(job_row["id"]), status="saved")
            refresh_caches()
            st.success("Job added to Application Tracker.")

def application_tracker():
    st.header("Application Tracker")

    apps_df = load_applications()
    if apps_df.empty:
        st.info("No applications yet. Mark some jobs as interested from the Job Explorer.")
        return

    # Sidebar filters
    st.sidebar.subheader("Application Filters")
    statuses = sorted(apps_df["status"].unique().tolist())
    selected_statuses = st.sidebar.multiselect("Status", statuses, default=statuses)

    reached_options = {
        "All": None,
        "Reached out": 1,
        "Did not reach out": 0,
    }
    reached_choice = st.sidebar.selectbox("Reached out?", list(reached_options.keys()))
    reached_filter_val = reached_options[reached_choice]

    df = apps_df.copy()
    if selected_statuses:
        df = df[df["status"].isin(selected_statuses)]
    if reached_filter_val is not None:
        df = df[df["reached_out"] == reached_filter_val]

    st.write(f"Showing {len(df)} applications")

    # Editable table-like UI
    for idx, row in df.iterrows():
        with st.expander(f"{row['title']} @ {row['company']}"):
            st.markdown(f"**Location:** {row['location']}")
            if pd.notna(row.get("job_type")):
                st.markdown(f"**Job type:** {row['job_type']}")
            st.markdown(f"**Saved at:** {row['saved_at']}")
            st.markdown(f"[Open job on LinkedIn]({row['job_url']})")

            col1, col2 = st.columns(2)

            with col1:
                new_status = st.selectbox(
                    "Status",
                    options=["saved", "applied", "waiting", "interview", "rejected", "rejected_interview"],
                    index=["saved", "applied", "waiting", "interview", "rejected", "rejected_interview"].index(row["status"]),
                    key=f"status_{row['application_id']}",
                )

            with col2:
                new_reached = st.checkbox(
                    "Reached out to someone?",
                    value=bool(row["reached_out"]),
                    key=f"reached_{row['application_id']}",
                )

            if st.button("Save changes", key=f"save_{row['application_id']}"):
                update_application(row["application_id"], status=new_status, reached_out=new_reached)
                refresh_caches()
                st.success("Updated.")
                st.experimental_rerun()


def main():
    init_db()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Job Explorer", "Application Tracker"])

    if st.sidebar.button("Refresh data"):
        refresh_caches()

    if page == "Job Explorer":
        job_explorer()
    else:
        application_tracker()


if __name__ == "__main__":
    main()
