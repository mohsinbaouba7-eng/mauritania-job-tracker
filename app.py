"""
app.py — Local and Worldwide Job Tracker
Developed by Mohsin Bewba

Reads the CSV produced by the scraper (mauritania_all_data_jobs.csv) and shows:
  - A horizontal bar chart of job postings by category, broken down by platform
  - Accurate average YEARLY salary and average HOURLY salary in USD
    (converted/normalized across whatever "Salary Type" each row has, then
    converted from MRU to USD)
  - Data from all scraped platforms
  - Restricted to 7 job categories: Data Analyst, Business Analyst, Data Engineer,
    Administrative Assistant, Secretary, Data Scientist, Cashier

Run with:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
import plotly.express as px

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------

CSV_PATH = "mauritania_all_data_jobs.csv"

# Standard full-time assumptions used to convert between salary periods.
HOURS_PER_WEEK = 40
WEEKS_PER_YEAR = 52
HOURS_PER_YEAR = HOURS_PER_WEEK * WEEKS_PER_YEAR          # 2080
HOURS_PER_MONTH = HOURS_PER_YEAR / 12                     # ~173.33

# MRU -> USD conversion rate. Mid-market rate as of July 2026 was roughly
# 1 USD = 40 MRU (i.e. 1 MRU ≈ 0.025 USD). Update this if rates move a lot.
MRU_TO_USD = 0.025

# Plausibility bounds (in normalized YEARLY MRU) used to catch bad rows —
# e.g. a posting tagged "Hourly" whose "Salary Amount" is actually a monthly
# or yearly figure. Those rows get multiplied by HOURS_PER_YEAR and blow up
# to absurd numbers (tens of thousands of dollars an hour). Any normalized
# yearly figure outside this range is treated as unreliable and excluded
# from the averages (though the raw row is still shown in the table).
MIN_PLAUSIBLE_YEARLY_MRU = 100_000      # ~ $2,500/yr
MAX_PLAUSIBLE_YEARLY_MRU = 8_000_000    # ~ $200,000/yr

# The 7 categories this dashboard should show. Keys match the "Category"
# values produced by the scraper's role_buckets; values are the labels
# shown in the UI (renaming "BI & Analytics" to "Business Analyst" and
# "Administrative Assistant" kept as-is per the request).
TARGET_CATEGORIES = {
    "Data Analyst": "Data Analyst",
    "BI & Analytics": "Business Analyst",
    "Data Engineer": "Data Engineer",
    "Administrative Assistant": "Administrative Assistant",
    "Secretary": "Secretary",
    "Data Scientist": "Data Scientist",
    "Cashier": "Cashier",
}


# ----------------------------------------------------------------------------
# DATA LOADING + CLEANING
# ----------------------------------------------------------------------------

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Keep only the 7 target categories, and relabel for display.
    df = df[df["Category"].isin(TARGET_CATEGORIES.keys())].copy()
    df["Job Category"] = df["Category"].map(TARGET_CATEGORIES)

    # Normalize salary fields
    df["Salary Amount"] = pd.to_numeric(df["Salary Amount"], errors="coerce").fillna(0)
    df["Salary Type"] = df["Salary Type"].fillna("Not Specified")

    # A salary is usable only if it's a positive number with a known period.
    usable = (df["Salary Amount"] > 0) & (df["Salary Type"].isin(["Hourly", "Monthly", "Yearly"]))

    df["Yearly Salary"] = pd.NA
    df["Hourly Salary"] = pd.NA

    def to_yearly(amount, period):
        if period == "Hourly":
            return amount * HOURS_PER_YEAR
        if period == "Monthly":
            return amount * 12
        if period == "Yearly":
            return amount
        return pd.NA

    def to_hourly(amount, period):
        if period == "Hourly":
            return amount
        if period == "Monthly":
            return amount / HOURS_PER_MONTH
        if period == "Yearly":
            return amount / HOURS_PER_YEAR
        return pd.NA

    df.loc[usable, "Yearly Salary"] = df.loc[usable].apply(
        lambda r: to_yearly(r["Salary Amount"], r["Salary Type"]), axis=1
    )
    df.loc[usable, "Hourly Salary"] = df.loc[usable].apply(
        lambda r: to_hourly(r["Salary Amount"], r["Salary Type"]), axis=1
    )

    df["Yearly Salary"] = pd.to_numeric(df["Yearly Salary"], errors="coerce")
    df["Hourly Salary"] = pd.to_numeric(df["Hourly Salary"], errors="coerce")

    # Flag rows whose normalized yearly figure falls outside a plausible
    # range (likely a mislabeled Salary Type) and null them out so they
    # don't distort the averages.
    implausible = df["Yearly Salary"].notna() & (
        (df["Yearly Salary"] < MIN_PLAUSIBLE_YEARLY_MRU)
        | (df["Yearly Salary"] > MAX_PLAUSIBLE_YEARLY_MRU)
    )
    df["Salary Flagged"] = implausible
    df.loc[implausible, ["Yearly Salary", "Hourly Salary"]] = pd.NA

    # Convert normalized MRU salaries to USD.
    df["Yearly Salary (USD)"] = df["Yearly Salary"] * MRU_TO_USD
    df["Hourly Salary (USD)"] = df["Hourly Salary"] * MRU_TO_USD

    return df


# ----------------------------------------------------------------------------
# APP LAYOUT
# ----------------------------------------------------------------------------

st.set_page_config(page_title="Local and Worldwide Job Tracker", layout="wide")
st.title("🌍 Local and Worldwide Job Tracker")
st.caption("Job postings and salary insights across all scraped platforms")
st.caption("Developed by Mohsin Bewba")

try:
    data = load_data(CSV_PATH)
except FileNotFoundError:
    st.error(
        f"Couldn't find '{CSV_PATH}'. Run the scraper first so this file exists "
        f"in the same folder as app.py, or upload it below."
    )
    uploaded = st.file_uploader("Upload mauritania_all_data_jobs.csv", type="csv")
    if uploaded is None:
        st.stop()
    data = load_data(uploaded)

if data.empty:
    st.warning("No rows found for the 7 target job categories in this dataset.")
    st.stop()

# --- Sidebar filters -----------------------------------------------------
st.sidebar.header("Filters")

all_platforms = sorted(data["Source Platform"].dropna().unique().tolist())
selected_platform = st.sidebar.selectbox(
    "Platform", options=["All Platforms"] + all_platforms
)

all_categories = list(TARGET_CATEGORIES.values())
selected_category = st.sidebar.selectbox(
    "Job category", options=["All Categories"] + all_categories
)

platform_filter = (
    data["Source Platform"].isin(all_platforms)
    if selected_platform == "All Platforms"
    else data["Source Platform"] == selected_platform
)
category_filter = (
    data["Job Category"].isin(all_categories)
    if selected_category == "All Categories"
    else data["Job Category"] == selected_category
)

filtered = data[platform_filter & category_filter]

if filtered.empty:
    st.warning("No postings match the current filter selection.")
    st.stop()

# --- KPIs: accurate average yearly / hourly salary (USD) -------------------
avg_yearly_usd = filtered["Yearly Salary (USD)"].dropna().mean()
avg_hourly_usd = filtered["Hourly Salary (USD)"].dropna().mean()
n_with_salary = filtered["Yearly Salary (USD)"].notna().sum()

col1, col2, col3, col4 = st.columns(4)
SALARY_LABEL_SIZE = "0.8rem"   # font size for the "Avg Yearly/Hourly Salary" labels
SALARY_VALUE_SIZE = "1.3rem"   # font size for the salary figures (smaller than default metric size)

def salary_metric(container, label, value):
    with container:
        st.caption(label)  # theme-aware label color, so it stays visible in light or dark mode
        st.markdown(
            f"<div style='font-size:{SALARY_VALUE_SIZE}; font-weight:600; line-height:1.4; margin-top:-0.5rem;'>{value}</div>",
            unsafe_allow_html=True,
        )

col1.metric("Job Postings (filtered)", f"{len(filtered):,}")
salary_metric(
    col2,
    "Avg Yearly Salary",
    f"${avg_yearly_usd:,.0f} USD" if pd.notna(avg_yearly_usd) else "N/A",
)
salary_metric(
    col3,
    "Avg Hourly Salary",
    f"${avg_hourly_usd:,.2f} USD" if pd.notna(avg_hourly_usd) else "N/A",
)
col4.metric("Postings with usable salary data", f"{n_with_salary:,}")

n_flagged = int(filtered["Salary Flagged"].sum())
st.caption(
    "Yearly/hourly figures are normalized across whatever period each posting listed "
    f"(hourly, monthly, yearly), assuming a {HOURS_PER_WEEK}-hour work week, then "
    f"converted from MRU to USD at an approximate rate of 1 MRU = {MRU_TO_USD} USD. "
    "Postings with no parsable salary are excluded from these averages but still "
    "count toward the postings chart below. "
    + (
        f"{n_flagged:,} posting(s) had an implausible salary (likely a mislabeled "
        "Salary Type, e.g. an 'Hourly' amount that was really monthly/yearly) and "
        "were excluded from the averages — see the 'Salary Flagged' column below."
        if n_flagged
        else ""
    )
)

st.divider()

# --- Bar chart: postings by category, split by platform (horizontal) ------
st.subheader("Job Postings by Category and Platform")

counts = (
    filtered.groupby(["Job Category", "Source Platform"])
    .size()
    .reset_index(name="Postings")
)

fig_counts = px.bar(
    counts,
    y="Job Category",
    x="Postings",
    color="Source Platform",
    barmode="group",
    orientation="h",
    category_orders={"Job Category": all_categories},
    title="Postings per Job Category, by Platform",
)
fig_counts.update_layout(yaxis_title="", xaxis_title="Number of Postings")
st.plotly_chart(fig_counts, use_container_width=True)

# --- Bar chart: average yearly salary by category (USD, horizontal) -------
st.subheader("Average Yearly Salary by Category (USD)")

salary_by_cat = (
    filtered.dropna(subset=["Yearly Salary (USD)"])
    .groupby("Job Category")["Yearly Salary (USD)"]
    .mean()
    .reindex(all_categories)
    .reset_index()
)

fig_salary = px.bar(
    salary_by_cat,
    y="Job Category",
    x="Yearly Salary (USD)",
    orientation="h",
    category_orders={"Job Category": all_categories},
    title="Average Yearly Salary (USD) by Job Category",
)
fig_salary.update_layout(yaxis_title="", xaxis_title="Avg Yearly Salary (USD)")
st.plotly_chart(fig_salary, use_container_width=True)

st.divider()

# --- Raw data table ---------------------------------------------------------
st.subheader("Filtered Postings")
st.dataframe(
    filtered[
        [
            "Job Title", "Company", "Job Category", "Source Platform",
            "Salary Amount", "Salary Type", "Yearly Salary (USD)", "Hourly Salary (USD)",
            "Salary Flagged", "Applicant Count",
        ]
    ].sort_values(["Job Category", "Source Platform"]),
    use_container_width=True,
)
