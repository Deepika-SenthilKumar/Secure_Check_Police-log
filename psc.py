import streamlit as st
import pymysql
import pandas as pd

#Database connection
def create_connection():
    try:
        connection = pymysql.connect(
        host="localhost",
        user='root',
        password='1234',
        database='securitycheck',
        cursorclass=pymysql.cursors.DictCursor
             )
        return connection
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None 
    
#fetch data from database
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result= cursor.fetchall()
                df = pd.DataFrame(result)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
    

#------------------ Streamlit Page Config ------------------
st.set_page_config(page_title="Traffic Stops Dashboard", layout="wide")

st.title("Secure Check: Police Check Post Digital Ledger")
st.markdown("Law Enforcement & Public Safety Real-time Monitoring Systems")

#-------------------show table------------------------------ 
st.header("Police Security Check Data")
query="SELECT * FROM traffic"
data=fetch_data(query)
#st.dataframe(data, use_container_width= True)
st.dataframe(data)

#------------------------QUICK TABLE------------------------
st.header("Quick Traffic Data Overview")

col1,col2,col3,col4 = st.columns(4)

with col1:
    total_stops= data.shape[0]
    st.metric("Total Stops by police", total_stops)

with col2:
    arrests=data[data['stop_outcome'].str.contains('Arrest',case=False,na=False)].shape[0]
    st.metric("Total Arrests", arrests)

with col3:
    warning=data[data['stop_outcome'].str.contains('warning',case=False,na=False)].shape[0]
    st.metric("Total warning", warning)

with col4:
    drugs_related_stop=data[data [ 'drugs_related_stop'] == '1'].shape[0]
    st.metric("Total drug_related", drugs_related_stop)


#--------------------------list of query------------------------------

st.header("Traffic Stops queries")
select_query=st.selectbox("Select Query to run ",[
    "Top 10 vehicle numbers in drug-related stops",
    "Vehicles most frequently searched",
    "Driver age group with highest arrest rate",
    "Gender distribution by country",
    "Race & gender combination with highest search rate",
    "Most traffic stops by hour",
    "Average stop duration by violation",
    "Night stops leading to arrests",
    "Violations associated with searches/arrests",
    "Violations most common among drivers <25",
    "Violations rarely resulting in search/arrest",
    "Countries with highest drug-related stops",
    "Arrest rate by country & violation",
    "Country with most stops with search conducted",

    "Yearly breakdown of stops & arrests by country",
    "Driver violation trends by age & race",
    "Time period analysis of stops (Year/Month/Hour)",
    "Top 5 violations with highest arrest rates",
    "Driver Demographics",
    "Top 5 violation with highest arrest",

])

query_map = {
    "Top 10 vehicle numbers in drug-related stops":
            """SELECT vehicle_number , count(*) as count
             FROM traffic
             WHERE drugs_related_stop = 1 
             GROUP BY vehicle_number 
             ORDER BY count DESC LIMIT 10""",
    "Vehicles most frequently searched":
            """SELECT vehicle_number, AVG(search_conducted=1) AS search_rate
             FROM traffic
             GROUP BY vehicle_number 
             ORDER BY search_rate DESC LIMIT 10""",

    "Driver age group with highest arrest rate":
            """SELECT driver_age, MAX(is_arrested='1') AS arrest_rate ,count(*) AS total_stops
             FROM traffic
             GROUP BY driver_age
             ORDER BY total_stops DESC""",

    "Gender distribution by country":
            """SELECT country_name, driver_gender, COUNT(*) AS count 
             FROM traffic
             GROUP BY country_name, driver_gender""",

    "Race & gender combination with highest search rate":
            """SELECT driver_race, driver_gender, MAX(search_conducted='1') as search_conduct,
             count(*) AS search_rate
             FROM traffic
             GROUP BY driver_race, driver_gender 
             ORDER BY search_rate DESC LIMIT 1""",

    "Most traffic stops by hour":
            """SELECT HOUR(stop_time) AS hour, COUNT(*) AS stops 
             FROM traffic
             GROUP BY hour 
             ORDER BY stops DESC""",

    "Average stop duration by violation":
            """SELECT violation, AVG(stop_duration) AS avg_duration 
             FROM traffic
             GROUP BY violation 
             ORDER BY avg_duration DESC""",

    "Night stops leading to arrests":
            """SELECT MAX(is_arrested='1') AS arrest_rate ,
             HOUR(stop_time) AS hour, COUNT(*) AS total_arrest_rate
             FROM traffic
             WHERE HOUR(stop_time) >= 12 AND HOUR(stop_time) <= 23
             GROUP BY HOUR(stop_time)
             ORDER BY arrest_rate DESC""",

    "Violations associated with searches/arrests":
            """select violation, 
             count(*) as total_arrest 
             from traffic
             where stop_outcome like 'arrest' group by violation""",

    "Violations most common among drivers <25":
            """SELECT violation, COUNT(*) AS count 
             FROM traffic
             WHERE driver_age < 25 
             GROUP BY violation 
             ORDER BY count DESC""",
            

    "Violations rarely resulting in search/arrest":
            """select violation, 
             count(*) as count, 
             SUM(CASE WHEN search_conducted = True then 1 else 0 end) as total_search, 
             SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests 
             from traffic group by violation""",

    "Countries with highest drug-related stops":
            """SELECT country_name, COUNT(*) AS count 
             FROM traffic
             WHERE drugs_related_stop='1'
             GROUP BY country_name 
             ORDER BY count DESC""",

    "Arrest rate by country & violation":
            """SELECT country_name, violation, AVG(is_arrested='1') AS arrest_rate 
             FROM traffic
             GROUP BY country_name, violation 
             ORDER BY arrest_rate DESC""",

    "Country with most stops with search conducted":
            """SELECT country_name, COUNT(*) AS count 
             FROM traffic
             WHERE search_conducted='1' 
             GROUP BY country_name 
             ORDER BY count DESC""",

    "Yearly breakdown of stops & arrests by country":
            """SELECT country_name,year,stops,arrest_rate
            FROM (
            SELECT country_name,YEAR(stop_date) AS year,COUNT(*) AS stops,
            AVG(CASE WHEN is_arrested = '1' THEN 1.0 ELSE 0.0 END) AS arrest_rate
            FROM traffic
            GROUP BY country_name, YEAR(stop_date)
            ) AS yearly_stats 
            ORDER BY year ASC"""
,

    "Driver violation trends by age & race":
           
            
            """WITH ViolationSummary AS (
            SELECT
                driver_age,driver_race,violation,COUNT(*) AS count
            FROM
                traffic
            GROUP BY
                driver_age,driver_race,violation
            )
            SELECT
            vs.driver_age,vs.driver_race,vs.violation,vs.count,
            SUM(vs.count) OVER (PARTITION BY vs.driver_race) AS total_by_race
            FROM
                ViolationSummary vs
            ORDER BY
                vs.count DESC""",


    "Time Period Analysis of Stops (Joining with Date Functions), Number of Stops by Year, Month, Hour of the Day": 
                """select 
                 year(stop_date) as stop_year, month(stop_date) as stop_month, hour(stop_time) as stop_hour, count(*) as Number_of_stops
                 from traffic
                 group by 
                 stop_year, stop_month, stop_hour""",
    
    "Violations with High Search and Arrest Rates (Window Function)":
                """select 
                violation, count(*) as total_stops, 
                sum(case when search_conducted = True then 1 else 0 end) as total_search, 
                sum(case when is_arrested = True then 1 else 0 end) as total_arrest, 
                rank() over (order by sum(case when search_conducted = True then 1 else 0 end)* 1.0 / Count(*)) as search, 
                rank() over (order by sum(case when is_arrested = True then 1 else 0 end)* 1.0/ count(*)) as arrest 
                from traffic 
                group by violation""",
    
    "Driver Demographics by Country (Age, Gender, and Race)": 
                """select 
                 country_name, driver_age, driver_gender, driver_race, count(*) as total_drivers
                 from traffic
                 group by country_name, driver_age, driver_gender, driver_race
                 order by country_name, driver_age, driver_gender, driver_race""",
    
    "Top 5 Violations with Highest Arrest Rates": 
                """select violation, count(*) as total_stops, 
                 sum(case when is_arrested = True then 1 else 0 end) as total_arrest, 
                 round(sum(case when is_arrested = True then 1 else 0 end) *1.0/ count(*), 2) as arrest_rate 
                 from traffic
                 group by violation order by total_arrest desc limit 5"""
}

    
if st.button("Run Query"):
    result= fetch_data(query_map[select_query])
    if not result.empty:
       st.write(result)
    else:
        st.warning("No data found for the selected query.")

#-----------------------------------------Input form--------------------------------------
st.header("add police log to predict outcome and violation")

with st.form("police_log_form"):
    stop_date= st.date_input("Stop Date")
    stop_time= st.time_input("Stop Time")   
    country_name= st.text_input("Country Name")
    driver_gender= st.selectbox("Driver Gender",["M","F"])
    driver_age= st.number_input("Driver Age",min_value=16,max_value=100,value=27)
    driver_race= st.selectbox("Driver Race",["White","Black","Hispanic","Asian","Other"])
    violation_raw= st.selectbox("Driver Violation",["Speeding","Drunk Driving","Seatbelt","Signal Violation","Other"])
    search_conducted= st.selectbox("Search Conducted",[0,1])
    search_type= st.selectbox("Search Type",["None","Vehicle Search","Frisk"])
    stop_outcome= st.selectbox("Stop Outcome",["Ticket","Warning","Arrest"])
    drugs_related_stop= st.selectbox("Drugs Related Stop",[0,1])   
    is_arrested= st.selectbox("Is Arrested",[0,1])
    stop_duration= st.number_input("Stop Duration (in minutes)",min_value=1,max_value=300,value=15) 
    violation_type= st.selectbox("Violation Type",["Speeding","DUI","Seatbelt","Equipment","Other"])
    vehicle_number= st.text_input("Vehicle Number")

    timestamp= pd.Timestamp.now()

    submitted= st.form_submit_button("Submit Log")

    if submitted:

        filtered_data= data[
           (data['driver_gender'] == (driver_gender)) &
            (data['driver_age'] ==int( driver_age)) &
            (data['search_conducted'] == int(search_conducted)) &
            (data['stop_duration'] == int(stop_duration)) &
            (data['drugs_related_stop'] == int(drugs_related_stop))
        ]

        # ----------------------Predict stop outcome-----------------------
        if not filtered_data.empty:
            predicted_outcome = filtered_data['stop_outcome'].mode()[0]
            predicted_violation = filtered_data['violation'].mode()[0]
        else:
            predicted_outcome = "Warning" 
            predicted_violation = "Speeding"

        #--------------------------------Insight-----------------------------------
        search_text = "A Search was Conducted" if int(search_conducted) else "No search was conducted"
        drug_text = "was drug_related" if int(drugs_related_stop) else "was not drug_related"

        st.markdown(f"""
                    **Prediction Summary**
                    - **Predicted Violation:** {predicted_violation}
                    - **Predicted Stop Outcome:** {predicted_outcome}
                    
                    A A  **{driver_age}**-year-old **{driver_gender}**
                    driver in **{ country_name}** was stopped at **{stop_time.strftime('%I:%M%p')}** on **{stop_date}**. 
                    **{search_text}**, and the stop **{drug_text}**.
                    
                    stop duration: **{stop_duration}**.

                    Vehicle Number: **{vehicle_number}**.
                    """)



