import streamlit as st
import pandas as pd
import altair as alt

# Disable Altair row limit so multi-year data doesn't silently break
alt.data_transformers.disable_max_rows()

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Chicago Crimes – Viz for Experts",
    layout="wide",
)

# -------------------------
# GLOBAL CUSTOM STYLING
# -------------------------
st.markdown(
    """
    <style>
    /* General font + headings */
    body, [data-testid="stAppViewContainer"] {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 0.95rem;
        color: #0f172a;
    }
    h1, h2, h3, h4 {
        font-family: inherit;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0.25rem 0 0.5rem 0;
    }
    p, li {
        font-size: 0.95rem;
        font-weight: 400;
    }
    /* We are not really using the sidebar now, keep it plain */
    [data-testid="stSidebar"] {
        background: #111827;
    }
    /* Glassmorphism metric cards (no white boxes) */
    div[data-testid="stMetric"] {
        background: rgba(15,23,42,0.9);
        padding: 1rem;
        border-radius: 1rem;
        border: 1px solid rgba(148,163,184,0.3);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 0 18px rgba(15,23,42,0.6);
    }
    div[data-testid="stMetric"] > label {
        color: #cbd5f5 !important;
        font-size: 0.8rem !important;
    }
    div[data-testid="stMetric"] > div {
        color: #e5e7eb !important;
        font-weight: 600 !important;
    }
    /* Make top-level layout background dark-slate */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #1e293b, #020617);
    }
    /* Card-like container for filters */
    .filter-card {
        background: rgba(15,23,42,0.95);
        border-radius: 0.75rem;
        padding: 1rem 1.25rem 0.75rem 1.25rem;
        border: 1px solid rgba(148,163,184,0.4);
        box-shadow: 0 0 18px rgba(15,23,42,0.8);
    }
    .filter-section-title {
        font-weight: 600;
        margin-bottom: 0.25rem;
        color: #e5e7eb;
    }
    .filter-section-subtitle {
        font-size: 0.82rem;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }
    /* Tabs styling – underline style like GA/GitHub */
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #94a3b8 !important;
        border-radius: 0 !important;
        border-bottom: 2px solid transparent !important;
        margin-right: 1.2rem !important;
        font-size: 1rem !important;
        padding: 0.5rem 0 !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #e5e7eb !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background: transparent !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
    /* Top filter bar look */
    .filter-top-bar {
        background: linear-gradient(90deg, #0f172a, #1e293b);
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        margin-top: 0.5rem;
        margin-bottom: 1.2rem;
        color: #e5e7eb;
    }
    .filter-top-bar h3, .filter-top-bar p {
        color: #e5e7eb !important;
        margin: 0;
        padding: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Chicago Crimes – Viz for Experts")
st.caption("IS445 • Expert-facing Streamlit dashboard for exploring Chicago crime data")

# -------------------------
# DATA LOADING
# -------------------------

YEAR_TO_FILE = {
    year: f"project/data/Crimes_{year}.csv"
    for year in range(2010, 2021)  # 2010–2020 inclusive on HuggingFace
}

@st.cache_data
def load_year_data(year: int) -> pd.DataFrame:
    """Load data for a single year's crime file."""
    path = YEAR_TO_FILE[year]
    df = pd.read_csv(path)
    return df

@st.cache_data
def load_multi_year_data(years: list[int]) -> pd.DataFrame:
    """Load and concatenate multiple years and derive extra columns."""
    frames = [load_year_data(y) for y in years]
    df = pd.concat(frames, ignore_index=True)

    # Parse dates and derive temporal features
    if "Date" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month
        df["YearMonth"] = df["Date"].dt.to_period("M").dt.to_timestamp()
        df["Weekday"] = df["Date"].dt.day_name()
        df["Hour"] = df["Date"].dt.hour
    else:
        if "Year" in df.columns:
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # Normalize some columns as string
    for col in ["District", "Ward", "Community Area", "Beat"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Fill some known missing columns gracefully
    for col in ["Arrest", "Domestic"]:
        if col in df.columns:
            df[col] = df[col].fillna(False)

    return df

# -------------------------
# DOCUMENTATION EXPANDER
# -------------------------
with st.expander("Expert Documentation – How to Use This Dashboard?", expanded=True):
    st.markdown("""
    ## Group Members  
    **Rohit Yadav**  
    **Pratyush Agarwal**  
    **Mohak Bansal**
    ---
    ## Chicago Crime Analysis Dashboard – Expert Usage Guide
    This dashboard is built for **expert-level exploration and analysis** of Chicago crime data.  
    It supports multi-year comparisons, district-level operational drill-down, temporal pattern mining, and enforcement evaluation.
    The guide below explains **what each section does**, **how the data flows through the dashboard**, and **how to read insights** generated by the dashboard.
    ---
    ## 1. Global Filters (Top Filter Bar)
    These filters define the exact slice of data that will be visualized across every tab.
    ### **Years**
    - Select any subset from **2010-2020**.
    - Multiple years can be chosen to analyze **trends over time**, or a single year for **focused analysis**.
    ### **Crime Type (Primary Type)**
    - Select one or more crime categories such as:
      - `THEFT`, `BATTERY`, `BURGLARY`, `NARCOTICS`, `ASSAULT`, etc.
    - If nothing is selected, **all types** are included.
    ### **Arrest vs Non-Arrest**
    - Filter to:
      - Only crimes where an **arrest was made**  
      - Only crimes where **no arrest was made**  
      - Or **both** (default).
    - Used to analyze **enforcement patterns** across geography and time.
    ### **Domestic Flag**
    - Filter to:
      - Domestic-related incidents  
      - Non-domestic incidents  
      - Or both (default).
    - Especially useful for **social services coordination**, victim support planning, and **intimate partner violence** studies.
    ### **Geographic Filters (District, Ward, Community Area, Beat)**
    - Choose specific:
      - Police **Districts**
      - Political **Wards**
      - **Community Areas**
      - Police **Beats**
    - Allows **spatial drill-down** and local-level policy evaluation.
    ### **Location Description**
    - Filter crimes by where they occurred:
      - `"STREET"`, `"RESIDENCE"`, `"SIDEWALK"`, `"APARTMENT"`, `"RESTAURANT"`, `"SCHOOL"`, etc.
    - Useful for **environmental criminology** and **place-based interventions**.
    ---
    ## 2. Overview Tab – High-Level Story of Crime
    The Overview tab focuses on understanding **"What is happening overall?"**
    ### **Top Metrics (KPIs)**
    Key indicators presented:
    - **Total Incidents** in the filtered data
    - **Arrest Rate** (% of incidents leading to arrest)
    - **Domestic Incident Share** (%) of crimes flagged as domestic
    - **Time Span** of the filter (min and max dates)
    **Usage:**
    - These metrics give an immediate sense of:
      - Crime intensity  
      - Enforcement levels  
      - Social context (domestic vs non-domestic)  
      - Temporal coverage of the data slice
    ---
    ### **Driver Plot – Top Crime Types**
    - Bar chart showing the **top N crime categories** by frequency.
    - Users can click one or more crime types to drive downstream plots.
    - This selection drives the two charts below.
    **What experts use it for:**
    - Identify top crimes in your filtered period.
    - Control which categories drive all deeper insights.
    ---
    ### **Driven Plot 1 – Crimes by District**
    Updates instantly when:
    - Filters are changed, or  
    - Crime types are selected in the driver plot  
    Helps experts see:
    - Which districts experience higher or lower levels of the selected crime types
    - District-level operational hotspots
    - Disparities across geography
    ---
    ### **Driven Plot 2 – Monthly Trend**
    A time series showing crime counts per month (YearMonth) for:
    - The selected crime types
    - The selected global filters
    Enables:
    - Trend analysis over time
    - Detection of:
      - Seasonal patterns  
      - Long-term increases/decreases  
      - Policy impact points (e.g., new regulations, policing changes)
    Together, these overview plots answer:
    - **What types of crime dominate the selected slice?**
    - **Where are they concentrated geographically?**
    - **How are they evolving over time?**
    ---
    ## 3. Crime Type Deep Dive Tab
    This tab is focused on **crime type composition and co-occurrence**.
    ### **Distribution by Crime Type**
    - A bar chart or share plot showing how often each crime category appears.
    Use cases:
    - Compare crime composition across:
      - Years  
      - Districts  
      - Domestic vs non-domestic incidents  
      - Arrest vs non-arrest cases
    ---
    ### **Crime Type vs Location**
    - A grouped view (e.g., stacked or clustered bars) showing:
      - How different crime types are distributed across **Location Descriptions**
    Helps with:
    - Understanding where certain crime types are more prevalent:
      - `THEFT` → retail/commercial areas  
      - `BATTERY` → residences or public gathering spots  
      - `NARCOTICS` → specific districts or street segments
    ---
    ## 4. Spatial Analysis (Geographic Drill-Down)
    A scatterplot map using Latitude/Longitude (sampled for performance).
    Displays:
    - Exact location of incidents  
    - Crime type (color-coded)  
    - Tooltip: crime type, location, district, date  
    Enables:
    - Micro-hotspot detection  
    - Spatial clustering analysis  
    - Transit-line crime patterns  
    - Environmental context insights  
    Especially powerful when combined with **Location Description** or **District** filters.
    ---
    ## 5. Temporal & Arrest Patterns
    Three charts help experts understand crime timing and enforcement.
    ### **Incidents by Hour of Day**
    Shows operational rhythms:
    - Late-night spikes  
    - Rush-hour transit crime  
    - Business-hour patterns  
    Helps in:
    - Patrol scheduling  
    - Predictive operational planning  
    ### **Incidents by Day of Week**
    Shows weekly cycles:
    - Weekend vs weekday crime  
    - Special attention to nightlife-heavy days  
    ### **Arrest Rate by Crime Type or Geography**
    - Compares arrest likelihood across:
      - Crime types  
      - Districts  
      - Domestic vs non-domestic incidents  
    Helps answer:
    - Are certain crimes or areas **under-policed or over-policed**?
    - Where are enforcement gaps?
    ---
    ## 6. Data Quality & Sampling Considerations
    Because the full Chicago crime dataset is very large:
    - Some views (especially maps) may use **sampling** for performance.
    - Filters may significantly change the number of rows.
    Experts should:
    - Always refer to **Total Incidents** KPI
    - Be cautious about making fine-grained conclusions at extremely small sample sizes
    ---
    ## 7. Example Expert Workflows
    ### **A. Patrol Optimization in a Specific District**
    1. Filter to:
       - Years: `2018-2020`
       - District: `10`
       - Crime Type: `THEFT`, `BATTERY`, `ASSAULT`
    2. Use **Overview** tab:
       - Identify trends in monthly incidents
       - Compare exposure across beats or districts
    3. Check **Temporal Patterns**:
       - Peak hours and days  
       - Design patrol routes and staffing
    ### **B. Domestic Violence Trend Analysis**
    1. Set:
       - Domestic = `Yes`
       - Crime Types: `BATTERY`, `ASSAULT`
    2. Use:
       - Time series to check trend curves
       - Geography to identify high-risk communities
    3. Combine:
       - Arrest rate analysis to evaluate enforcement follow-through.
    ### **C. Policy Impact Study**
    Suppose a new policing or social policy was introduced mid-2015.
    - Filter: years `2012-2018`
    - Compare:
      - Pre-policy trend (2012-2014)
      - Interim (2015-2016)
      - Post-policy (2017-2018)
    - Use the monthly series and crime-type breakdowns.
    ---
    ## 8. Technical Notes for Data Scientists
    - Date column is parsed to extract:
      - Year, Month, YearMonth
      - Weekday, Hour
    - District, Ward, Community Area, Beat are standardized to string type.
    - The dashboard uses:
      - **Altair** for charting (interactive, Vega-Lite)
      - **Streamlit** for UI, caching, and layout
    - Heavy operations (multi-year load) are cached with `@st.cache_data` for better performance.
    ---
    ## 9. Key Takeaways
    - The dashboard is built for:
      - **Exploratory analysis**
      - **Operational insights**
      - **Policy evaluation**
    - It supports:
      - Deep filtering
      - Multi-dimensional slicing (time, space, crime type, enforcement)
      - Interactive selection-driven visualizations
    Use it as a **workbench** to:
    - Form hypotheses quickly
    - Validate or falsify intuitive explanations
    - Communicate findings with clear visual evidence.
    """)

# -------------------------
# FILTER BAR
# -------------------------

st.markdown(
    '<div class="filter-top-bar"><h3>Global Filters</h3>'
    '<p>Set the slice of the Chicago crime dataset that all tabs will analyze.</p></div>',
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    col_year, col_primary, col_geo1, col_geo2 = st.columns([1.2, 1.6, 2, 2])

    with col_year:
        st.markdown('<div class="filter-section-title">Years</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="filter-section-subtitle">Select one year at a time (HF constraint).</div>',
            unsafe_allow_html=True,
        )
        year_options = list(YEAR_TO_FILE.keys())
        selected_year = st.selectbox("Year (single-year view)", options=year_options, index=len(year_options)-1)

    with col_primary:
        st.markdown('<div class="filter-section-title">Crime Types</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="filter-section-subtitle">Select none to include all crime categories.</div>',
            unsafe_allow_html=True,
        )
        # We'll populate the primary types after loading the data (below).
        # For now, placeholder; actual options built from data.
        primary_types_placeholder = st.empty()

    with col_geo1:
        st.markdown('<div class="filter-section-title">Geography – Part 1</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="filter-section-subtitle">District and Ward level filters.</div>',
            unsafe_allow_html=True,
        )
        district_placeholder = st.empty()
        ward_placeholder = st.empty()

    with col_geo2:
        st.markdown('<div class="filter-section-title">Geography – Part 2</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="filter-section-subtitle">Community Areas and Beats.</div>',
            unsafe_allow_html=True,
        )
        community_placeholder = st.empty()
        beat_placeholder = st.empty()

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# LOAD DATA FOR SELECTED YEAR (HF limitation → single year)
# -------------------------

# NOTE:
# Earlier versions of this app allowed multi-year selection directly.
# However, on HuggingFace Spaces with limited memory, loading multiple
# large CSVs simultaneously caused:
# - heavy browser lag
# - slow re-renders
# - occasional app restarts
#
# So for the actual app logic we now always pass a **single-element list**:
selected_years = [selected_year]

# Load data for selected years
# Commenting this to add a new addition about bufferring. Since the data is large and sometimes it can take longer to render.
# data = load_multi_year_data(selected_years)

with st.spinner("Thank you for your patience! Loading and processing the requested data..."):
    data = load_multi_year_data(selected_years)

if "Primary Type" in data.columns:
    primary_types = sorted(
        data["Primary Type"].dropna().astype(str).unique().tolist()
    )
else:
    primary_types = []

if "District" in data.columns:
    district_vals = sorted(data["District"].dropna().astype(str).unique().tolist())
else:
    district_vals = []

if "Ward" in data.columns:
    ward_vals = sorted(data["Ward"].dropna().astype(str).unique().tolist())
else:
    ward_vals = []

if "Community Area" in data.columns:
    community_vals = sorted(data["Community Area"].dropna().astype(str).unique().tolist())
else:
    community_vals = []

if "Beat" in data.columns:
    beat_vals = sorted(data["Beat"].dropna().astype(str).unique().tolist())
else:
    beat_vals = []

with col_primary:
    selected_primary_types = primary_types_placeholder.multiselect(
        "Primary Crime Types",
        options=primary_types,
        default=[],
    )

with col_geo1:
    selected_districts = district_placeholder.multiselect(
        "Police Districts",
        options=district_vals,
        default=[],
    )
    selected_wards = ward_placeholder.multiselect(
        "Wards",
        options=ward_vals,
        default=[],
    )

with col_geo2:
    selected_community = community_placeholder.multiselect(
        "Community Areas",
        options=community_vals,
        default=[],
    )
    selected_beats = beat_placeholder.multiselect(
        "Beats",
        options=beat_vals,
        default=[],
    )

# Additional filter controls below the main bar
with st.container():
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    col_loc, col_arrest, col_domestic = st.columns([2, 1, 1])

    with col_loc:
        st.markdown('<div class="filter-section-title">Location Description</div>', unsafe_allow_html=True)
        loc_options = (
            sorted(data["Location Description"].dropna().astype(str).unique().tolist())
            if "Location Description" in data.columns
            else []
        )
        selected_locations = st.multiselect(
            "Where did the incident occur?",
            options=loc_options,
            default=[],
        )

    with col_arrest:
        st.markdown('<div class="filter-section-title">Arrest Filter</div>', unsafe_allow_html=True)
        arrest_filter = st.selectbox(
            "Arrest status",
            options=["All", "Only Arrests", "Only Non-Arrests"],
            index=0,
        )

    with col_domestic:
        st.markdown('<div class="filter-section-title">Domestic Filter</div>', unsafe_allow_html=True)
        domestic_filter = st.selectbox(
            "Domestic incidents",
            options=["All", "Domestic Only", "Non-Domestic Only"],
            index=0,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# APPLY FILTERS
# -------------------------
filtered = data.copy()

if selected_primary_types:
    filtered = filtered[filtered["Primary Type"].isin(selected_primary_types)]

if selected_districts:
    filtered = filtered[filtered["District"].isin(selected_districts)]

if selected_wards:
    filtered = filtered[filtered["Ward"].isin(selected_wards)]

if selected_community:
    filtered = filtered[filtered["Community Area"].isin(selected_community)]

if selected_beats:
    filtered = filtered[filtered["Beat"].isin(selected_beats)]

if selected_locations:
    filtered = filtered[filtered["Location Description"].isin(selected_locations)]

if arrest_filter == "Only Arrests":
    if "Arrest" in filtered.columns:
        filtered = filtered[filtered["Arrest"] == True]
elif arrest_filter == "Only Non-Arrests":
    if "Arrest" in filtered.columns:
        filtered = filtered[filtered["Arrest"] == False]

if domestic_filter == "Domestic Only":
    if "Domestic" in filtered.columns:
        filtered = filtered[filtered["Domestic"] == True]
elif domestic_filter == "Non-Domestic Only":
    if "Domestic" in filtered.columns:
        filtered = filtered[filtered["Domestic"] == False]

# -------------------------
# METRICS (TOP KPIs)
# -------------------------
st.markdown("### Key Metrics for Current Filter")

metric_cols = st.columns(4)
c1, c2, c3, c4 = metric_cols

total_crimes = len(filtered)

if "Arrest" in filtered.columns and total_crimes > 0:
    arrest_rate = 100 * filtered["Arrest"].mean()
else:
    arrest_rate = None

if "Domestic" in filtered.columns and total_crimes > 0:
    domestic_share = 100 * filtered["Domestic"].mean()
else:
    domestic_share = None

if "Date" in filtered.columns and not filtered["Date"].isna().all():
    first_date = filtered["Date"].min()
    last_date = filtered["Date"].max()
else:
    first_date = last_date = None

c1.metric("Total Incidents", f"{total_crimes:,}")

if arrest_rate is not None:
    c2.metric("Arrest Rate", f"{arrest_rate:.1f}%")
else:
    c2.metric("Arrest Rate", "N/A")

if domestic_share is not None:
    c3.metric("Domestic Incident Share", f"{domestic_share:.1f}%")
else:
    c3.metric("Domestic Incident Share", "N/A")

if first_date is not None and last_date is not None:
    c4.metric("Time Span", f"{first_date.date()} → {last_date.date()}")
else:
    c4.metric("Time Span", "N/A")

# -------------------------
# TABS
# -------------------------
tab_overview, tab_types, tab_temporal, tab_spatial, tab_raw = st.tabs(
    ["Overview", "Crime Types", "Temporal Patterns", "Spatial / Location", "Raw Data"]
)

# -------------------------
# OVERVIEW TAB
# -------------------------
with tab_overview:
    st.markdown("#### Overview – Top Crime Types, Districts & Monthly Trend")

    if filtered.empty:
        st.warning("No data available for the selected filters.")
    else:
        top_n = 15
        crime_by_type = (
            filtered.groupby("Primary Type")
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
            .head(top_n)
        )

        if not crime_by_type.empty:
            selector = alt.selection_multi(fields=["Primary Type"], bind="legend")
            base = alt.Chart(crime_by_type).encode(
                x=alt.X("Count:Q", title="Number of Incidents"),
                y=alt.Y("Primary Type:N", sort="-x", title="Crime Type"),
                color=alt.Color("Primary Type:N", legend=None),
                tooltip=[
                    alt.Tooltip("Primary Type:N", title="Crime Type"),
                    alt.Tooltip("Count:Q", title="Incidents", format=","),
                ],
            )
            bar = base.mark_bar().add_selection(selector)
            st.altair_chart(bar.properties(height=400), use_container_width=True)
        else:
            st.info("No crimes found to show by type.")

        col_left, col_right = st.columns(2)

        with col_left:
            if "District" in filtered.columns and not filtered["District"].isna().all():
                dist_counts = (
                    filtered.groupby("District")
                    .size()
                    .reset_index(name="Count")
                    .sort_values("Count", ascending=False)
                )
                dist_chart = (
                    alt.Chart(dist_counts)
                    .mark_bar()
                    .encode(
                        x=alt.X("District:N", title="Police District"),
                        y=alt.Y("Count:Q", title="Incidents"),
                        tooltip=[
                            alt.Tooltip("District:N", title="District"),
                            alt.Tooltip("Count:Q", title="Incidents", format=","),
                        ],
                    )
                )
                st.markdown("**Incidents by Police District**")
                st.altair_chart(dist_chart.properties(height=350), use_container_width=True)
            else:
                st.info("District data not available in this dataset slice.")

        with col_right:
            if "YearMonth" in filtered.columns and not filtered["YearMonth"].isna().all():
                ym_counts = (
                    filtered.groupby("YearMonth")
                    .size()
                    .reset_index(name="Count")
                    .sort_values("YearMonth")
                )
                line_chart = (
                    alt.Chart(ym_counts)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("YearMonth:T", title="Month"),
                        y=alt.Y("Count:Q", title="Incidents"),
                        tooltip=[
                            alt.Tooltip("YearMonth:T", title="Month"),
                            alt.Tooltip("Count:Q", title="Incidents", format=","),
                        ],
                    )
                )
                st.markdown("**Monthly Trend of Incidents**")
                st.altair_chart(line_chart.properties(height=350), use_container_width=True)
            else:
                st.info("Cannot build a monthly trend because 'Date' or 'YearMonth' is missing.")

# -------------------------
# CRIME TYPE TAB
# -------------------------
with tab_types:
    st.markdown("#### Crime Type Composition & Location Context")

    if filtered.empty:
        st.warning("No data available for the selected filters.")
    else:
        type_counts = (
            filtered.groupby("Primary Type")
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
        )

        col_bar, col_share = st.columns(2)

        with col_bar:
            if not type_counts.empty:
                chart = (
                    alt.Chart(type_counts.head(25))
                    .mark_bar()
                    .encode(
                        x=alt.X("Count:Q", title="Incidents"),
                        y=alt.Y("Primary Type:N", sort="-x", title="Crime Type"),
                        tooltip=[
                            alt.Tooltip("Primary Type:N", title="Crime Type"),
                            alt.Tooltip("Count:Q", title="Incidents", format=","),
                        ],
                        color=alt.Color("Primary Type:N", legend=None),
                    )
                )
                st.markdown("**Top Crime Types by Count**")
                st.altair_chart(chart.properties(height=450), use_container_width=True)
            else:
                st.info("No crime type counts to display.")

        with col_share:
            type_counts["Share"] = type_counts["Count"] / type_counts["Count"].sum()
            share_chart = (
                alt.Chart(type_counts.head(15))
                .mark_bar()
                .encode(
                    x=alt.X("Share:Q", title="Share of Incidents", axis=alt.Axis(format="%")),
                    y=alt.Y("Primary Type:N", sort="-x", title="Crime Type"),
                    tooltip=[
                        alt.Tooltip("Primary Type:N", title="Crime Type"),
                        alt.Tooltip("Share:Q", title="Share", format=".1%"),
                        alt.Tooltip("Count:Q", title="Incidents", format=","),
                    ],
                    color=alt.Color("Primary Type:N", legend=None),
                )
            )
            st.markdown("**Relative Share of Top Crime Types**")
            st.altair_chart(share_chart.properties(height=450), use_container_width=True)

        st.markdown("---")

        if "Location Description" in filtered.columns:
            cross = (
                filtered.groupby(["Primary Type", "Location Description"])
                .size()
                .reset_index(name="Count")
            )
            if not cross.empty:
                cross_chart = (
                    alt.Chart(cross)
                    .mark_bar()
                    .encode(
                        x=alt.X("Count:Q", title="Incidents"),
                        y=alt.Y("Primary Type:N", sort="-x", title="Crime Type"),
                        color=alt.Color("Location Description:N", title="Location"),
                        tooltip=[
                            alt.Tooltip("Primary Type:N", title="Crime Type"),
                            alt.Tooltip("Location Description:N", title="Location"),
                            alt.Tooltip("Count:Q", title="Incidents", format=","),
                        ],
                    )
                    .interactive()
                )
                st.markdown("**Crime Type by Location Description**")
                st.altair_chart(cross_chart.properties(height=450), use_container_width=True)
            else:
                st.info("No cross-tab between crime type and location to show.")
        else:
            st.info("Location Description column not available.")

# -------------------------
# TEMPORAL PATTERNS TAB
# -------------------------
with tab_temporal:
    st.markdown("#### Temporal Patterns – Hour of Day, Day of Week, and Monthly Trends")

    if filtered.empty:
        st.warning("No data available for the selected filters.")
    else:
        col_hour, col_day = st.columns(2)

        with col_hour:
            if "Hour" in filtered.columns:
                hour_counts = (
                    filtered.groupby("Hour")
                    .size()
                    .reset_index(name="Count")
                    .sort_values("Hour")
                )
                if not hour_counts.empty:
                    hour_chart = (
                        alt.Chart(hour_counts)
                        .mark_bar()
                        .encode(
                            x=alt.X("Hour:O", title="Hour of Day (0–23)"),
                            y=alt.Y("Count:Q", title="Incidents"),
                            tooltip=[
                                alt.Tooltip("Hour:O", title="Hour"),
                                alt.Tooltip("Count:Q", title="Incidents", format=","),
                            ],
                        )
                    )
                    st.markdown("**Incidents by Hour of Day**")
                    st.altair_chart(hour_chart.properties(height=350), use_container_width=True)
                else:
                    st.info("No incidents with valid hour information.")
            else:
                st.info("Hour information not available.")

        with col_day:
            if "Weekday" in filtered.columns:
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                day_counts = (
                    filtered.groupby("Weekday")
                    .size()
                    .reindex(day_order, fill_value=0)
                    .reset_index(name="Count")
                    .rename(columns={"index": "Weekday"})
                )
                day_chart = (
                    alt.Chart(day_counts)
                    .mark_bar()
                    .encode(
                        x=alt.X("Weekday:N", title="Day of Week", sort=day_order),
                        y=alt.Y("Count:Q", title="Incidents"),
                        tooltip=[
                            alt.Tooltip("Weekday:N", title="Day"),
                            alt.Tooltip("Count:Q", title="Incidents", format=","),
                        ],
                    )
                )
                st.markdown("**Incidents by Day of Week**")
                st.altair_chart(day_chart.properties(height=350), use_container_width=True)
            else:
                st.info("Weekday information not available.")

        st.markdown("---")

        if "YearMonth" in filtered.columns:
            ym_counts = (
                filtered.groupby("YearMonth")
                .size()
                .reset_index(name="Count")
                .sort_values("YearMonth")
            )
            if not ym_counts.empty:
                line_chart = (
                    alt.Chart(ym_counts)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("YearMonth:T", title="Month"),
                        y=alt.Y("Count:Q", title="Incidents"),
                        tooltip=[
                            alt.Tooltip("YearMonth:T", title="Month"),
                            alt.Tooltip("Count:Q", title="Incidents", format=","),
                        ],
                    )
                )
                st.markdown("**Monthly Trend (Filtered Slice)**")
                st.altair_chart(line_chart.properties(height=350), use_container_width=True)
            else:
                st.info("No monthly data points after filtering.")
        else:
            st.info("No YearMonth information available.")

# -------------------------
# SPATIAL / LOCATION TAB
# -------------------------
with tab_spatial:
    st.markdown("#### Spatial & Location-Based Patterns")

    if filtered.empty:
        st.warning("No data available for the selected filters.")
    else:
        if {"Latitude", "Longitude"}.issubset(filtered.columns):
            subset = filtered.dropna(subset=["Latitude", "Longitude"])
            if len(subset) > 3000:
                subset = subset.sample(3000, random_state=42)

            if not subset.empty:
                base = alt.Chart(subset).encode(
                    x=alt.X("Longitude:Q", title="Longitude"),
                    y=alt.Y("Latitude:Q", title="Latitude"),
                    tooltip=[
                        alt.Tooltip("Primary Type:N", title="Crime Type"),
                        alt.Tooltip("Location Description:N", title="Location"),
                        alt.Tooltip("District:N", title="District"),
                        alt.Tooltip("Date:T", title="Date"),
                    ],
                )
                points = base.mark_circle(size=10, opacity=0.4).encode(
                    color=alt.Color("Primary Type:N", title="Crime Type", legend=None)
                )
                st.markdown("**Geospatial Scatter of Incidents (Sampled if Large)**")
                st.altair_chart(points.properties(height=500), use_container_width=True)
            else:
                st.info("No valid latitude/longitude records in the filtered data.")
        else:
            st.info("Latitude/Longitude columns not present; spatial plotting not available.")

        if "Location Description" in filtered.columns:
            loc_counts = (
                filtered.groupby("Location Description")
                .size()
                .reset_index(name="Count")
                .sort_values("Count", ascending=False)
                .head(20)
            )
            loc_chart = (
                alt.Chart(loc_counts)
                .mark_bar()
                .encode(
                    x=alt.X("Count:Q", title="Incidents"),
                    y=alt.Y("Location Description:N", sort="-x", title="Location Description"),
                    tooltip=[
                        alt.Tooltip("Location Description:N", title="Location"),
                        alt.Tooltip("Count:Q", title="Incidents", format=","),
                    ],
                    color=alt.Color("Location Description:N", legend=None),
                )
            )
            st.markdown("**Top Locations by Incident Count**")
            st.altair_chart(loc_chart.properties(height=450), use_container_width=True)
        else:
            st.info("Location Description column not found in the dataset.")

# -------------------------
# RAW DATA TAB
# -------------------------
with tab_raw:
    st.markdown("#### Raw Data View")

    st.write(
        "This table shows the filtered records. Use it for validation, quick lookups, "
        "or to export data slices for offline analysis."
    )

    st.dataframe(filtered, use_container_width=True, height=500)

    st.markdown("**Note:** For very large slices, you may want to apply more filters to keep this table responsive.")

# -------------------------
# COMMENTED-OUT / HISTORICAL CODE (KEPT FOR DOCUMENTATION)
# -------------------------
# The code below documents experimental or alternative approaches we tried earlier in the project.
# It is intentionally preserved but not executed.

# Example of the earlier multi-year checkbox UI (commented out):
# with st.sidebar:
#     st.write("Early Prototype Filters (Sidebar) – Now Deprecated")
#     multi_years = st.multiselect("Pick multiple years", year_options, default=year_options[-3:])
#     st.write("This approach allowed multi-year loading but caused performance issues on HF Spaces.")

# Example of older tab styling code (commented, replaced by new design above):
#  /* Tabs styling */
#  button[data-baseweb="tab"] {
#      font-weight: 600 !important;
#      color: #4b5563 !important;
#      background-color: #e5e7eb !important;
#      border-radius: 999px !important;
#      margin-right: 0.5rem !important;
#      border: none !important;
#  }
#  button[data-baseweb="tab"][aria-selected="true"] {
#      color: #f9fafb !important;
#      background: linear-gradient(90deg, #38bdf8, #6366f1) !important;
#  }
# New Design
# /* Tabs styling – underline style like GA/GitHub */
# button[data-baseweb="tab"] {
#     background: transparent !important;
#     color: #94a3b8 !important;
#     border-radius: 0 !important;
#     border-bottom: 2px solid transparent !important;
#     margin-right: 1.2rem !important;
#     font-size: 1rem !important;
#     padding: 0.5rem 0 !important;
# }
# button[data-baseweb="tab"]:hover {
#     color: #e5e7eb !important;
# }
# button[data-baseweb="tab"][aria-selected="true"] {
#     color: #ffffff !important;
#     background: transparent !important;
#     border-bottom: 2px solid #38bdf8 !important;
# }

# Below is an internal project note describing the data-loading architecture change
# from multi-year dynamic loading to a single-year constrained view for HF Spaces.
# We keep it here as part of technical documentation.

st.markdown("""
---
### Appendix – Data Loading Design History (For Instructors / Reviewers)

Over the course of this project, we iterated through multiple data-loading strategies.
This section explains why the **final app** uses **single-year CSV files** instead of
the Chicago Open Data API or multi-year simultaneous loads.

#### **1. Initial Approach – Multi-Year Local CSVs**
We started by:
- Downloading a large multi-year CSV extract
- Loading it entirely into memory
- Allowing users to filter across **2010–2023** at once

**Issues:**
- On local machines, performance was acceptable.
- On HuggingFace Spaces (with limited RAM/CPU), this caused:
  - timeouts when reloading data
  - sluggish UI interaction
  - occasional app restarts

#### **2. Optimized Multi-Year Loading with Caching**
We refactored loading into:
- `load_year_data(year)`: loads one CSV per year
- `load_multi_year_data(years)`: concatenates per-year data on demand
- Added `@st.cache_data` so repeated requests for the same years reuse cached data

This allowed us to:
- Load only requested years
- Avoid repeating expensive disk reads
- Keep the code modular and testable

However, on HF Spaces, selecting many years at once **still** occasionally pushed
memory limits, especially when combined with heavy Altair interactivity.

#### **3. Multi-Year + Heavy Interactivity (Abandoned)**
We experimented with:
- Linked selections (Altair `selection_multi`, brushing)
- Large geospatial plots with thousands of points
- Multiple complex charts in the same view

Even after careful sampling and simplification, we encountered:
- heavy browser lag  
- HF Spaces freezing and restarting  
- interaction glitches  
- large memory spikes

To maintain usability, we restricted the dashboard to **one year at a time**.

#### **4. Buffered Loading UX**
We added loading spinners such as:
- *“Thank you for your patience! Loading data…”*
- *“Filtering data…”*

This improved the user experience but still depended on uploading CSVs manually.

#### **5. Attempted Migration to the Chicago Open Data API**
We attempted to fully replace uploaded CSVs by loading data directly from the official SODA API:
- Pros:
  - Always-current data
  - No need to upload CSVs manually
- Cons (in this environment):
  - HF Spaces sometimes throttles outbound API calls
  - Long cold-start times on initial API queries
  - Harder to guarantee reproducibility for grading/demonstration

#### **6. Final Architecture – Hosted Per-Year CSVs**
Given the constraints, we settled on:
- Hosting **2010–2020 per-year CSVs** within the project
- Restricting the user to **one selected year at a time**
- Applying rich filters and visualizations **within that year**
- Keeping `load_multi_year_data` general for future extension beyond HF Spaces

This hybrid approach:
- Keeps the UX responsive
- Avoids API quotas/throttling issues
- Still allows rich spatial, temporal, and categorical analysis
- Is easy to reason about and reproduce

The commented sections in the code — especially around multi-year selection,
early CSS prototypes, and prior data-loading strategies — are intentionally preserved.  
They document the evolution of the project, the reasoning behind the final technical decisions, and
the efforts invested in exploring multiple architectural paths.

### **7. Final Decision**
The current implementation balances:
- performance  
- usability  
- reliability  
- reproducibility  

under the constraints of HuggingFace Spaces.  
Although the API-based architecture would be ideal in a scalable cloud environment, the hosted CSV
solution provides the most consistent behavior for deployment on limited compute resources.
""")
