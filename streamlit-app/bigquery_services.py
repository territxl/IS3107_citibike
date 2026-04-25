import streamlit as st
from google.cloud import bigquery

client = bigquery.Client(project="is3107-491906")

@st.cache_data
def load_stations():
    query = f"""
    SELECT short_name, name, lat, lon
    FROM `is3107-491906.citibike.static_stations`
    ORDER BY name
    """
    return client.query(query).to_dataframe()

@st.cache_data
def top_ori_demand_by_h3():
    query = f"""
    SELECT
    origin_h3_r9,
    COUNT(*) AS trip_count
    FROM `is3107-491906.citibike.features`
    GROUP BY origin_h3_r9
    """
    return client.query(query).to_dataframe()

@st.cache_data
def top_dest_demand_by_h3():
    query = f"""
    SELECT
    dest_h3_r9,
    COUNT(*) AS trip_count
    FROM `is3107-491906.citibike.features`
    GROUP BY dest_h3_r9
    """
    return client.query(query).to_dataframe()

@st.cache_data
def obtain_feature_store(year, month):
    query = f"""
    SELECT is_weekend, is_rush_hour, hour, is_holiday, is_member, is_ebike, origin_h3_r8, 
        dest_h3_r8, origin_h3_r9, dest_h3_r9, origin_h3_r7, dest_h3_r7, is_raining, actual_temp, windspeed, snowfall, mins_since_rain
    FROM `is3107-491906.citibike.features`
    WHERE 
        EXTRACT(YEAR FROM started_at) = {year}
        AND month = {month}
    LIMIT 100000
    """
    return client.query(query).to_dataframe()