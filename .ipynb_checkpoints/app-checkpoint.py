import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.set_page_config(
    page_title="Chicago Crime Dashboard",
    layout="wide"
)

# ------------------------------------------------------------------------------
#  PLACEHOLDER: YOUR ORIGINAL COMMENTED-OUT CODE
#  (Paste your entire commented code block EXACTLY here)
# ------------------------------------------------------------------------------

# Example placeholder:
# # Old HF loading logic:
# # df = pd.read_csv("https://huggingface.co/...") 
# # This was causing issues due to file size and lag.
#
# # Old multi-year slider attempt:
# # year_range = st.slider("Select years", 2001, 2024, (2010, 2020))
# # This caused extreme lag on HF Spaces.


# ------------------------------------------------------------------------------
# Helper: Load data for ONE year from Chicago Data Portal API
# ------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_year_data(year):
    """
    Loads crime data for a single year using the official Chicago Data Portal (SODA API).
    Returns a pandas DataFrame.
    """

    # Very high limit to avoid Chicago default 1000 row cap
    limit = 50000000

    api_url = (
        "https://data.cityofchicago.org/resource/ijzp-q8t2.json"
        f"?$limit={limit}"
        f"&$where=year={year}"
    )

    response = requests.get(api_url)

    if response.status_code != 200:
        st.error(f"Failed to fetch data for {year}. API Error: {response.status_code}")
        return pd.DataFrame()

    df = pd.DataFrame(response.json())

    # Basic cleaning
    if not df.empty:
        if "latitude" in df.columns and "longitude" in df.columns:
            df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


# ------------------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------------------

st.sidebar.header("Filters")

year_list = list(range(2001, datetime.now().year + 1))
selected_year = st.sidebar.selectbox("Select Year", year_list, index=year_list.index(2020))

st.sidebar.markdown("### Tip:")
st.sidebar.markdown("Selecting one year at a time improves performance significantly.")

with st.spinner("Loading data for selected year..."):
    df = load_year_data(selected_year)

st.write(f"### Crimes in {selected_year} — Total Records: {len(df):,}")

if df.empty:
    st.warning("No data available for the selected year.")
    st.stop()


# ------------------------------------------------------------------------------
# TABS
# ------------------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs(["📊 Crime Type Distribution", "📅 Monthly Trends", "📍 Map View"])

# ------------------------------------------------------------------------------
# TAB 1 – Crime Type Distribution
# ------------------------------------------------------------------------------

with tab1:
    st.subheader("Distribution of Crime Types")
    st.caption("Hover for counts. Click to lightly highlight a bar.")

    crime_counts = df["primary_type"].value_counts().reset_index()
    crime_counts.columns = ["primary_type", "count"]

    fig1 = px.bar(
        crime_counts,
        x="primary_type",
        y="count",
        title="Crime Frequency by Type",
        color="count",
        color_continuous_scale="Blues"
    )
    fig1.update_layout(
        xaxis_title="Crime Type",
        yaxis_title="Count",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig1.update_xaxes(tickangle=45)

    st.plotly_chart(fig1, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 2 – Monthly Trend
# ------------------------------------------------------------------------------

with tab2:
    st.subheader("Monthly Crime Trend")
    st.caption("Hover to see exact monthly numbers.")

    df["month"] = df["date"].dt.month
    monthly_counts = df.groupby("month").size().reset_index(name="count")

    fig2 = px.line(
        monthly_counts,
        x="month",
        y="count",
        markers=True,
        title="Crimes per Month",
    )
    fig2.update_traces(hovertemplate="Month %{x}<br>Count: %{y}")
    fig2.update_layout(
        xaxis_title="Month",
        yaxis_title="Crimes",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    st.plotly_chart(fig2, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 3 – Map
# ------------------------------------------------------------------------------

with tab3:
    st.subheader("Crime Location Map")
    st.caption("Zoom and pan enabled. Simple, clean map for clarity.")

    df_map = df.dropna(subset=["latitude", "longitude"])

    if df_map.empty:
        st.warning("No mappable coordinates for this year.")
    else:
        fig3 = px.scatter_mapbox(
            df_map,
            lat="latitude",
            lon="longitude",
            hover_name="primary_type",
            hover_data={"latitude": False, "longitude": False},
            zoom=9,
            opacity=0.5,
        )
        fig3.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        st.plotly_chart(fig3, use_container_width=True)


# ------------------------------------------------------------------------------
#  IMPLEMENTATION ISSUES & ITERATIONS (FINAL SECTION)
# ------------------------------------------------------------------------------

st.markdown("---")
st.markdown("## 🛠️ Implementation Issues & Iterations (Data Size, Hosting & Design Decisions)")

st.markdown("""
We intentionally kept this section to document the engineering decisions behind
the dashboard and to show the evolution of the design.

### **1. Original dataset size (~2 GB)**
- We first downloaded the entire “Crimes 2001 to Present” CSV bundle (~2 GB).
- This exceeded GitHub’s 100 MB single-file limit.
- It also made local processing slow.

### **2. Yearly CSV splits on GitHub / HuggingFace**
- We split the dataset into individual yearly files to bypass the file-size limit.
- Early years (2001–2008) were still too large for GitHub.
- HuggingFace Storage also limited how many years we could upload.

### **3. Multi-year concatenation attempts**
- Initial versions supported selecting multiple years at once.
- Concatenating multiple large files caused:
  - Very long loading times  
  - Glitchy interface  
  - HF Spaces freezing or timing out  

### **4. Single-year restriction + Loading spinners**
- To improve UX, we changed to a single-year dropdown.
- Added friendly loading messages like:
  - *“Thank you for your patience! Loading data...”*
  - *“Filtering data...”*

This improved the experience but still depended on pre-uploaded CSV files.

### **5. Final migration to the Chicago Open Data API (current design)**
- Completely removed the need for hosting files on GitHub or HuggingFace.
- Now the app loads data directly from:  
  **https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2**
- We request only one year at a time and cache it with `st.cache_data`.
- This:
  - Solves all storage issues  
  - Greatly improves performance  
  - Ensures data stays up-to-date  
  - Eliminates lag from multi-GB CSV handling  

### **6. Why the commented-out code remains**
- It shows all the iterations we tried.
- Demonstrates your engineering process.
- Provides transparency on why the final design works better.
- Helpful if instructors review progress or if future teammates extend the work.

All improvements respect performance constraints on HuggingFace while maintaining a
clean, professional, and believable level of interactivity.
""")
