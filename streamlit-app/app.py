import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_echarts import st_echarts
from bigquery_services import load_stations, top_ori_demand_by_h3, top_dest_demand_by_h3
from trip_duration_predictor.feature_builder import build_feature_row
from trip_duration_predictor.predict_trip import predict_trip_duration
from trip_duration_predictor.weather_features import build_weather_features
from trip_duration_predictor.dist_features import build_distance_features
from ui_components.map_view import render_map
from demand_analysis.da_visualisations import h3_demand_heatmap, render_demand_heatmap_legend, demand_by_hour_echarts, demand_hour_split_echarts, plot_h3_demand_map
from weather_analysis.wa_visualisations import rain_recency_echarts, rain_vs_no_rain_echarts, snow_impact_echarts, temp_vs_demand_echarts, wind_impact_echarts, snow_impact_echarts, rain_recency_echarts

if "interacted_start_end_stations" not in st.session_state:
    st.session_state.interacted_start_end_stations = False

def mark_interacted_start_end_stations():
    st.session_state.interacted_start_end_stations = True

st.title("🚲 CitiBike Dashboard")

tab1, tab2, tab3 = st.tabs(["⏱️Citibike Trip Duration Predictor", "🗺️Demand Analysis", "🌦️Weather Analysis"]) 


with tab1:
    # ROW 1: Date & Time, Profile
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🗓️ Date & Time")
        date_input = st.date_input("Select date", min_value=datetime.today().date())
        time_input = st.time_input("Select time")

    with col2:
        st.subheader("🚴 Profile")
        is_ebike = st.toggle("Electric Bike", value=False)
        is_member = st.toggle("Member", value=False)

    selected_time = pd.Timestamp(datetime.combine(date_input, time_input))

    # Load stations
    stations_df = load_stations()

    station_map = {
        row["name"]: (row["lat"], row["lon"])
        for _, row in stations_df.iterrows()
    }

    station_names = sorted(station_map.keys())


    # ROW 2: Station selection
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("📍 Start Station")
        start_station = st.selectbox("Start station", station_names, on_change=mark_interacted_start_end_stations)

    with col4:
        st.subheader("🏁 End Station")
        end_station = st.selectbox("End station", station_names, on_change=mark_interacted_start_end_stations)


    start_lat, start_lon = station_map[start_station]
    end_lat, end_lon = station_map[end_station]
    # ROW 3: Map
    st.subheader("🗺️ Route Preview")

    if start_station and end_station and start_station != end_station:
        render_map(start_lat, start_lon, end_lat, end_lon, start_station, end_station)

        # ROW 4: Predict button + results
        feature_row = build_feature_row(start_lat, start_lon, end_lat, end_lon, selected_time, is_ebike, is_member)
        disable_predict = (start_station == end_station)

        # Predict button and display results
        if st.button("Predict Trip Duration", disable_predict):
            duration = predict_trip_duration(feature_row) / 60  # convert seconds to minutes

            weather_info = build_weather_features(start_lat, start_lon, selected_time)
            actual_temp = weather_info["actual_temp"]
            precipitation = weather_info["precipitation_mm"]
            windspeed = weather_info["windspeed"]
            snowfall = weather_info["snowfall"]

            dist_info = build_distance_features(start_lat, start_lon, end_lat, end_lon)
            estimated_dist = dist_info["euclidean_dist_m"] / 1000  # convert to km


            st.success(f"Successful: Estimated based on route distance, time and weather conditions.")

            st.subheader("Prediction Result")
            col1, col2 = st.columns(2)

            col1.metric(label="🚲 Predicted Trip Duration", value=f"{duration:.2f} min")
            col2.metric(label="Estimated Distance", value=f"{estimated_dist:.2f} km")

            st.subheader("🌦️ Weather Conditions at Trip Time")
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("🌡️ Temperature", f"{actual_temp} °C")
            col2.metric("🌧️ Rainfall", f"{precipitation} mm")
            col3.metric("💨 Wind", f"{windspeed} m/s")
            col4.metric("❄️ Snowfall", f"{snowfall} mm")
    else:
        if start_station == end_station and not st.session_state.interacted_start_end_stations:
            st.info("Select two different stations to preview the route 🗺️")
        else:
            st.warning("Start and end stations cannot be the same")


with tab2:
    # ROW 1: Filters - Date, User Type
    col1, col2 = st.columns(2)

    with col1:
        # Date Range (Month and Year)
        st.subheader("📅 Date")
        months_list = list("January February March April May June July August September October November December".split())
        month = st.selectbox("Month", months_list, index=datetime.today().month - 1)
        year = st.selectbox("Year", [2025, 2026], index=1)
        time_input_hm = st.selectbox(
            "Time Filter",
            ["All", "Weekday", "Weekend", "Rush Hour", "Morning", "Evening"]
        )

    with col2:
        st.subheader("🚴 Profile")
        is_ebike_hm = st.toggle("Electric Bike", value=False, key="ebike_hm")
        is_member_hm = st.toggle("Member", value=False, key="member_hm")

    # ROW 2: View Mode, H3 Resolution
    col3, col4= st.columns(2)
    with col3:
        st.subheader("📊 View Mode")
        view_mode = st.selectbox(
            "View Mode",
            ["Origin Demand", "Destination Demand", "Net Flow"]
        )
    with col4:
        st.subheader("🔍 H3 Resolution")
        h3_resolution = st.selectbox(
            "H3 Resolution",
            ["r7","r8", "r9"]
        )
    # ROW 3: Heatmap
    st.subheader("🗺️ Demand Heatmap")

    # Load feature store data
    month_num = months_list.index(month) + 1
    # df = pd.read_csv(f"output/feature_store/features_{year}-{month_num:02d}.csv") # Replace with output/feature_store/features_YYYY-MM.csv
    df = pd.read_csv("./output/samples/feature_store/features_sample.csv") # Temp

    # Placing legend directly below the heatmap (Bottom Right)
    heatmap = h3_demand_heatmap(df, view_mode, h3_resolution, time_input_hm, is_ebike_hm, is_member_hm)
    legend_b64 = render_demand_heatmap_legend(view_mode)
    st.pydeck_chart(heatmap)
    st.markdown(
        f"""
        <style>
        .legend-container {{
            position: relative;
        }}

        .legend-box {{
            position: absolute;
            bottom: 12px;
            right: 0px;
            background: ;
            padding: 6px;
            border-radius: 6px;
            box-shadow: 0 1px 6px rgba(0,0,0,0);
            z-index: 10;
        }}

        .legend-box img {{
            width: 140px;
            height: auto;
        }}
        </style>

        <div class="legend-container">
            <div class="legend-box">
                <img src="data:image/png;base64,{legend_b64}" />
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Visualisation: Demand - Time Analysis
    st.header("📈 Demand - Time Analysis")
    option_dbh = demand_by_hour_echarts(df)
    option_dhs = demand_hour_split_echarts(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st_echarts(option_dbh, height="400px")
    with col2:
        st_echarts(option_dhs, height="400px")
    
    # Visualisation - Top H3 Regions by Demand (Origin)
    st.header("🚴 Top Trip Origins/Destinations (Fine-Grained)")
    top_ori_demand_by_h3_df = top_ori_demand_by_h3()
    st.plotly_chart(plot_h3_demand_map(top_ori_demand_by_h3_df, is_origin=True), use_container_width=True)

    # Visualisation - Top H3 Regions by Demand (Destination)
    top_dest_demand_by_h3_df = top_dest_demand_by_h3()
    st.plotly_chart(plot_h3_demand_map(top_dest_demand_by_h3_df, is_origin=False), use_container_width=True)

with tab3:
    st.header("🌦️ Weather Analysis - Impact on Demand")
    
    col1, col2 = st.columns(2)
    with col1:
        # Visualisation: Rain vs No Rain
        st.subheader("🌧️ Rain vs No Rain") 
        st_echarts(rain_vs_no_rain_echarts(df), height="400px")
    with col2:
        # Visualisation: Temperatre vs Demand
        st.subheader("🌡️ Temperature")
        temp_vs_demand_echarts(df)

    col3, col4 = st.columns(2)
    with col3:
        # Visualisation: Wind Speed Impact
        st.subheader("💨 Wind Speed")
        wind_impact_echarts(df)
    with col4:
        # Visualisation: Snowfall Impact
        st.subheader("❄️ Snowfall")
        snow_impact_echarts(df)  

    # Visualisation: Rain Recency Effect
    st.subheader("⏱️ Rain Recency Effect")
    rain_recency_echarts(df)

