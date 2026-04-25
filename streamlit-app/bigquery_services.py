import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import datetime

def convert_to_datetime(year, month):
    start = datetime.datetime(year, month, 1)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1)
    else:
        end = datetime.datetime(year, month + 1, 1)
    return str(start), str(end)

@st.cache_resource
def get_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials)

client = get_client()

@st.cache_data
def load_stations():
    query = f"""
    SELECT short_name, name, lat, lon
    FROM `is3107-491906.citibike.static_stations`
    ORDER BY name
    """
    return client.query(query).to_dataframe()

@st.cache_data
def top_ori_demand_by_h3(year, month):
    query = f"""
    SELECT
      origin_h3_r9,
      origin_h3_r8,
      origin_h3_r7,
      is_member,
      is_ebike,
      is_weekend,
      is_rush_hour,
      hour,
      COUNT(*) AS trip_count
    FROM `is3107-491906.citibike.features`
    WHERE 
        EXTRACT(YEAR FROM started_at) = {year}
        AND month = {month}
    GROUP BY origin_h3_r9, origin_h3_r8, origin_h3_r7, is_member, is_ebike, is_weekend, is_rush_hour, hour
    LIMIT 100000
    """
    return client.query(query).to_dataframe()

@st.cache_data
def top_dest_demand_by_h3(year, month):
    query = f"""
    SELECT
      dest_h3_r9,
      dest_h3_r8,
      dest_h3_r7,
      is_member,
      is_ebike,
      is_weekend,
      is_rush_hour,
      hour,
      COUNT(*) AS trip_count
    FROM `is3107-491906.citibike.features`
    WHERE 
        EXTRACT(YEAR FROM started_at) = {year}
        AND month = {month}
    GROUP BY dest_h3_r9, dest_h3_r8, dest_h3_r7, is_member, is_ebike, is_weekend, is_rush_hour, hour
    LIMIT 100000
    """
    return client.query(query).to_dataframe()

@st.cache_data
def obtain_feature_store(year, month):
    start_date, end_date = convert_to_datetime(year, month)
    query = f"""
    SELECT is_weekend, is_rush_hour, hour, is_holiday, is_member, is_ebike, origin_h3_r8, 
        dest_h3_r8, origin_h3_r9, dest_h3_r9, origin_h3_r7, dest_h3_r7, is_raining, actual_temp, windspeed, snowfall, mins_since_rain
    FROM `is3107-491906.citibike.features`
    WHERE 
        started_at >= '{start_date}' 
        AND started_at < '{end_date}'
    LIMIT 100000
    """
    return client.query(query).to_dataframe()

@st.cache_data
def obtain_demand_by_hour_echarts(year, month):
    start_date, end_date = convert_to_datetime(year, month)
    query = f"""
    SELECT is_weekend, hour, is_member, is_ebike, count(*) as num_trips
    FROM `is3107-491906.citibike.features`
    WHERE 
        started_at >= '{start_date}' 
        AND started_at < '{end_date}'
    group by 1, 2, 3, 4
    """
    return client.query(query).to_dataframe()