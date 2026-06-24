# Job Search Application

This project is a job search application that fetches job postings, processes them, and displays the results using a Streamlit web application.

---

## Features
- Fetches job postings based on search term combinations.
- Processes and filters job data.
- Displays results in an interactive Streamlit app.

---

## Installation Guide

### 1. Clone the Repository
To get started, clone this repository to your local machine:
```bash
git clone https://github.com/DigoZM/job_hunt.git
cd job_hunt
```

### 2. Create and Activate a Virtual Environment
It is recommended to use a virtual environment to manage dependencies:

```bash
python3 -m venv job-env
source job-env/bin/activate
```

### 3. Install Dependencies
Install the required Python packages listed in requirements.txt:

```bash
pip install -r requirements.txt
```

---

## Configuration
### 1. Edit the config.py File
The config.py file contains the configuration settings for the application. Open the file and update the necessary fields, such as:

Search terms: Define the terms to search for.
API keys (if applicable): Add any required API keys for job fetching services.
Example:
```bash

    SEARCH_CONFIG = {
    "search_terms": ["MEMS", "electrical engineer"],
    "locations": ["Denmark", "Norway", "Sweden", "Finland"],
    "results_per_search": 2,  # Jobs per search term/location combo
    "hours_old": 48,  # Last 2 days 
}
```

---
## How It Works
### 1. Search for Job Postings
The application searches for job postings based on combinations of search terms and locations defined in config.py. For example:

 - Search terms: ["MEMS", "electrical engineer"]
 - Locations: ["Denmark", "Norway"]
The application will generate combinations like:

 - MEMS + Denmark
 - MEMS + Norway
 - electrical engineer + Denmark
 - electrical engineer + Norway

### 2. Fetch and Save Jobs
The job postings are fetched and saved into a database (jobs.db) or intermediate files (e.g., CSVs).

### 3. Run the Streamlit App
The Streamlit app reads the processed job data and displays it in an interactive web interface.

---

## Running the Application
To start the Streamlit app, run the following command:
```bash
streamlit run streamlit_app.py
```

This will launch the app in your default web browser. You can interact with the app to view and filter job postings.
 
---

## Notes

Ensure the config.py file is properly configured before running the application.
If you encounter any issues, check the logs or ensure all dependencies are installed correctly.