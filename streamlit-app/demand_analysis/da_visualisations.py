import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import base64
import h3
import plotly.express as px
from io import BytesIO

# -----------------------------
# LEGEND (MATPLOTLIB)
# -----------------------------
def render_demand_heatmap_legend(viewmode: str):
    fig, ax = plt.subplots(figsize=(2.2, 0.4)) 

    gradient = [[(1, g/255, 0) for g in range(255, -1, -1)]]
    ax.imshow(gradient, aspect="auto", extent=[0, 1, 0, 1], origin="upper")

    ax.set_xticks([0, 0.5, 1])
    ax.set_xticklabels(["Low", "Med", "High"], fontsize=7, color="white")
    ax.set_yticks([])
    ax.tick_params(axis="x", color="white")
    ax.set_title(f"{viewmode}", fontsize=8, color="white")

    plt.tight_layout()
    return fig_to_base64(fig)

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=True, dpi=200)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

# -----------------------------
# H3 TO POLYGON
# -----------------------------

def h3_to_polygon(h):
    boundary = h3.cell_to_boundary(h) 
    return {
        "type": "Polygon",
        "coordinates": [[(lng, lat) for lat, lng in boundary]]
    }


# -----------------------------
# VISUALISATIONS
# -----------------------------
def h3_demand_heatmap(
    df: pd.DataFrame,
    view_mode: str = "Origin Demand",
    h3_resolution: str = "r8",
    time_filter: str = "All",
    is_ebike_filter: bool = False,
    is_member_filter: bool = False,
    center_lat: float = 40.75,
    center_lon: float = -73.98,
    zoom: int = 11
):

    data = df.copy()

    # -----------------------------
    # FILTER
    # -----------------------------
    if time_filter == "Weekday":
        data = data[data["is_weekend"] == False]
    elif time_filter == "Weekend":
        data = data[data["is_weekend"] == True]
    elif time_filter == "Rush Hour":
        data = data[data["is_rush_hour"] == True]
    elif time_filter == "Morning":
        data = data[data["hour"].between(6, 11)]
    elif time_filter == "Evening":
        data = data[data["hour"].between(16, 20)]
    elif time_filter == "Holiday":
        data = data[data["is_holiday"] == True]

    if is_member_filter:
        data = data[data["is_member"] == True]
    if is_ebike_filter:
        data = data[data["is_ebike"] == True]

    # -----------------------------
    # H3 SELECTION
    # -----------------------------
    origin_col = "origin_h3_r9" if h3_resolution == "r9" else "origin_h3_r8"
    dest_col = "dest_h3_r9" if h3_resolution == "r9" else "dest_h3_r8"

    # -----------------------------
    # AGGREGATION
    # -----------------------------
    if view_mode == "Origin Demand":
        agg = data.groupby(origin_col).size().reset_index(name="count")
        agg = agg.rename(columns={origin_col: "hex"})

    elif view_mode == "Destination Demand":
        agg = data.groupby(dest_col).size().reset_index(name="count")
        agg = agg.rename(columns={dest_col: "hex"})

    else:
        origin = data.groupby(origin_col).size().reset_index(name="outflow")
        dest = data.groupby(dest_col).size().reset_index(name="inflow")

        agg = pd.merge(
            origin,
            dest,
            left_on=origin_col,
            right_on=dest_col,
            how="outer"
        ).fillna(0)

        agg["hex"] = agg[origin_col].fillna(agg[dest_col])
        agg["count"] = agg["inflow"] - agg["outflow"]

    # -----------------------------
    # NORMALISATION
    # -----------------------------
    max_val = agg["count"].abs().max() + 1e-6

    agg["elevation"] = agg["count"] / max_val

    # Color mapping to use yellow-to-red gradient
    agg["color"] = agg["count"].apply(
        lambda x: [
            int(255),  
            int(255 - (abs(x) / max_val) * 255),  
            0  
        ]
    )

    # -----------------------------
    # NYC BOROUGH GEOJSON (REAL DATA)
    # -----------------------------
    nyc_boroughs_url = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/new-york-city-boroughs.geojson"

    borough_layer = pdk.Layer(
        "GeoJsonLayer",
        data=nyc_boroughs_url,
        stroked=True,
        filled=True,
        opacity=0.08,
        get_fill_color=[200, 200, 200],
        get_line_color=[60, 60, 60],
        line_width_min_pixels=2,
    )

    # -----------------------------
    # H3 LAYER
    # -----------------------------
    h3_layer = pdk.Layer(
        "H3HexagonLayer",
        data=agg,
        get_hexagon="hex",
        get_fill_color="color",
        get_elevation="elevation * 500",
        elevation_scale=50,
        pickable=True,
        extruded=True,
    )

    # -----------------------------
    # VIEW
    # -----------------------------
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=45
    )

    # -----------------------------
    # FINAL DECK
    # -----------------------------
    deck = pdk.Deck(
        layers=[borough_layer, h3_layer],
        initial_view_state=view_state,
        tooltip={"text": "Trips: {count}"}
    )

    return deck

def demand_by_hour_echarts(df):
    hourly = (
        df.groupby("hour")
        .size()
        .reset_index(name="trip_count")
        .sort_values("hour")
    )
    option_dbh = {
        "title": {
            "text": "Trips by Hour", 
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
        },
        "xAxis": {
            "type": "category",
            "name": "Hour of Day",
            "nameLocation": "middle",
            "nameGap": 30,
            "data": hourly["hour"].tolist()
        },
        "yAxis": {
            "type": "value",
            "name": "       Number of Trips",
            "nameLocation": "end",   
            "nameRotate": 0,         
            "nameGap": 15,
        },
        "series": [{
            "name": "Trips",
            "data": hourly["trip_count"].tolist(),
            "type": "line",
            "smooth": True
        }]
    }
    return option_dbh

def demand_hour_split_echarts(df):
    grouped = (
        df.groupby(["hour", "is_weekend"])
        .size()
        .reset_index(name="trip_count")
    )
    weekday = grouped[grouped["is_weekend"] == False]
    weekend = grouped[grouped["is_weekend"] == True]
    option_dhs = {
        "title": {
            "text": "Trips by Hour (Days of Week)", 
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis"
        },
        "legend": {
            "data": ["Weekday", "Weekend"], 
            "top": 30,
            "left": "right",
            "textStyle": {
                "fontSize": 10}
        },
        "xAxis": {
            "type": "category", 
            "data": list(range(24)), 
            "name": "Hour of Day", 
            "nameLocation": "middle", 
            "nameGap": 30
        },
        "yAxis": {
            "type": "value",
            "name": "       Number of Trips",
            "nameLocation": "end",   
            "nameRotate": 0,         
            "nameGap": 15,
        },
        "series": [
            {
                "name": "Weekday",
                "type": "line",
                "data": weekday.sort_values("hour")["trip_count"].tolist(),
                "smooth": True
            },
            {
                "name": "Weekend",
                "type": "line",
                "data": weekend.sort_values("hour")["trip_count"].tolist(),
                "smooth": True
            }
        ]
    }
    return option_dhs

def plot_h3_demand_map(df, is_origin=True):
    df = df.reset_index(drop=True)
    df["id"] = df.index.astype(str)
    df["geometry"] = df["origin_h3_r9"].apply(h3_to_polygon) if is_origin else df["dest_h3_r9"].apply(h3_to_polygon)

    # ----------------------------
    # Data Preparation
    # ----------------------------
    df = df.copy()
    df = df.reset_index(drop=True)

    df["id"] = df.index.astype(str)
    df = df.sort_values("trip_count", ascending=False)
    df["rank"] = range(len(df))
    df["is_top10"] = df["rank"] < 10

    # ----------------------------
    # GeoJSON Construction
    # ----------------------------
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for _, row in df.iterrows():
        geojson["features"].append({
            "type": "Feature",
            "id": row["id"],
            "geometry": row["geometry"],
            "properties": {
                "trip_count": row["trip_count"],
                "is_top10": row["is_top10"]
            }
        })

    # ----------------------------
    # Choropleth Map
    # ----------------------------
    fig = px.choropleth_map(
        df,
        geojson=geojson,
        locations="id",
        color="trip_count",
        color_continuous_scale="YlOrRd",
        zoom=10,
        center={"lat": 40.7, "lon": -74},
        opacity=0.6,
        hover_data={
            "trip_count": True,
            "id": False
        },
        title="Origin" if is_origin else "Destination"
    )

    # Clean Hover (remove id, keep only trips)
    fig.update_traces(
        hovertemplate="<b>Trips:</b> %{z:,}<extra></extra>"
    )

    # ----------------------------
    # Top 10 Hotspots
    # ----------------------------
    top10 = df[df["is_top10"]]

    if is_origin:
        top10_lat, top10_lon = zip(*[
            h3.cell_to_latlng(h) for h in top10["origin_h3_r9"]
        ])
    else:
        top10_lat, top10_lon = zip(*[
            h3.cell_to_latlng(h) for h in top10["dest_h3_r9"]
        ])

    fig.add_scattermap(
        lat=[lat for lat, lon in zip(top10_lat, top10_lon)],
        lon=[lon for lat, lon in zip(top10_lat, top10_lon)],
        mode="markers",
        marker=dict(size=12, color="red", opacity=0.8, symbol="star"),
        name="Top 10 Hotspots",
        text=top10["trip_count"],
        hovertemplate="<b>Top Hotspot</b><br>Trips: %{text:,}<extra></extra>"
    )

    # ----------------------------
    # Final Layout
    # ----------------------------
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Trips")
    )

    return fig