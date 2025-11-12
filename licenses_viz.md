---
layout: page
title: Licenses Visualizations (Fall 2022)
permalink: /licenses-viz/
---

## Visualization 1: Licenses by Type and Status
The first visualization shows the distribution of professional licenses across different license types, categorized by their current status (e.g., Active, Inactive, or Expired). I chose a bar chart because it clearly communicates categorical comparisons — the x-axis represents the license type, and the y-axis represents the number of licenses in each category. Each bar is colored by license status to make the active/inactive distinction visually immediate. Before plotting, I cleaned the dataset by standardizing column names, removing missing values, and aggregating the data using `groupby` in Pandas. The design emphasizes clear comparisons and readability: the color encoding helps quickly highlight which professions have the most active licenses relative to their inactive or expired ones.

<div style="margin:1rem 0;">
  <a class="btn" href="https://github.com/UIUC-iSchool-DataViz/is445_data/raw/main/licenses_fall2022.csv" target="_blank">The Data</a>
  <a class="btn" href="https://github.com/RohitYadav-edu/RohitYadav-edu.github.io/blob/main/python_notebooks/licenses_viz.ipynb" target="_blank">The Analysis</a>
</div>

<iframe src="/assets/vis/licenses/chart1.html" width="100%" height="520" style="border:1px solid #ddd;border-radius:6px;"></iframe>

---

## Visualization 2: License Trends Over Time (Interactive)
The second visualization explores temporal trends in the issuance of licenses. It uses a line chart to show how the number of licenses issued each month changes over time for different license types. A dropdown menu allows the viewer to select a specific license type (defaulting to “Appraisal”) to focus on. This interactivity lets users explore trends in a targeted way without cluttering the view with every category at once. To prepare this visualization, I parsed the date columns in Python, created a `year_month` variable, and then aggregated license counts by month and license type. The interactive dropdown improves clarity and engagement by making it easy to isolate the time trends for individual professions.

<div style="margin:1rem 0;">
  <a class="btn" href="https://github.com/UIUC-iSchool-DataViz/is445_data/raw/main/licenses_fall2022.csv" target="_blank">The Data</a>
  <a class="btn" href="https://github.com/RohitYadav-edu/RohitYadav-edu.github.io/blob/main/python_notebooks/licenses_viz.ipynb" target="_blank">The Analysis</a>
</div>

<iframe src="/assets/vis/licenses/chart2.html" width="100%" height="520" style="border:1px solid #ddd;border-radius:6px;"></iframe>
