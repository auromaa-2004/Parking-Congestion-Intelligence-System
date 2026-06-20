import streamlit as st
import pandas as pd
import requests
import folium

from streamlit_folium import st_folium


st.set_page_config(
    page_title="Parking Congestion Intelligence",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"


@st.cache_data
def get_stats():
    return requests.get(
        f"{API_URL}/stats"
    ).json()


@st.cache_data
def get_map_data():
    return requests.get(
        f"{API_URL}/map-data"
    ).json()


@st.cache_data
def get_top_zones():
    return requests.get(
        f"{API_URL}/top-zones?limit=20"
    ).json()



st.title("Parking Congestion Intelligence")

st.markdown(
    """
    AI-powered system for detecting parking hotspots,
    ranking enforcement zones, and supporting
    targeted traffic management.
    """
)


stats = get_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Violations",
        f"{stats['total_violations']:,}"
    )

with col2:
    st.metric(
        "Hotspots",
        f"{stats['total_hotspots']:,}"
    )

with col3:
    st.metric(
        "Critical Zones",
        stats["critical_zones"]
    )

with col4:
    st.metric(
        "Top Zone",
        stats["top_zone"][:25]
    )

st.divider()

st.subheader("Hotspot Map")

map_data = get_map_data()

m = folium.Map(
    location=[12.97, 77.59],
    zoom_start=11
)

for row in map_data:

    priority = row["priority"]
    if priority == "CRITICAL":
        color = "red"
    elif priority == "HIGH":
        color = "orange"
    elif priority == "MEDIUM":
        color = "blue"
    elif priority == "LOW":
        color = "green"
    else:  
        color = "purple"

    popup_html = f"""
    <b>{row['hotspot_name']}</b><br>
    Type: {row['hotspot_type']}<br>
    Risk Score: {round(row['risk_score'],2)}<br>
    Violations: {row['violations']}<br>
    Priority: {row['priority']}
    """

    folium.CircleMarker(
        location=[
            row["latitude"],
            row["longitude"]
        ],
        radius=6,
        color="#2c3e50",      
        weight=1.5,           
        fill=True,
        fill_color=color,    
        fill_opacity=0.85,
        popup=popup_html
    ).add_to(m)


legend_html = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
width: 250px;
height: 195px;
background-color: white;
border:2px solid #2c3e50;
border-radius:8px;
z-index:9999;
font-size:14px;
padding:10px;
box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
">

<b>Risk Priority Legend</b><br><br>

🔴 <b>CRITICAL</b> - Immediate enforcement<br>

🟠 <b>HIGH</b> - High congestion risk<br>

🔵 <b>MEDIUM</b> - Moderate congestion risk<br>

🟢 <b>LOW</b> - Low congestion risk<br>

🟣 <b>VERY LOW</b> - Minimal congestion risk

</div>
"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)


st_folium(
    m,
    width=1200,
    height=600
)

st.divider()



st.subheader("Top 20 Priority Zones")

top_zones = pd.DataFrame(
    get_top_zones()
)

display_cols = [
    "rank",
    "hotspot_name",
    "hotspot_type",
    "risk_score",
    "priority",
    "violations"
]

st.dataframe(
    top_zones[display_cols],
    use_container_width=True
)

st.divider()


st.subheader(" Hotspot Drilldown")

selected_hotspot = st.selectbox(
    "Select Hotspot",
    top_zones["hotspot_name"]
)

zone = top_zones[
    top_zones["hotspot_name"]
    == selected_hotspot
].iloc[0]

col1, col2 = st.columns(2)

with col1:

    st.write(
        f"### {zone['hotspot_name']}"
    )

    st.write(
        f"**Type:** {zone['hotspot_type']}"
    )

    st.write(
        f"**Priority:** {zone['priority']}"
    )

    st.write(
        f"**Risk Score:** "
        f"{round(zone['risk_score'],2)}"
    )

with col2:

    st.write(
        f"**Violations:** "
        f"{zone['violations']:,}"
    )

    st.write(
        f"**Latitude:** "
        f"{round(zone['latitude'],5)}"
    )

    st.write(
        f"**Longitude:** "
        f"{round(zone['longitude'],5)}"
    )

    