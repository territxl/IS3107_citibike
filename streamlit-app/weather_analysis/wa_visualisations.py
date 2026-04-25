import streamlit as st
import plotly.express as px

# -----------------------------
# VISUALISATIONS
# -----------------------------
   
def rain_vs_no_rain_echarts(data):
    # data cols: [actual_temp, windspeed, snowfall, mins_since_rain, is_raining, trip_count]

    counts = data.groupby("is_raining")["trip_count"].sum() # e.g. {True: x, False: y}
    rain_count    = int(counts.get(True,  0))
    no_rain_count = int(counts.get(False, 0))

    option_rain = {
        "title": {"text": "Trips Demand by Rainfall", "left": "center"},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {
            "orient": "vertical",
            "bottom": "bottom",
        },
        "series": [{
            "type": "pie",
            "radius": "60%",
            "data": [
                {"name": "No Rain", "value": no_rain_count},
                {"name": "Rain",    "value": rain_count}
            ]
        }]
    }
    return option_rain

def temp_vs_demand_echarts(data):
    fig = px.histogram(data, x="actual_temp", y="trip_count", histfunc="sum", nbins=10, title="Temperature", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Temperature (°C)")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, width='content')

def wind_impact_echarts(data):
    fig = px.histogram(data, x="windspeed", y="trip_count", histfunc="sum", nbins=10, title="Wind Speed", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Wind Speed (m/s)")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, width='content')

def snow_impact_echarts(data):
    fig = px.histogram(data, x="snowfall", y="trip_count", histfunc="sum", nbins=10, title="Snowfall", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Snowfall (mm)")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, width='content')

def rain_recency_echarts(data):
    fig = px.histogram(data, x="mins_since_rain", y="trip_count", histfunc="sum", nbins=10, title="Rain Recency", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Minutes Since Rain")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, width='content')