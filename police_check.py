import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import datetime


#  Page Configuration (Modern Pro UI)

st.set_page_config(
    page_title="Police Traffic Stop Dashboard",
    layout="wide"
)

st.markdown("""
<style>
.reportview-container { padding: 0rem 2rem; }

.big-metric {
    background-color: #F5F7FA;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    font-weight: 600;
    border: 1px solid #E1E5EB;
}

h2 { padding-top: 20px; }

.stButton>button {
    background-color: #2E7DFA;
    color: white;
    border-radius: 8px;
    padding: 8px 20px;
}
</style>
""", unsafe_allow_html=True)


#  Database Connection

def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="Police_Check_new"
        )
    except:
        st.error("❌ Cannot connect to MySQL. Start Apache + MySQL.")
        return None


#  Load Data

@st.cache_data(ttl=300)
def load_data():
    db = connect_db()
    if db:
        return pd.read_sql("SELECT * FROM cleaned_traffic_stops", db)
    return pd.DataFrame()

df = load_data()


#  Dynamic Story Insight Generator

def generate_dynamic_insight(row):
    stop_date = row.get("stop_date", "Unknown")
    stop_time = row.get("stop_time", "")
    if isinstance(stop_time, datetime.time):
        stop_time = stop_time.strftime("%I:%M %p")

    gender = str(row.get("driver_gender", "Unknown")).title()
    age = row.get("driver_age", "Unknown")
    race = row.get("driver_race", "Unknown")
    violation = row.get("violation", "Unknown")
    outcome = row.get("stop_outcome", "Unknown")
    vehicle = row.get("vehicle_number", "Unknown")
    duration = row.get("stop_duration", "Unknown")
    country = row.get("country_name", "Unknown")

    search = "a search was conducted" if row.get("search_conducted", 0) == 1 else "no search was conducted"
    drug = "a drug-related stop" if row.get("drugs_related_stop", 0) == 1 else "NOT related to drugs"

    return (
        f"🚔 On **{stop_date}** at **{stop_time}**, a **{age}-year-old {gender} ({race})** "
        f"from **{country}** driving vehicle **{vehicle}** was stopped for **{violation}**.\n\n"
        f"✅ During the stop, **{search}**, and the incident was **{drug}**.\n\n"
        f"🕒 The stop lasted **{duration}**, and the final recorded outcome was **{outcome}**."
    )



#  Predefined Questions

QUESTION_LIST = [
    # Medium Level
    "Top 10 vehicle_Number involved in drug-related stops",
    "Which vehicles were most frequently searched?",
    "Which driver age group had the highest arrest rate?",
    "What is the gender distribution of drivers stopped in each country?",
    "Which race and gender combination has the highest search rate?",
    "What time of day sees the most traffic stops?",
    "What is the average stop duration for different violations?",
    "Are stops during the night more likely to lead to arrests?",
    "Which violations are most associated with searches or arrests?",
    "Which violations are most common among younger drivers (<25)?",
    "Is there a violation that rarely results in search or arrest?",
    "Which countries report the highest rate of drug-related stops?",
    "What is the arrest rate by country and violation?",
    "Which country has the most stops with search conducted?",

    # Complex Level
    "Yearly Breakdown of Stops and Arrests by Country (Using Subquery and Window Functions)",
    "Driver Violation Trends Based on Age and Race (Join with Subquery)",
    "Time Period Analysis of Stops (Joining with Date Functions)",
    "Violations with High Search and Arrest Rates (Window Function)",
    "Driver Demographics by Country (Age, Gender, and Race)",
    "Top 5 Violations with Highest Arrest Rates"
]


#  PAGE TITLE

st.title("🚔 Police Traffic Stop Dashboard — Modern View")


#  Dataset

st.header("📘 Complete Dataset")
st.dataframe(df, use_container_width=True)


#  Key Metrics (Modern Cards)

st.header("📊 Key Metrics")
c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"<div class='big-metric'>Total Records<br><h3>{len(df)}</h3></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='big-metric'>Total Arrests<br><h3>{df['is_arrested'].sum()}</h3></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='big-metric'>Drug Related<br><h3>{df['drugs_related_stop'].sum()}</h3></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='big-metric'>Searches<br><h3>{df['search_conducted'].sum()}</h3></div>", unsafe_allow_html=True)


#  Visual Insights (Bar Chart)

st.header("📈 Visual Insights")
vioc = df["violation"].value_counts().reset_index()
vioc.columns = ["violation", "count"]

bar = px.bar(vioc, x="violation", y="count", title="Most Common Violations", color="count")
st.plotly_chart(bar, use_container_width=True)



#  ADVANCED SQL INSIGHTS   

st.header("🚀 Advanced SQL Insights")

selected_q = st.selectbox("Choose a question", QUESTION_LIST)

# Mapping Question 
QUERY_MAP = {
    "Top 10 vehicle_Number involved in drug-related stops":
        "SELECT vehicle_number, COUNT(*) AS total FROM cleaned_traffic_stops "
        "WHERE drugs_related_stop = 1 GROUP BY vehicle_number ORDER BY total DESC LIMIT 10",

    "Which vehicles were most frequently searched?":
        "SELECT vehicle_number, COUNT(*) AS total FROM cleaned_traffic_stops "
        "WHERE search_conducted = 1 GROUP BY vehicle_number ORDER BY total DESC LIMIT 10",

    "Which driver age group had the highest arrest rate?":
        "SELECT driver_age, AVG(is_arrested)*100 AS arrest_rate FROM cleaned_traffic_stops "
        "GROUP BY driver_age ORDER BY arrest_rate DESC LIMIT 10",

    "What is the gender distribution of drivers stopped in each country?":
        "SELECT country_name, driver_gender, COUNT(*) AS total FROM cleaned_traffic_stops "
        "GROUP BY country_name, driver_gender ORDER BY total DESC",

    "Which race and gender combination has the highest search rate?":
        "SELECT driver_race, driver_gender, AVG(search_conducted)*100 AS search_rate "
        "FROM cleaned_traffic_stops GROUP BY driver_race, driver_gender ORDER BY search_rate DESC LIMIT 10",

    "What time of day sees the most traffic stops?":
        "SELECT HOUR(stop_time) AS hour, COUNT(*) AS total FROM cleaned_traffic_stops "
        "GROUP BY hour ORDER BY total DESC",

    "What is the average stop duration for different violations?":
        "SELECT violation, AVG(stop_duration) AS avg_duration FROM cleaned_traffic_stops "
        "GROUP BY violation ORDER BY avg_duration DESC",

    "Are stops during the night more likely to lead to arrests?":
        "SELECT IF(HOUR(stop_time) BETWEEN 18 AND 23, 'Night', 'Day') AS period, "
        "AVG(is_arrested)*100 AS arrest_rate FROM cleaned_traffic_stops GROUP BY period",

    "Which violations are most associated with searches or arrests?":
        "SELECT violation, AVG(search_conducted)*100 AS search_rate, AVG(is_arrested)*100 AS arrest_rate "
        "FROM cleaned_traffic_stops GROUP BY violation ORDER BY search_rate DESC LIMIT 10",

    "Which violations are most common among younger drivers (<25)?":
        "SELECT violation, COUNT(*) AS total FROM cleaned_traffic_stops WHERE driver_age < 25 "
        "GROUP BY violation ORDER BY total DESC LIMIT 10",

    "Is there a violation that rarely results in search or arrest?":
        "SELECT violation, AVG(search_conducted)*100 AS search_rate, AVG(is_arrested)*100 AS arrest_rate "
        "FROM cleaned_traffic_stops GROUP BY violation ORDER BY search_rate ASC LIMIT 10",

    "Which countries report the highest rate of drug-related stops?":
        "SELECT country_name, AVG(drugs_related_stop)*100 AS drug_rate FROM cleaned_traffic_stops "
        "GROUP BY country_name ORDER BY drug_rate DESC",

    "What is the arrest rate by country and violation?":
        "SELECT country_name, violation, AVG(is_arrested)*100 AS arrest_rate "
        "FROM cleaned_traffic_stops GROUP BY country_name, violation ORDER BY arrest_rate DESC LIMIT 15",

    "Which country has the most stops with search conducted?":
        "SELECT country_name, COUNT(*) AS total FROM cleaned_traffic_stops "
        "WHERE search_conducted = 1 GROUP BY country_name ORDER BY total DESC",

    # Complex
    "Yearly Breakdown of Stops and Arrests by Country (Using Subquery and Window Functions)":
        "SELECT country_name, YEAR(stop_date) AS year, COUNT(*) AS total_stops, "
        "SUM(is_arrested) AS arrests FROM cleaned_traffic_stops "
        "GROUP BY country_name, year ORDER BY year DESC",

    "Driver Violation Trends Based on Age and Race (Join with Subquery)":
        "SELECT driver_age, driver_race, COUNT(*) AS total FROM cleaned_traffic_stops "
        "GROUP BY driver_age, driver_race ORDER BY total DESC LIMIT 20",

    "Time Period Analysis of Stops (Joining with Date Functions)":
        "SELECT YEAR(stop_date) AS year, MONTH(stop_date) AS month, COUNT(*) AS total "
        "FROM cleaned_traffic_stops GROUP BY year, month ORDER BY year DESC, month DESC",

    "Violations with High Search and Arrest Rates (Window Function)": 
        "SELECT violation, AVG(search_conducted)*100 AS search_rate, AVG(is_arrested)*100 AS arrest_rate "
        "FROM cleaned_traffic_stops GROUP BY violation ORDER BY arrest_rate DESC LIMIT 10",

    "Driver Demographics by Country (Age, Gender, and Race)":
        "SELECT country_name, driver_age, driver_gender, driver_race, COUNT(*) AS total "
        "FROM cleaned_traffic_stops GROUP BY country_name, driver_age, driver_gender, driver_race "
        "ORDER BY total DESC LIMIT 20",

    "Top 5 Violations with Highest Arrest Rates":
        "SELECT violation, AVG(is_arrested)*100 AS arrest_rate FROM cleaned_traffic_stops "
        "GROUP BY violation ORDER BY arrest_rate DESC LIMIT 5"
}

# RUN BUTTON
if st.button("▶ Run Insight"):
    st.success(f"✅ Insight for: **{selected_q}**")

    query = QUERY_MAP[selected_q]
    db = connect_db()
    result_df = pd.read_sql(query, db)

    #  SHOW TABLE
    st.dataframe(result_df, use_container_width=True)

    st.info("📌 Insight based on dataset patterns has been shown above.")



#  Natural Language Insights

st.header("💬 Natural Language Insights")
nl_q = st.selectbox("Select a question", QUESTION_LIST)
st.info(f"✅ This explains: **{nl_q}**")



#  Add New Police Log 
st.header("🆕 Add New Police Log — Rule-Based Prediction")

id_val = st.number_input("Enter ID from dataset", min_value=1, step=1)

row = None
if id_val:
    found = df[df["id"] == id_val]
    if len(found) > 0:
        row = found.iloc[0]
        st.success("✅ Auto-filled successfully!")
    else:
        st.warning("❌ ID not found.")

if row is not None:
    colA, colB, colC = st.columns(3)

    stop_date = colA.text_input("Stop Date", str(row["stop_date"]))
    stop_time = colB.text_input("Stop Time", str(row["stop_time"]))
    country = colC.text_input("Country", row["country_name"])

    gender = colA.text_input("Driver Gender", row["driver_gender"])
    age = colB.number_input("Driver Age", value=int(row["driver_age"]))
    race = colC.text_input("Driver Race", row["driver_race"])

    violation = colA.text_input("Violation", row["violation"])
    search = colB.number_input("Search Conducted (0/1)", value=int(row["search_conducted"]))
    search_type = colC.text_input("Search Type", row["search_type"])

    outcome = colA.text_input("Outcome", row["stop_outcome"])
    arrested = colB.number_input("Arrested (0/1)", value=int(row["is_arrested"]))
    duration = colC.text_input("Stop Duration", row["stop_duration"])

    drug = colA.number_input("Drug Related (0/1)", value=int(row["drugs_related_stop"]))
    vehicle = colB.text_input("Vehicle Number", row["vehicle_number"])
    timestamp = colC.text_input("Timestamp", str(row["timestamp"]))

    if st.button("🔮 Predict Outcome & Violation"):
        st.info(generate_dynamic_insight(row))
        st.success("✅ Additional Interpretation Provided!")







