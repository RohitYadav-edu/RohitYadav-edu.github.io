---
layout: page
title: Licenses Visualizations (Fall 2022)
permalink: /licenses-viz/
---

## Visualization 1: Licenses by Type and Status
This visualization shows the distribution of licenses across professional **license types** and their **current status**. A **bar chart** communicates categorical comparison clearly: the x-axis encodes **license_type (N)** and the y-axis encodes the **count of records (Q)**. I color the bars by **license_status (N)** to make the active vs. inactive/expired distinction obvious at a glance. 

**Design choices:**  
Bars emphasize differences between categories. Position (x, y) communicates magnitude effectively, while color (hue) segments by status. I chose a **categorical color palette** (contrasting but perceptually balanced colors) so viewers can easily distinguish statuses without implying a numeric order.  

**Data transformations:**  
I standardized column names, removed rows with missing `license_type` or `license_status`, and used Pandas `groupby` to count the number of licenses in each `(license_type, license_status)` combination. I also ordered license types by descending total count to make the plot easier to read.  

**Interpretation:**  
This chart highlights which professions dominate the dataset and which have a high proportion of active versus inactive licenses, making it a strong summary of professional activity distribution.

<div style="margin:1rem 0;">
  <a class="btn" href="https://github.com/UIUC-iSchool-DataViz/is445_data/raw/main/licenses_fall2022.csv" target="_blank">The Data</a>
  <a class="btn" href="https://github.com/RohitYadav-edu/RohitYadav-edu.github.io/blob/main/python_notebooks/licenses_viz.ipynb" target="_blank">The Analysis</a>
</div>

<iframe src="https://rohityadav-edu.github.io/assets/vis/licenses/chart1.html" width="100%" height="520" style="border:1px solid #ddd;border-radius:6px;"></iframe>

---

## Visualization 2: Monthly License Counts by Type (Interactive)
This visualization explores how the number of licenses changes **over time** for each license type. I use a **line chart** where the x-axis encodes **year_month (temporal)** and the y-axis encodes the **count of licenses (quantitative)**. The line’s color encodes **license_type (nominal)**, but to avoid clutter I add a **dropdown menu** that lets viewers focus on a single license type (defaulting to *Appraisal*).  

**Design choices:**  
Line charts effectively reveal temporal patterns. The x-position shows time progression; the y-position shows volume. Color originally distinguished license types, but I added the dropdown so only one type is visible at a time, improving clarity. Each data point includes a visible marker to emphasize discrete months.  

**Data transformations:**  
I parsed the most complete date column into a datetime format, derived a **`year_month`** variable, and then aggregated the data using `groupby(['year_month', 'license_type'])` to count monthly totals.  

**Interactivity (Altair dropdown parameter):**  
This plot introduces a selection parameter bound to a dropdown menu. When a license type is selected, the chart filters dynamically to show only that type’s time series. This goes beyond simple pan/zoom by allowing focused comparison. It enhances **clarity** (reduces overplotting) and **engagement** (users explore trends for different professions interactively).

**Interpretation:**  
This visualization helps identify seasonal or yearly changes in licensing activity for any chosen profession, such as increases in new “Appraisal” licenses in specific years.

<div style="margin:1rem 0;">
  <a class="btn" href="https://github.com/UIUC-iSchool-DataViz/is445_data/raw/main/licenses_fall2022.csv" target="_blank">The Data</a>
  <a class="btn" href="https://github.com/RohitYadav-edu/RohitYadav-edu.github.io/blob/main/python_notebooks/licenses_viz.ipynb" target="_blank">The Analysis</a>
</div>

<iframe src="https://rohityadav-edu.github.io/assets/vis/licenses/chart2.html" width="100%" height="520" style="border:1px solid #ddd;border-radius:6px;"></iframe>
