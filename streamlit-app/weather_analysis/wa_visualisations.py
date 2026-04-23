import streamlit as st
import plotly.express as px

# -----------------------------
# VISUALISATIONS
# -----------------------------
   
def rain_vs_no_rain_echarts(df):
    rain = df["is_raining"]

    rain = rain.astype(bool).tolist()

    rain_count = sum(rain)
    no_rain_count = len(rain) - rain_count 
    
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
                {"name": "Rain", "value": rain_count}
            ]
        }]
    }
    return option_rain

def temp_vs_demand_echarts(df):
    fig = px.histogram(df, x="actual_temp", nbins=10, title="Temperature", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Temperature (°C)")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, use_container_width=True)

def wind_impact_echarts(df):
    fig = px.histogram(df, x="windspeed", nbins=10, title="Wind Speed", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Wind Speed (m/s)")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, use_container_width=True)

def snow_impact_echarts(df):
    fig = px.histogram(df, x="snowfall", nbins=10, title="Snowfall", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Snowfall (mm)")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, use_container_width=True)

def rain_recency_echarts(df):
    fig = px.histogram(df, x="mins_since_rain", nbins=10, title="Rain Recency", color_discrete_sequence=["#2E86C1"], opacity=0.85)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title_text="Minutes Since Rain")
    fig.update_yaxes(title_text="Number of Trips")
    st.plotly_chart(fig, use_container_width=True)