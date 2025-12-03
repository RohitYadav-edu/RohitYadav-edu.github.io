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
    h1, h2, h3, h4 {
        color: #0f172a;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
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
    # Early stage design (We have commented it because we have replaced and implemented a new design)
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
            df[col] = df[col].astype("string")

    # Normalize Arrest/Domestic flags
    for flag_col in ["Arrest", "Domestic"]:
        if flag_col in df.columns:
            df[flag_col] = (
                df[flag_col]
                .astype(str)
                .str.strip()
                .str.upper()
                .isin(["TRUE", "T", "1", "YES", "Y"])
            )

    return df

# -------------------------
# REQUIRED WRITE-UP
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
    It supports multi-year comparisons, district-level operational insights, spatial drill-down, temporal pattern mining, and enforcement evaluation.
    The guide below explains **what each section does**, **how each filter works**, and **how to read insights** generated by the dashboard.
    ---
    ## 1. Global Filters (Top Filter Bar)
    These filters define the exact slice of data that will be visualized across every tab.
    ### **Years**
    - Select any subset from **2010-2020**.
    - Works for:
      - Pre/post policy comparison
      - Year-over-year crime pattern analysis
      - Multi-year trend evaluation
    ### **Primary Crime Types**
    - Select crime categories like THEFT, ASSAULT, NARCOTICS, ROBBERY, etc.
    - Used to focus the dashboard on:
      - Violent crime  
      - Property crime  
      - Transit-related crime  
      - Drug-related offenses  
    ### **Police Districts**
    - Filter data to one or more police operational districts.
    - Supports:
      - District-level resource planning
      - Operational hotspot comparison
      - District performance evaluation
    ### **Location Description**
    - Filter for specific environments such as:
      - RESIDENCE  
      - STREET  
      - PARKING LOT  
      - CTA TRAIN / BUS  
      - ALLEY  
    - Enables environmental pattern analysis.
    ### After using these filters:
    Every chart in every tab updates to show **only** the selected years, types, districts, and locations.
    ---
    ## 2. Summary Metrics
    Four high-level metrics summarize the filtered dataset:
    ### **Total Incidents**  
    Total number of crimes matching your filters.
    ### **Arrest Rate**  
    Percentage of selected incidents that resulted in an arrest.
    ### **Domestic Share**  
    Percentage of incidents marked as domestic-related.
    ### **Time Span**  
    Actual temporal coverage of the filtered data using Year-Month, not just the year labels.
    These immediately tell experts:
    - How big the selected problem space is  
    - Whether the filtered slice has high/low enforcement  
    - How domestic violence is represented  
    - Whether the time period is continuous or fragmented  
    ---
    ## 3. Crime Overview (Driver + Driven Plots)
    This is the **core analytical dashboard**.
    ### **Driver Plot – Crime Counts by Primary Type**
    - Click a crime type to activate cross-filtering.
    - Ctrl/Cmd-click to choose multiple crime types.
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
    Shows the **time evolution** of the selected crime types.
    Experts can see:
    - Seasonal patterns  
    - Month-over-month changes  
    - Crime acceleration or decline  
    - Effects of city policies or events  
    **Together**, the three plots give an expert:
    - What types of crime dominate  
    - Where they occur  
    - How they behave over time  
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
    - Weekend vs weekday differences  
    - Consistent operational trends  
    ### **Arrest Rate by Primary Type**
    Shows which crime types have:
    - High arrest success  
    - Low enforcement outcomes  
    - Potential operational gaps  
    ---
    ## 6. What Experts Can Conclude from the Results
    Once filters + driver selections are applied, the dashboard provides:
    ### **Crime Composition**
    - Which crime categories dominate the selected slice
    ### **Geographic Concentration**
    - Which districts account for most incidents  
    - Potential deployment imbalances  
    ### **Temporal Dynamics**
    - Peak hours  
    - Weekly cycles  
    - Seasonal or monthly trends  
    ### **Space-Based Clustering**
    - Where micro-hotspots occur  
    - Location-specific risk patterns  
    ### **Enforcement Effectiveness**
    - Arrest rates by crime type  
    - Crimes with consistently low arrest rates  
    ### **Policy & Operational Insights**
    - Whether trends align with policy changes  
    - Which districts need targeted attention  
    - How crime types shift over time or location  
    This dashboard enables experts to move from:
    **broad → focused → geographic → temporal → operational insights**  
    using a clean, reproducible workflow suitable for urban planning, criminology, and policy analytics.
    """)


# -------------------------
# TOP FILTER BAR (REAL TOP PANEL)
# -------------------------

st.markdown(
    """
    <div class="filter-top-bar">
        <h3>Filters</h3>
        <p>Adjust the parameters below to refine the dataset for analysis.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    # Row 1: Years / Primary Types
    f1, f2 = st.columns([1, 2])

    available_years = sorted(list(YEAR_TO_FILE.keys()))

    with f1:
        # ---- CURRENT IMPLEMENTATION: single year selection ----
        selected_year = st.selectbox(
            "Year (single selection – one year at a time for stability)",
            options=available_years,
            index=len(available_years) - 1,  # default = latest year
        )
        st.caption(
            "Note: For performance and clarity, the dashboard is restricted to **one year at a time**. "
            "Selecting a different year will replace the current selection."
        )

        # ---- PREVIOUS ATTEMPTS (kept commented to show work) ----
        # Multi-year selection using multiselect (did not work well with our large data)
        # selected_years = st.multiselect(
        #     "Years",
        #     options=available_years,
        #     default=[max(available_years)],
        # )
        #
        # if not selected_years:
        #     st.warning("Please select at least one year.")
        #     st.stop()
        #
        # Slider-based year range (early experiment, kept for reference)
        # year_start, year_end = st.slider(
        #     "Year range",
        #     min_value=min(available_years),
        #     max_value=max(available_years),
        #     value=(max(available_years), max(available_years)),
        #     step=1,
        #     key="year_slider",
        # )
        # selected_years = list(range(year_start, year_end + 1))

    # For the actual app logic we now always pass a **single-element list**:
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

    with f2:
        # "Select all" behaviour via checkbox
        select_all_primary = st.checkbox("Select all primary crime types", value=True)
        if select_all_primary:
            selected_primary_types = st.multiselect(
                "Primary Crime Types",
                options=primary_types,
                default=primary_types,
            )
        else:
            selected_primary_types = st.multiselect(
                "Primary Crime Types",
                options=primary_types,
                default=primary_types[:10] if len(primary_types) > 10 else primary_types,
            )

    # Row 2: Districts / Location Description
    f3, f4 = st.columns(2)

    if "District" in data.columns:
        # Sort districts in chronological/numeric order but keep them as strings
        district_vals = data["District"].dropna().astype(str).unique().tolist()
        try:
            districts = sorted(district_vals, key=lambda x: int(float(x)))
        except Exception:
            districts = sorted(district_vals)
    else:
        districts = []

    with f3:
        select_all_districts = st.checkbox("Select all police districts", value=True)
        if select_all_districts:
            selected_districts = st.multiselect(
                "Police Districts",
                options=districts,
                default=districts,
            )
        else:
            selected_districts = st.multiselect(
                "Police Districts",
                options=districts,
                default=districts,
            )

    if "Location Description" in data.columns:
        loc_descs = sorted(data["Location Description"].dropna().astype(str).unique().tolist())
    else:
        loc_descs = []

    with f4:
        select_all_locations = st.checkbox("Select all locations", value=False)
        if select_all_locations:
            selected_locations = st.multiselect(
                "Location Description",
                options=loc_descs,
                default=loc_descs,
            )
        else:
            selected_locations = st.multiselect(
                "Location Description",
                options=loc_descs,
                default=[],
            )

# -------------------------
# APPLY FILTERS
# -------------------------

with st.spinner("Filtering data..."):
    filtered = data.copy()
    
    # Only filter by Primary Type if user has chosen a strict subset
    if selected_primary_types and len(selected_primary_types) < len(primary_types):
        filtered = filtered[filtered["Primary Type"].isin(selected_primary_types)]
    
    # Only filter by District if user has chosen a strict subset
    if selected_districts and len(selected_districts) < len(districts):
        filtered = filtered[filtered["District"].isin(selected_districts)]
    
    if selected_locations:
        filtered = filtered[filtered["Location Description"].isin(selected_locations)]

    # Used this piece of code to debug a plot renderring issue
    # st.write("DEBUG – filtered rows:", len(filtered))
    # if "Primary Type" in filtered.columns:
    #     st.write("DEBUG – unique Primary Types:", filtered["Primary Type"].nunique())
    # if "District" in filtered.columns:
    #     st.write("DEBUG – unique Districts:", filtered["District"].nunique())
    # if "Year" in filtered.columns:
    #     st.write("DEBUG – unique Years:", filtered["Year"].unique().tolist())
    
    if filtered.empty:
        st.error("No data left after applying filters. Try relaxing your selections.")
        st.stop()

# -------------------------
# SUMMARY METRICS
# -------------------------

st.subheader("Summary Metrics (under current filters)")

total_crimes = len(filtered)

if "Arrest" in filtered.columns:
    arrest_rate = filtered["Arrest"].mean() * 100
else:
    arrest_rate = None

if "Domestic" in filtered.columns:
    domestic_share = filtered["Domestic"].mean() * 100
else:
    domestic_share = None

if "YearMonth" in filtered.columns:
    first_date = filtered["YearMonth"].min()
    last_date = filtered["YearMonth"].max()
else:
    first_date = None
    last_date = None

c1, c2, c3, c4 = st.columns(4)

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
# TABS FOR EXPERT VIEWS
# -------------------------

overview_tab, spatial_tab, temporal_tab = st.tabs(
    ["Crime Overview", "Spatial Analysis", "Temporal & Arrest Patterns"]
)

# =====================================================
# TAB 1: CRIME OVERVIEW – DRIVER / DRIVEN
# =====================================================
with overview_tab:
    with st.spinner("Rendering crime overview..."):
        st.markdown("### Driver & Driven Plots – Crime Types, Districts, Time")

        # ---- DRIVER PLOT: Crimes by Primary Type (aggregated) ----
        driver_df = (
            filtered
            .groupby("Primary Type", as_index=False)
            .size()
            .rename(columns={"size": "Crime Count"})
        )

        if driver_df.empty:
            st.warning("No data available for the current filter selection to build the driver plot.")
        else:
            selection = alt.selection_multi(fields=["Primary Type"], empty="all")

            driver_chart = (
                alt.Chart(driver_df)
                .mark_bar()
                .encode(
                    x=alt.X("Primary Type:N", sort="-y", title="Primary Crime Type"),
                    y=alt.Y("Crime Count:Q", title="Number of Crimes"),
                    color=alt.condition(
                        selection,
                        alt.Color("Primary Type:N", legend=None),
                        alt.value("lightgray")
                    ),
                    tooltip=[
                        alt.Tooltip("Primary Type:N", title="Primary Type"),
                        alt.Tooltip("Crime Count:Q", title="Number of Crimes")
                    ]
                )
                .add_selection(selection)
                .properties(
                    width=900,
                    height=300,
                    title="Driver Plot – Crime Counts by Primary Type"
                )
            )

            # ---- DRIVEN PLOT 1: Crimes by District (aggregated) ----
            district_df = (
                filtered
                .groupby(["District", "Primary Type"], as_index=False)
                .size()
                .rename(columns={"size": "Crime Count"})
            )

            district_chart = (
                alt.Chart(district_df)
                .transform_filter(selection)
                .mark_bar()
                .encode(
                    x=alt.X("District:N", title="Police District"),
                    y=alt.Y("Crime Count:Q", title="Number of Crimes"),
                    color=alt.Color("District:N", title="District"),
                    tooltip=[
                        alt.Tooltip("District:N", title="District"),
                        alt.Tooltip("Crime Count:Q", title="Number of Crimes")
                    ]
                )
                .properties(
                    width=900,
                    height=300,
                    title="Driven Plot 1 – Crimes by District (for selected Primary Types)"
                )
            )

            # ---- DRIVEN PLOT 2: Monthly Trend (aggregated) ----
            if "YearMonth" in filtered.columns:
                trend_df = (
                    filtered
                    .groupby(["YearMonth", "Primary Type"], as_index=False)
                    .size()
                    .rename(columns={"size": "Crime Count"})
                )

                trend_chart = (
                    alt.Chart(trend_df)
                    .transform_filter(selection)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("YearMonth:T", title="Year-Month"),
                        y=alt.Y("Crime Count:Q", title="Number of Crimes"),
                        color=alt.Color("Primary Type:N", title="Primary Type"),
                        tooltip=[
                            alt.Tooltip("YearMonth:T", title="Year-Month"),
                            alt.Tooltip("Primary Type:N", title="Primary Type"),
                            alt.Tooltip("Crime Count:Q", title="Number of Crimes")
                        ]
                    )
                    .properties(
                        width=900,
                        height=300,
                        title="Driven Plot 2 – Monthly Trend (for selected Primary Types)"
                    )
                )

                combined_chart = driver_chart & district_chart & trend_chart
                st.altair_chart(combined_chart, use_container_width=True)
            else:
                combined_chart = driver_chart & district_chart
                st.altair_chart(combined_chart, use_container_width=True)
                st.info("No YearMonth information available to show time trends.")

# =====================================================
# TAB 2: SPATIAL ANALYSIS
# =====================================================
with spatial_tab:
    with st.spinner("Rendering spatial analysis..."):
        st.markdown("### Spatial Analysis – Latitude/Longitude (sampled for performance)")

        if {"Latitude", "Longitude"}.issubset(filtered.columns):
            sample_size = min(5000, len(filtered))
            spatial_sample = filtered.dropna(subset=["Latitude", "Longitude"]).sample(
                n=sample_size, random_state=42
            ) if len(filtered) > sample_size else filtered.dropna(subset=["Latitude", "Longitude"])

            if spatial_sample.empty:
                st.warning("No spatial data (Latitude/Longitude) available for current filters.")
            else:
                spatial_chart = (
                    alt.Chart(spatial_sample)
                    .mark_circle(opacity=0.6)
                    .encode(
                        longitude="Longitude:Q",
                        latitude="Latitude:Q",
                        color=alt.Color("Primary Type:N", title="Primary Type"),
                        tooltip=[
                            alt.Tooltip("Primary Type:N", title="Primary Type"),
                            alt.Tooltip("Location Description:N", title="Location"),
                            alt.Tooltip("District:N", title="District"),
                            alt.Tooltip("Date:T", title="Date"),
                        ]
                    )
                    .properties(
                        width=800,
                        height=500
                    )
                )

                st.altair_chart(spatial_chart, use_container_width=True)
                st.caption("Note: points are sampled for performance; use filters in the top bar to narrow down.")
        else:
            st.info("Latitude/Longitude not available in the current data selection.")

# =====================================================
# TAB 3: TEMPORAL & ARREST PATTERNS
# =====================================================
with temporal_tab:
    with st.spinner("Rendering temporal & arrest patterns..."):
        st.markdown("### Temporal & Arrest Patterns")

        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.markdown("#### Incidents by Hour of Day")

            if "Hour" in filtered.columns:
                hour_chart = (
                    alt.Chart(filtered)
                    .mark_bar()
                    .encode(
                        x=alt.X("Hour:O", title="Hour of Day"),
                        y=alt.Y("count():Q", title="Number of Crimes"),
                        tooltip=[
                            alt.Tooltip("Hour:O", title="Hour"),
                            alt.Tooltip("count():Q", title="Number of Crimes")
                        ]
                    )
                    .properties(
                        width=350,
                        height=300
                    )
                )
                st.altair_chart(hour_chart, use_container_width=True)
            else:
                st.info("No hour information available in Date column.")

        with col_t2:
            st.markdown("#### Incidents by Day of Week")

            if "Weekday" in filtered.columns:
                weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                weekday_chart = (
                    alt.Chart(filtered)
                    .mark_bar()
                    .encode(
                        x=alt.X("Weekday:N", sort=weekday_order, title="Day of Week"),
                        y=alt.Y("count():Q", title="Number of Crimes"),
                        tooltip=[
                            alt.Tooltip("Weekday:N", title="Day"),
                            alt.Tooltip("count():Q", title="Number of Crimes")
                        ]
                    )
                    .properties(
                        width=350,
                        height=300
                    )
                )
                st.altair_chart(weekday_chart, use_container_width=True)
            else:
                st.info("No weekday information available.")

        st.markdown("#### Arrest Rate by Primary Type")

        if "Arrest" in filtered.columns and "Primary Type" in filtered.columns:
            arrest_df = (
                filtered
                .groupby("Primary Type", as_index=False)["Arrest"]
                .mean()
                .rename(columns={"Arrest": "Arrest Rate"})
            )

            if arrest_df.empty:
                st.warning("No arrest information available for current filters.")
            else:
                arrest_chart = (
                    alt.Chart(arrest_df)
                    .mark_bar()
                    .encode(
                        x=alt.X("Primary Type:N", sort="-y", title="Primary Crime Type"),
                        y=alt.Y("Arrest Rate:Q", title="Arrest Rate", axis=alt.Axis(format="%")),
                        tooltip=[
                            alt.Tooltip("Primary Type:N", title="Primary Type"),
                            alt.Tooltip("Arrest Rate:Q", title="Arrest Rate", format=".1%")
                        ]
                    )
                    .properties(
                        width=900,
                        height=350
                    )
                )
                st.altair_chart(arrest_chart, use_container_width=True)
        else:
            st.info("Arrest information is not available.")

# -------------------------
# DATA PREVIEW + SOURCE LINKS
# -------------------------

with st.expander("Preview Filtered Data"):
    st.write(f"Showing **{len(filtered):,} rows** after filters.")
    st.dataframe(filtered.head(100))

with st.expander("Data Source Links"):
    st.markdown("""
    - **Main crime dataset (yearly splits, e.g., Crimes_2009.csv … Crimes_2024.csv):**  
      Stored in this repo under `https://github.com/RohitYadav-edu/RohitYadav-edu.github.io/tree/main/project/data`.
    - **Original full crime dataset description:**  
      'https://catalog.data.gov/dataset/crimes-2001-to-present'
    """)

# ------------------------------------------------------------------------------
# IMPLEMENTATION ISSUES & ITERATIONS (PROJECT HISTORY & TECHNICAL DECISIONS)
# ------------------------------------------------------------------------------

st.markdown("---")
st.markdown("## 🛠️ Implementation Issues & Iterations (Project History & Technical Decisions)")

st.markdown("""
This section documents the engineering reasoning, experiments, and constraints that shaped the
final design of this dashboard. The dataset used in this project — the Chicago “Crimes 2001 to Present”
dataset — is extremely large, so multiple approaches were attempted before arriving at the current
stable implementation.

### **1. Full Dataset Size (~2 GB)**
The raw dataset is approximately **2 gigabytes**, far too large to store in a single repository file.
This made it impossible to host the dataset directly in GitHub due to the **100 MB per-file limit**
and also made local preprocessing slow.

### **2. Splitting the Dataset Into Yearly Files**
To overcome storage limits, we split the dataset into separate yearly CSVs
(e.g., `Crimes_2010.csv`, `Crimes_2011.csv`, etc.).
This worked for some years, but early years (2001–2008) were still too large to upload.
HuggingFace also has storage and built-time constraints, so only a subset of years could be hosted.

### **3. Multi-Year Loading Attempts**
Early prototypes allowed selecting multiple years at once and concatenating them into a single
DataFrame.  
This caused:
- very long load times  
- heavy browser lag  
- HF Spaces freezing and restarting  
- interaction glitches  
- large memory spikes

To maintain usability, we restricted the dashboard to **one year at a time**.

### **4. Buffered Loading UX**
We added loading spinners such as:
- *“Thank you for your patience! Loading data…”*
- *“Filtering data…”*

This improved the user experience but still depended on uploading CSVs manually.

### **5. Attempted Migration to the Chicago Open Data API**
We attempted to fully replace uploaded CSVs by loading data directly from the official SODA API:

**https://data.cityofchicago.org/resource/ijzp-q8t2**

This approach theoretically solves:
- storage limits  
- manual updates  
- HuggingFace file-size constraints  
- stale data issues  

However, in practice:

#### **API Attempt Results**
- HF Spaces repeatedly **crashed** when switching between years  
- The API sometimes returns **300k–500k rows** for a single year  
- HuggingFace Spaces have **limited RAM (CPU containers ~2–4GB)**  
- This caused:
  - out-of-memory (OOM) restarts  
  - frozen interface  
  - long delays  
  - build failures  
  - broken sessions  

While the API method **worked locally**, it became unstable on HuggingFace due to the large volume of
records pulled directly from the live API.

To ensure predictable performance, we reverted to using uploaded CSV files for each year.

### **6. Keep Existing Commented-Out Code**
All commented sections in this script — including multi-year attempts, alternative visualizations,
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
