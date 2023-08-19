import sqlite3
import pandas as pd
from datetime import datetime, timedelta,timezone,time
from pytz import timezone
from flask import Flask, jsonify, request, render_template, send_from_directory
from concurrent.futures import ThreadPoolExecutor
import multiprocessing, threading
import io
from flask_cors import CORS  # Import the CORS module

# Step 1: Load data into SQLite database

# Function to create and populate the SQLite tables
def load_data_into_database():
    # Connect to the database
    conn = sqlite3.connect('store_monitoring.db')
    cursor = conn.cursor()

    # Load CSV data into pandas DataFrames
    data_source1 = pd.read_csv('data_source1.csv')
    data_source2 = pd.read_csv('data_source2.csv')
    data_source3 = pd.read_csv('data_source3.csv')

    # Create tables and load data into them
    data_source1.to_sql('data_source1', conn, if_exists='replace', index=False)
    data_source2.to_sql('data_source2', conn, if_exists='replace', index=False)
    data_source3.to_sql('data_source3', conn, if_exists='replace', index=False)

    # Close the connection
    conn.close()

# Load the data into the database
load_data_into_database()




def get_store_timezone(store_id):
    # Connect to the database
    conn = sqlite3.connect('store_monitoring.db')
    cursor = conn.cursor()

    # Get the store timezone from data_source3
    cursor.execute("SELECT timezone_str FROM data_source3 WHERE store_id=?", (store_id,))
    timezone = cursor.fetchone()

    # If data is missing for a store, assume it is America/Chicago
    store_timezone = timezone[0] if timezone else 'America/Chicago'

    # Close the connection
    conn.close()

    return store_timezone

def get_business_hours(store_id, day_of_week):
    # Connect to the database
    conn = sqlite3.connect('store_monitoring.db')
    cursor = conn.cursor()

    # Get the start and end time of business hours in local time
    cursor.execute("SELECT start_time_local, end_time_local FROM data_source2 WHERE store_id=? AND day=?", (store_id, day_of_week))
    business_hours = cursor.fetchone()

    # If data is missing for a store on a particular day, assume it is open 24*7
    if business_hours:
        start_time_local, end_time_local = business_hours
        #print('dsg')
    else:
        start_time_local = time.min
        end_time_local = time.max
    conn.close()
    #print(type(start_time_local))
    if type(start_time_local) is str:
        start_time_local= datetime.strptime(start_time_local,"%H:%M:%S").time()
        #print(type(start_time_local))
    if type(end_time_local) is str:    
        end_time_local= datetime.strptime(end_time_local,"%H:%M:%S").time()
    return start_time_local, end_time_local

def local_to_utc(local_time, local_timezone):
    tz = timezone(local_timezone)
    local_time = tz.localize(local_time)
    local_time=local_time.astimezone(timezone('UTC'))
    if type(local_time) is str:
       local_time = datetime.strptime(local_time, "%Y-%m-%d %H:%M:%S.%f UTC")
    return local_time
def calculate_uptime_downtime_for_a_period(store_id, current_start_time_utc,current_end_time_utc):
    current_start_time_utc=current_start_time_utc.astimezone(timezone('UTC'))
    current_end_time_utc=current_end_time_utc.astimezone(timezone('UTC'))
    local_timezone = get_store_timezone(store_id)  # Get the local timezone for the store
    day_of_week = current_start_time_utc.weekday()

    # Get the start and end time of business hours in local time
    start_time_local, end_time_local = get_business_hours(store_id, day_of_week)
    #print('direct busicness')
    if start_time_local is None or end_time_local is None:
        # If data is missing for a store on a particular day, assume it is open 24*7
        start_time_local = time.min
        end_time_local = time.max
        #print('g2 insdie if')

    #print(type(current_start_time_utc.date()), type(start_time_local))
    start_time_utc = local_to_utc(datetime.combine(current_start_time_utc.date(), start_time_local), local_timezone)
    end_time_utc = local_to_utc(datetime.combine(current_start_time_utc.date(), end_time_local), local_timezone)
    #print(type(current_start_time_utc), type(start_time_utc))
    if type(start_time_utc) is str:
        start_time_utc = datetime.strptime(start_time_utc, "%Y-%m-%d %H:%M:%S.%f UTC")
    if type(end_time_utc) is str:
        end_time_utc = datetime.strptime(end_time_utc, "%Y-%m-%d %H:%M:%S.%f UTC")
    valid_first_point= max( current_start_time_utc, start_time_utc)
    valid_last_point = min(current_end_time_utc,end_time_utc)
    if valid_last_point<= valid_first_point:
        return 0,0

    conn = sqlite3.connect('store_monitoring.db')
    cursor = conn.cursor()
    # Get all store statuses within the valid_first_point and valid_last_point window
    cursor.execute("SELECT timestamp_utc, status FROM data_source1 WHERE store_id=? AND timestamp_utc BETWEEN ? AND ?ORDER BY timestamp_utc",
                   (store_id, valid_first_point.strftime("%Y-%m-%d %H:%M:%S.%f UTC"), valid_last_point.strftime("%Y-%m-%d %H:%M:%S.%f UTC")))
    status_data = cursor.fetchall()

    prev_status_time = start_time_utc
    prev_status = "active"

    # Get the store status just before valid_first_point
    if valid_first_point != start_time_utc:
      cursor.execute("SELECT timestamp_utc, status FROM data_source1 WHERE store_id=? AND timestamp_utc < ? ORDER BY timestamp_utc DESC LIMIT 1",
                    (store_id, str(current_start_time_utc)))
      prev_status_data = cursor.fetchone()
      #print('gokul',prev_status_data,current_start_time_utc)
      if prev_status_data:
        if type(prev_status_data[0]) is str:
            prev_status_time = datetime.strptime(prev_status_data[0], "%Y-%m-%d %H:%M:%S.%f UTC")
            prev_status_time=prev_status_time.astimezone(timezone('UTC'))
        prev_status = prev_status_data[1]
        #if just left timestamp for valid_first_point is 1.5hours away from valid_first_point, then we will take status as active,
        #since this is inside business timings and we can't rely on timestamp which is 1.5hrs far.
        if valid_first_point- prev_status_time>= timedelta(hours=1.5):
            prev_status= "active"
      else:
         prev_status= 'active'

    uptime = 0
    downtime = 0
    prev_time= valid_first_point

    # Calculate uptime and downtime based on the status data
    flag=0
    #to take care of last part i.e valid_last_point and it's previous time stamp, we are appending valid_last_point in status_data
    status_data=list(status_data)
    status_data.append((valid_last_point,'active'))
    for timestamp, status in status_data:
      if type(timestamp) is str:
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f UTC")
        timestamp=timestamp.astimezone(timezone('UTC'))

      if flag==0:
        flag=1
        prev_time= timestamp
        if prev_status== "active":
          uptime += (timestamp -valid_first_point).total_seconds()
        else:
          downtime += (timestamp - valid_first_point).total_seconds()
        prev_status= status
        continue
      #other than 1st part
      #if diff btw 2 consecutive elements is more than 1.5hrs, then 1st status will be there for 1hr, and
      #remaining time is 'active' whatever the suitation is. because this is within business hours
      if timestamp - prev_time>= timedelta(hours=1.5):
        if prev_status== "active":
            uptime += (timestamp - prev_time).total_seconds()
        else:
            downtime += (timedelta(hours=1)).total_seconds()
            uptime += (timestamp - prev_time-timedelta(hours=1)).total_seconds()

      else:
        if prev_status== "active":
            uptime += (timestamp - prev_time).total_seconds()
        else:
            downtime += (timestamp - prev_time).total_seconds()
      prev_time,prev_status= timestamp, status

    # Convert uptime and downtime to minutes
    uptime_last_hour = round(uptime/60, 2)
    downtime_last_hour= round(downtime/60,2)

    conn.close()
    #return in minutes
    return uptime_last_hour,downtime_last_hour


def calculate_uptime_last_hour(store_id, current_time_utc):

    uptime_last_hour,downtime_last_hour= calculate_uptime_downtime_for_a_period(store_id, current_time_utc-timedelta(hours=1), current_time_utc)
    return uptime_last_hour,downtime_last_hour


def calculate_uptime_last_day(store_id, current_time_utc):

    # Split the last 24 hours into two parts: the part before the current day and the part of the current day
    previous_day_start_time = current_time_utc - timedelta(days=1)
    current_day_start_time = datetime.combine(current_time_utc.date(), time.min)
    current_day_end_time = datetime.combine(current_time_utc.date(), time.max)

    # Calculate uptime and downtime for the previous day and the current day
    uptime_previous_day, downtime_previous_day = calculate_uptime_downtime_for_a_period(store_id, previous_day_start_time, current_day_start_time-timedelta(minutes=1))
    uptime_current_day, downtime_current_day = calculate_uptime_downtime_for_a_period(store_id, current_day_start_time, current_day_end_time)

    # total uptime and downtime for the last 24 hours
    total_uptime = uptime_previous_day + uptime_current_day
    total_downtime = downtime_previous_day + downtime_current_day

    # Convert uptime and downtime to hours
    uptime_hours = round(total_uptime /60, 2)
    downtime_hours = round(total_downtime /60, 2)

    return uptime_hours, downtime_hours

    #fgrdf

def calculate_uptime_last_week(store_id, current_time):
    uptime_hours, downtime_hours= 0,0
    for i in range(7):
        a,b= calculate_uptime_last_day(store_id, current_time-timedelta(days=i))
        uptime_hours+=a
        downtime_hours+=b
    uptime_hours = round(uptime_hours, 2)
    downtime_hours = round(downtime_hours, 2)
    return uptime_hours, downtime_hours

def calculate_uptime_downtime(store_id, current_time):
    uptime_last_hour, downtime_last_hour = calculate_uptime_last_hour(store_id, current_time)
    uptime_last_day, downtime_last_day = calculate_uptime_last_day(store_id, current_time)
    uptime_last_week, downtime_last_week = calculate_uptime_last_week(store_id, current_time)
    return store_id, uptime_last_hour, uptime_last_day, uptime_last_week, downtime_last_hour, downtime_last_day, downtime_last_week



# Function to generate the final report
def generate_report(current_time='0000-00-00 00:09:30.3 UTC'):
    # start_time = datetime.now()
    # while (datetime.now() - start_time).total_seconds() < 10:
    #     pass
    conn = sqlite3.connect('store_monitoring.db')
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT store_id FROM data_source1")
    store_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT MAX(timestamp_utc) FROM data_source1")
    
    max_timestamp = cursor.fetchone()[0]
    if current_time=="0000-00-00 00:09:30.3 UTC":
      current_time= max_timestamp
    if type(current_time) is str:
        current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S.%f UTC")
    #print('gokul',current_time)
    report = []
    for store_id in store_ids:
        store_report = calculate_uptime_downtime(store_id, current_time)    
        report.append(store_report)

    conn.close()

    # Return the report as a DataFrame
    report_df = pd.DataFrame(report, columns=['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week',
                                               'downtime_last_hour', 'downtime_last_day', 'downtime_last_week'])
    return report_df

# Generate and print the final report
#final_report = generate_report()
#print(final_report)


app = Flask(__name__)
CORS(app) 
# Connect to the SQLite database
conn = sqlite3.connect('reports.db')
cursor = conn.cursor()

# Create the reports table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        status TEXT,
        data BLOB
    )
''')
conn.commit()
db_lock = threading.Lock()
# Function to save the report to a CSV file
def save_report_to_csv(report_df, report_id):
    filename = f"report_{report_id}.csv"
    report_df.to_csv(filename, index=False)
    return filename


# Serve React app's index.html
@app.route('/')
def serve_react_app():
    return send_from_directory('front_end_view/public', 'index.html')
# API to trigger report generation
@app.route('/trigger_report', methods=['GET'])
def trigger_report():
    # Generate a unique report_id using the current date and time
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    report_id = current_time + ".csv"
    conn = sqlite3.connect('reports.db')
    cursor = conn.cursor()    
    cursor.execute('INSERT INTO reports (report_id, status) VALUES (?, ?)', (report_id, 'Running'))
    conn.commit()
    
    #report_df = generate_report()
    #report_data = report_df.to_csv(index=False)
    #cursor.execute('UPDATE reports SET status=?, data=? WHERE report_id=?', ('Complete', report_data, report_id))
    #conn.commit()

    # Trigger report generation using multiprocessing.Pool
    #with ThreadPoolExecutor() as executor:
       # future = executor.submit(generate_report_background, report_id)
    threading.Thread(target=generate_report_background,args=(report_id,)).start()
    return jsonify({"report_id": report_id})

def update_report_status(report_id, report_df):
    conn = sqlite3.connect('reports.db')
    cursor = conn.cursor()    
    print('step1')
    report_data = report_df.to_csv(index=False)
    cursor.execute('UPDATE reports SET status=?, data=? WHERE report_id=?', ('Complete', report_data, report_id))
    print('step2')
    conn.commit()
    # Fetch the updated status from the database
    cursor.execute('SELECT data FROM reports WHERE report_id=?', (report_id,))
    updated_status = cursor.fetchone()[0]
    print(f"Updated status for report_id '{report_id}': {updated_status}")


# Function to generate the report in the background
def generate_report_background(report_id):
    current_time= datetime.now().strftime('%Y%m%d%H%M%S')
    #print('gokul',current_time)
    conn = sqlite3.connect('reports.db')
    cursor = conn.cursor()  
    cursor.execute('SELECT status FROM reports WHERE report_id=?', (report_id,))
    updated_status = cursor.fetchone()[0]
    print(f"Updated status for report_id '{report_id}': {updated_status}")
    c= datetime.utcnow()
    report_df = generate_report(c)
    print("comp;;")
    update_report_status(report_id, report_df)

# API to get report status or download the CSV file
@app.route('/get_report', methods=['GET'])
def get_report():
    report_id = request.args.get('report_id')
    conn = sqlite3.connect('reports.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status, data FROM reports WHERE report_id=?', (report_id,))
    row = cursor.fetchall()

    if row:
        status, data = row[0][0],row[0][1]
        if status == 'Running':
            return jsonify({"status": "Running"})

        elif status == 'Complete':
            report_df = pd.read_csv(io.StringIO(data))
            report_data = report_df.to_dict(orient='records')  # Convert DataFrame to a list of dictionaries
            return jsonify({"status": "Complete", "csv_data": report_data})

    else:
        return jsonify({"status": "Invalid report_id"})

if __name__ == '__main__':
    app.run(debug=True)
