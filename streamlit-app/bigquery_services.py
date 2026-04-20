import streamlit as st
from google.cloud import bigquery

client = bigquery.Client()

@st.cache_data
def load_stations():
    query = f"""
    SELECT short_name, name, lat, lon
    FROM `is3107-491906.citibike.static_stations`
    ORDER BY name
    """
    return client.query(query).to_dataframe()

def top_ori_demand_by_h3():
    query = f"""
    SELECT
    origin_h3_r9,
    COUNT(*) AS trip_count
    FROM `is3107-491906.citibike.features`
    GROUP BY origin_h3_r9
    """
    return client.query(query).to_dataframe()

def top_dest_demand_by_h3():
    query = f"""
    SELECT
    dest_h3_r9,
    COUNT(*) AS trip_count
    FROM `is3107-491906.citibike.features`
    GROUP BY dest_h3_r9
    """
    return client.query(query).to_dataframe()