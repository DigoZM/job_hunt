"""
Simple Configuration - LinkedIn Job Scraper with Language Filter
"""

# ===== JOB SEARCH PARAMETERS =====
SEARCH_CONFIG = {
    "search_terms": ["robotics engineer", "mechatronics engineer"],
    "locations": ["European Economic Area"],
    # "locations": ["Germany", "Austria", "Switzerland", "Denmark", "Norway", "Sweden", "Finland", "Portugal"],
    # "locations": ["Denmark", "Norway", "Sweden", "Finland"],
    "results_per_search": 2,  # Jobs per search term/location combo
    "hours_old": 72,  # Last 7 days (168 hours)
}

# ===== YOUR PROFILE (Optional - for future filtering) =====
USER_PROFILE = {
    "languages": ["English", "Portuguese"]
}