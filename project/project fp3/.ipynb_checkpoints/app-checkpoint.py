import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import os

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Chicago Crime in Focus – A Public Guide",
    layout="wide",
)

# =====================================================
# GLOBAL STYLING (LIGHT DATA-JOURNALISM LOOK)
# =====================================================
st.markdown(
    """
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .main-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #9ca3af;
        margin-bottom: 0.75rem;
    }
    .byline {
        font-size: 0.95rem;
        color: #d1d5db;
        margin-bottom: 1.5rem;
    }

    h2 {
        margin-top: 2.5rem;
        margin-bottom: 0.75rem;
    }

    .stApp {
        background: radial-gradient(circle at top, #111827 0, #020617 55%, #000000 100%);
        color: #e5e7eb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1150px;
    }

    div[data-testid="stMetric"] {
        background: rgba(15,23,42,0.9);
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
        border: 1px solid rgba(148,163,184,0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 0 18px rgba(15,23,42,0.6);
    }
    div[data-testid="stMetric"] > label {
        color: #cbd5f5 !important;
        font-size: 0.8rem !important;
    }
    div[data-testid="stMetric"] > div {
        color: #f9fafb !important;
        font-weight: 600 !important;
    }

    .helper {
        font-size: 0.85rem;
        color: #9ca3af;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# TITLE + BYLINE
# =====================================================
st.markdown('<div class="main-title">Chicago Crime in Focus</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">A decade of reported incidents, explained for everyday Chicagoans.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="byline">By Rohit Yadav, Pratyush Agarwal, and Mohak Bansal • IS445 Final Project – Viz for the Public</div>',
    unsafe_allow_html=True,
)

# =====================================================
# INTRO
# =====================================================
st.markdown(
    """
Over the last decade, Chicago has published detailed records of every reported crime in the city.
That information can feel overwhelming: hundreds of thousands of rows, dozens of columns, and
a lot of jargon. This page is meant to act like a guided tour, turning that raw data into a
story that a non-expert can read and explore.

The data shown here comes from the City of Chicago crime dataset. Each row is one incident:
when it happened, where it happened, what kind of offense it was, and a few additional details
such as whether an arrest was made. To keep the page fast and readable, we focus on one year at a
time and summarize the patterns rather than showing every point individually.

You can think of this page in three layers. First, there is one main chart that shows how crime
builds up over the course of a year. Then, two additional charts provide context: one looks at
which parts of the city report the most incidents, and the other shows when during the day incidents
tend to happen. Together, these views give a practical, human-scale sense of how public safety
looks in Chicago across different years.
"""
)

st.markdown("---")

# =====================================================
# DATA LOADING – SINGLE YEAR
# =====================================================

YEAR_TO_FILE = {
    year: f"project/data/Crimes_{year}.csv"
    for year in range(2010, 2021)  # 2010–2020 inclusive
}


@st.cache_data
def load_year_data(year: int) -> pd.DataFrame:
    """Load and lightly clean data for a single year."""
    path = YEAR_TO_FILE[year]

    if not os.path.exists(path):
        st.error(
            f"Could not find file `{path}` for year {year}. "
            "Make sure the CSV exists in the repo with that exact path and name."
        )
        return pd.DataFrame()

    df = pd.read_csv(path)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month
        df["YearMonth"] = df["Date"].dt.to_period("M").dt.to_timestamp()
        df["Hour"] = df["Date"].dt.hour
    else:
        if "Year" not in df.columns:
            df["Year"] = year

    if "Primary Type" in df.columns:
        df["Primary Type"] = df["Primary Type"].astype("string")

    if "District" in df.columns:
        df["District"] = df["District"].astype("string")

    return df


# =====================================================
# CONTROL PANEL
# =====================================================
with st.container():
    c1, c2 = st.columns([1, 2])

    available_years = sorted(YEAR_TO_FILE.keys())

    with c1:
        selected_year = st.selectbox(
            "Choose a year to explore",
            options=available_years,
            index=len(available_years) - 1,
            help="Only one year can be active at a time. Changing the year reloads the data.",
        )

    with st.spinner(f"Loading crime data for {selected_year}..."):
        data_year = load_year_data(selected_year)

    if data_year.empty:
        st.stop()

    with c2:
        if "Primary Type" in data_year.columns:
            primary_types = sorted(
                data_year["Primary Type"].dropna().unique().tolist()
            )
        else:
            primary_types = []

        selected_types = st.multiselect(
            "Optional filter: focus on specific crime types (otherwise, all types are included)",
            options=primary_types,
            default=[],
        )

filtered = data_year.copy()
if selected_types:
    filtered = filtered[filtered["Primary Type"].isin(selected_types)]

if filtered.empty:
    st.warning(
        "There are no incidents left after applying the selected filters. "
        "Try clearing the crime-type filter or pick a different year."
    )
    st.stop()

st.markdown(
    f"<div class='helper'>You are currently looking at <b>{len(filtered):,}</b> reported incidents from {selected_year}.</div>",
    unsafe_allow_html=True,
)

# =====================================================
# SECTION 1 – CENTRAL INTERACTIVE VIZ
# =====================================================

st.header("1. How Does Crime Build Up Over the Year? (Central Interactive Visualization)")

st.markdown(
    """
The first question many people have is simple: **how much crime happens in a typical year, and does it
seem to be clustered in particular months?** The chart below answers that by showing the number
of reported incidents per month for the year you selected above.

You can hover over the line to see exact counts. If you chose specific crime types in the filter
above, this chart will update to show **only** those categories. That lets you compare, for example,
a year of all crime to a year of just theft, robbery, or other offenses of particular interest.
"""
)

if "YearMonth" in filtered.columns:
    monthly = (
        filtered.dropna(subset=["YearMonth"])
        .groupby("YearMonth", as_index=False)
        .size()
        .rename(columns={"size": "Crime Count"})
    )

    base = alt.Chart(monthly).encode(
        x=alt.X(
            "YearMonth:T",
            title="Month in year",
            axis=alt.Axis(format="%b", labelAngle=0),
        ),
        y=alt.Y("Crime Count:Q", title="Number of reported crimes"),
    )

    line = base.mark_line(point=True).encode(
        tooltip=[
            alt.Tooltip("YearMonth:T", title="Month"),
            alt.Tooltip("Crime Count:Q", title="Reported crimes"),
        ]
    )

    chart = line.properties(
        width=900,
        height=400,
        title=f"Reported crimes by month in {selected_year}",
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.info(
        "Month-level information is not available for this dataset. "
        "Make sure the Date column was parsed correctly."
    )

# =====================================================
# SECTION 2 – CONTEXTUAL VIZ #1 (MAP: POINTS + HEATMAP)
# =====================================================

st.header("2. Where in the City Are These Crimes Happening? *(Contextual Visualization #1)*")

st.markdown(
    f"""
Raw numbers tell us **how many** crimes are reported in {selected_year}, but a map makes it much
easier to see **where** they cluster in the city.

Below you can switch between two views:

- **Individual incidents** – each point is one crime report  
- **Crime density heatmap** – bright areas show where many reports are concentrated  

This uses the same City of Chicago crime dataset, but focuses only on **location** and **density**
to give the public an intuitive feel for where incidents are happening.
"""
)

# Use the same filtered dataframe that powers the main charts,
# so the map responds to crime-type and other filters.
source_df = filtered

if {"Latitude", "Longitude"}.issubset(source_df.columns):
    map_base = source_df.dropna(subset=["Latitude", "Longitude"]).copy()


    if not map_base.empty:
        # Keep the map responsive for larger years
        max_points = 8000
        if len(map_base) > max_points:
            map_base = map_base.sample(n=max_points, random_state=42)

        # Center the camera explicitly on downtown Chicago
        view_state = pdk.ViewState(
            latitude=41.8781,    # Chicago city center
            longitude=-87.6298,
            zoom=10.5,
            pitch=40,
        )

        # Mode toggle: points vs heatmap
        map_mode = st.radio(
            "Choose how to view incidents on the map:",
            ["Individual incidents (points)", "Crime density (heatmap)"],
            index=0,
            help="Switch between seeing individual crime reports or overall density.",
        )

        if map_mode == "Individual incidents (points)":
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_base,
                get_position="[Longitude, Latitude]",
                get_radius=40,
                get_fill_color=[56, 189, 248, 140],  # teal-ish
                pickable=True,
            )
        else:
            layer = pdk.Layer(
                "HeatmapLayer",
                data=map_base,
                get_position="[Longitude, Latitude]",
                radius_pixels=40,
            )

        tooltip = {
            "html": "<b>Type:</b> {Primary Type}<br/>"
                    "<b>Location:</b> {Location Description}",
            "style": {
                "backgroundColor": "rgba(15,23,42,0.95)",
                "color": "white",
                "fontSize": "12px",
            },
        }

        deck = pdk.Deck(
            # Streets style feels closer to Google Maps
            map_style="mapbox://styles/mapbox/streets-v12",
            initial_view_state=view_state,
            layers=[layer],
            tooltip=tooltip,
        )

        st.pydeck_chart(deck)
        st.caption(
            "Note: to keep the app fast, this map shows a random sample of up to "
            f"{max_points:,} incidents from {selected_year}."
        )
    else:
        st.info(f"No latitude/longitude data available for {selected_year}.")
else:
    st.info(
        "Latitude and longitude columns ('Latitude', 'Longitude') are not available in this dataset. "
        "Make sure these columns exist in the CSV files."
    )

st.markdown(
    """
This **contextual visualization** was created by our group using the same City of Chicago crime dataset,
but rendered on an interactive basemap instead of as a bar chart.

For a public reader, this map is much easier to interpret than raw tables:

- You can **pan and zoom** like a familiar map application  
- You can switch between **individual incidents** and a **heatmap** to see density  
- You can visually compare downtown, neighborhood centers, and more residential areas  

It does not claim to be a perfect “safety map”, but it turns abstract incident records into a
geographic story that is far more intuitive to explore.
"""
)

# =====================================================
# SECTION 3 – CONTEXTUAL VIZ #2 (HOUR OF DAY)
# =====================================================

st.header("3. When During the Day Do Crimes Happen Most? *(Contextual Visualization #2)*")

st.markdown(
    f"""
Another way to make the data feel real is to shift from **what** happens to **when** it happens.
The chart below shows how incidents are distributed across the 24 hours of the day in
**{selected_year}**.

If you imagine a typical day in the city, this helps answer questions like:
*Is crime mostly a late-night phenomenon, or is it spread across the whole day?*
"""
)

if "Hour" in filtered.columns:
    hour_data = filtered.dropna(subset=["Hour"]).copy()

    if not hour_data.empty:
        hour_counts = (
            hour_data["Hour"]
            .value_counts()
            .rename_axis("Hour")
            .reset_index(name="Crime Count")
        )

        hour_chart = (
            alt.Chart(hour_counts)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Hour:O",
                    title="Hour of day (0–23)",
                    sort=list(range(24)),
                ),
                y=alt.Y("Crime Count:Q", title="Number of reported crimes"),
                tooltip=[
                    alt.Tooltip("Hour:O", title="Hour of day"),
                    alt.Tooltip("Crime Count:Q", title="Number of crimes"),
                ],
            )
            .properties(
                width=900,
                height=400,
                title=f"Crimes by hour of day in {selected_year}",
            )
        )

        st.altair_chart(hour_chart, use_container_width=True)
    else:
        st.info(f"No hour-of-day information available for {selected_year}.")
else:
    st.info(
        "The 'Hour' column is missing. Make sure it is derived from the 'Date' field during loading."
    )

st.markdown(
    """
This contextual visualization is also created by us using the same underlying dataset.
Instead of looking at categories or yearly totals, it emphasizes the **daily rhythm** of
reported crime.

For a non-expert reader, it makes the idea of crime more concrete: crime is not just a yearly
statistic, but something that ebbs and flows from hour to hour. Peaks in the late evening,
for example, might suggest different kinds of risk than peaks during commuting hours or
the middle of the workday.
"""
)

# =====================================================
# SECTION 4 – DATA SOURCES & CITATIONS
# =====================================================

st.header("4. Data Sources and How to Find Them")

st.markdown(
    """
**Primary crime dataset**

- City of Chicago, open data portal.  
  *Crimes 2001 to Present.*  
  Retrieved via the consolidated entry on Data.gov:  
  https://catalog.data.gov/dataset/crimes-2001-to-present  

  For this public visualization, we work with yearly CSV files
  (`Crimes_2010.csv` ... `Crimes_2020.csv`) that were downloaded from the
  original source and then split by year to keep the app responsive.

**Code and analysis**

- Our Streamlit application and related project files are hosted in our GitHub repository:  
  https://github.com/RohitYadav-edu/RohitYadav-edu.github.io/tree/main/project 

  The contextual visualizations shown above were created by our group using this same
  dataset. The code that produces them lives directly in this `app.py` file and in
  the project repository.
"""
)

st.markdown(
    """
If you are interested in doing your own analysis, the links above give you everything you need:
the original raw data from the city, and the code we used to turn that data into the charts on
this page.
"""
)
