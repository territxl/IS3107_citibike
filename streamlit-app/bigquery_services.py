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

@st.cache_data
def get_h3_heatmap_data(year, month, time_filter, is_member_filter=False, is_ebike_filter=False, h3_level='r7'):
    start_date, end_date = convert_to_datetime(year, month)
    h3_origin_col = f"origin_h3_{h3_level}"
    h3_dest_col = f"dest_h3_{h3_level}"

    predicates = [
        f"started_at >= '{start_date}'",
        f"started_at < '{end_date}'",
    ]
    if time_filter == "Weekday":
        predicates.append("is_weekend = FALSE")
    elif time_filter == "Weekend":
        predicates.append("is_weekend = TRUE")
    elif time_filter == "Rush Hour":
        predicates.append("is_rush_hour = TRUE")
    elif time_filter == "Morning":
        predicates.append("hour BETWEEN 6 AND 11")
    elif time_filter == "Evening":
        predicates.append("hour BETWEEN 16 AND 20")
    if is_member_filter:
        predicates.append("is_member = TRUE")
    if is_ebike_filter:
        predicates.append("is_ebike = TRUE")

    query = f"""
    select h3_cell, sum(origin_count) as origin_count, sum(dest_count) as dest_count
    FROM (
        SELECT {h3_origin_col} AS h3_cell, COUNT(*) AS origin_count, 0 AS dest_count
        FROM `is3107-491906.citibike.features`
        WHERE {' AND '.join(predicates)}
        GROUP BY h3_cell

        UNION ALL

        SELECT {h3_dest_col} AS h3_cell, 0 AS origin_count, COUNT(*) AS dest_count
        FROM `is3107-491906.citibike.features`
        WHERE {' AND '.join(predicates)}
        GROUP BY h3_cell
    )
    GROUP BY h3_cell
    """
    return client.query(query).to_dataframe()

@st.cache_data
def get_weather_agg(
    year,
    month,
    time_filter,
    is_member_filter=False,
    is_ebike_filter=False,
):
    start_date, end_date = convert_to_datetime(year, month)

    predicates = [
        f"started_at >= '{start_date}'",
        f"started_at <  '{end_date}'",
    ]
    if time_filter == "Weekday":
        predicates.append("is_weekend = FALSE")
    elif time_filter == "Weekend":
        predicates.append("is_weekend = TRUE")
    elif time_filter == "Rush Hour":
        predicates.append("is_rush_hour = TRUE")
    elif time_filter == "Morning":
        predicates.append("hour BETWEEN 6 AND 11")
    elif time_filter == "Evening":
        predicates.append("hour BETWEEN 16 AND 20")
    if is_member_filter:
        predicates.append("is_member = TRUE")
    if is_ebike_filter:
        predicates.append("is_ebike = TRUE")

    query = f"""
    SELECT
        actual_temp,
        windspeed,
        snowfall,
        mins_since_rain,
        is_raining,
        COUNT(*) AS trip_count
    FROM `is3107-491906.citibike.features`
    WHERE {' AND '.join(predicates)}
    GROUP BY actual_temp, windspeed, snowfall, mins_since_rain, is_raining
    """
    return client.query(query).to_dataframe()