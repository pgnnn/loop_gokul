There are many ways to calculate uptime and downtime, I have calculated in a way That for example, consecutive timestamps in data_source1.csv (i.e contains a status for roughly one hour for each store) are 9am 'active', 10:12am 'inactive', 1:10pm 'inactive' ;;business_hours for this store is 8am to 2pm. In this case, I have taken 8am to 9am as 'active' since this is inside business_hours 9am to 10:12am status as 'active', 10:12am to 11:12am as 'inactive', 11:12am to 1:10pm as 'active' since we don't have data in between, 1:10pm to 2pm as 'inactive'.

My idea to calculate uptime and downtime (nearest neighbor with limitation)

a) status of timestamp t1 will be continued till the next timestamp only if the next timestamp is within 1.5hrs, else I gonna take t1 status as status from t1 to t1+1hour and status from t1+1hour to next timestamp as 'active' only if next timestamp is within business hours else 'active' till the end of business_hours

b) why 1.5hr instead of 1hr is there will be some delta while taking the status of restaurants for roughly 1hour.

below are my 5 ideas which I tried to assign a status for missing points (in the sense if 2 consecutive timestamps of a store are differ more than 1hr or 1.5hr, then there will be missing points eg: if we have status at 6am and 8:20am, missing point is around 7am.)

greedy nearest neighbor interpolation (status of missing point = status of the nearest point)
by finding a polynomial Function that fits all points and finding y value for the missing x value. (y= status and x=timestamp)
by using machine learning
center of mass approach (like calculating status at missing point by taking an average of status which are present within some 'k' hours frame from missing point and weights as the distance from that missing point to remaining points)
nearest neighbor with limitation (my approach)
reason for rejections: In 1, even if the missing point and next available timestamps are so far, it will take status as the status of next available timestamp, which is not at all accurate.

in 2, polynomial function may be correct if we have fewer points and values of y are multiple integers. but here we have many points and y value(status) is either 1 or 0. so, there will be many turns in the graph that will give inappropriate equation.

In 3, the given data is only for a week, but we need more data to find some patterns in the data because there may be some similarities between the same day in every week for example 'happy hours' will be there for every "Thrusday' for a restaurant etc, so we can't give missing value based on data of other days in given week data.

In 4, this is a good approach but it will take more "time Complexity".

#################################################################################################################

data_source1.csv contains status of the stores data_source2.csv contains business hours of all the stores data_source3.csv contains Timezone for the stores

functions.py contains the whole code

Take home interview - Store Monitoring
This will be a take-home interview that tests real-life problem-solving ability, ability to build something from scratch and handle complex algorithmic problems.

Problem statement
Loop monitors several restaurants in the US and needs to monitor if the store is online or not. All restaurants are supposed to be online during their business hours. Due to some unknown reasons, a store might go inactive for a few hours. Restaurant owners want to get a report of the how often this happened in the past.

We want to build backend APIs that will help restaurant owners achieve this goal.

We will provide the following data sources which contain all the data that is required to achieve this purpose.

Data sources
We will have 3 sources of data

We poll every store roughly every hour and have data about whether the store was active or not in a CSV. The CSV has 3 columns (store_id, timestamp_utc, status) where status is active or inactive. All timestamps are in UTC
Data can be found in CSV format here
We have the business hours of all the stores - schema of this data is store_id, dayOfWeek(0=Monday, 6=Sunday), start_time_local, end_time_local
These times are in the local time zone
If data is missing for a store, assume it is open 24*7
Data can be found in CSV format here
Timezone for the stores - schema is store_id, timezone_str
If data is missing for a store, assume it is America/Chicago
This is used so that data sources 1 and 2 can be compared against each other.
Data can be found in CSV format here
System requirement
Do not assume that this data is static and precompute the answers as this data will keep getting updated every hour.
You need to store these CSVs into a relevant database and make API calls to get the data.
Data output requirement
We want to output a report to the user that has the following schema

store_id, uptime_last_hour(in minutes), uptime_last_day(in hours), update_last_week(in hours), downtime_last_hour(in minutes), downtime_last_day(in hours), downtime_last_week(in hours)

Uptime and downtime should only include observations within business hours.
You need to extrapolate uptime and downtime based on the periodic polls we have ingested, to the entire time interval.
eg, business hours for a store are 9 AM to 12 PM on Monday
we only have 2 observations for this store on a particular date (Monday) in our data at 10:14 AM and 11:15 AM
we need to fill the entire business hours interval with uptime and downtime from these 2 observations based on some sane interpolation logic
Note: The data we have given is a static data set, so you can hard code the current timestamp to be the max timestamp among all the observations in the first CSV.

API requirement
You need two APIs
/trigger_report endpoint that will trigger report generation from the data provided (stored in DB)
No input
Output - report_id (random string)
report_id will be used for polling the status of report completion
/get_report endpoint that will return the status of the report or the csv
Input - report_id
Output
if report generation is not complete, return “Running” as the output
if report generation is complete, return “Complete” along with the CSV file with the schema described above.
Considerations/Evaluation criteria
The code should be well structured, handling corner cases, with good type systems.
The functionality should be correct for trigger + poll architecture, database reads and CSV output.
The logic for computing the hours overlap and uptime/downtime should be well documented and easy to read/understand.
The code should be as optimized as people and run within a reasonable amount of time.
You can use any Python framework to build this.

Submission instructions
Send us the following in the same thread

Github link to the repo
Loom/any other screen-sharing video of a demo of the functionality
We will get back on the next steps.
