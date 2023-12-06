# ! pip install pylotoncycle
# import pylotoncycle
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import datetime
import streamlit as st
from PIL import Image
from plotnine import *

st.set_page_config(layout       = 'wide', 
                   page_title   = 'Peloton Statistics' ,
                   menu_items   = {'Get Help': None, 'Report a bug': None, 'About': None},
                   page_icon    = ':bike')

username = 'scothomas24@me.com'
data = pd.read_pickle("peloton_data.pkl")

# convert to dataframe, format dates      
data = pd.DataFrame(data).drop_duplicates()
data['date'] = pd.to_datetime(data['date'], unit='s').dt.date
data['date'] = pd.to_datetime(data['date'])
data = data[data['difficulty_rating'] != 0]
data['ride_time'] = data[['ride_time']] \
    .assign(ride_time = lambda x: x['ride_time'] / 60)

data['difficulty'] = \
    pd.cut(
        data.difficulty_rating, 
        bins = [0, 3, 4, 5, 6, 7, 8, 9, 10], 
        labels=['0-3', '3', '4', '5', '6', '7', '8', '9']
    )  
    
data = data.assign(leaderboard_pct = 
    1 - (data['leaderboard_rank'] / data['leaderboard_users'])
    ) 

st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)

st.image(image=Image.open('Peloton-Logo.jpeg').resize((300,170)))

st.write(f"User: {username} Cycling Analysis")
st.write("First Ride: ", data['date'].min().strftime(format= "%Y-%m-%d"))

# st.header(":bike:")

# st.sidebar.image(image=Image.open('peloton_logo2.png').resize((100,100)))
st.sidebar.header("Select Filters")

date1 = pd.to_datetime(st.sidebar.date_input("Start Date", data.date.min()))
date2 = pd.to_datetime(st.sidebar.date_input("End Date", data.date.max()))

selected_instructor = st.sidebar.multiselect(
    'Instructor', 
    np.append(data['instructor'].unique(), ["All"]), 
    default="All"
    )
selected_difficulty = st.sidebar.multiselect(
    'Difficulty', 
    np.append(data['difficulty'].unique(),['All'] ), 
    default="All"
    )
selected_ride_time = st.sidebar.multiselect(
    'Ride Time', 
    np.append(data['ride_time'].unique().astype(str), ['All']), 
    default="All"
    )

if "All" in selected_instructor:
    selected_instructor = data['instructor'].unique()

if "All" in selected_difficulty:
    selected_difficulty = data['difficulty'].unique()

#All Ride Times not working
if "All" in selected_ride_time:
    selected_ride_time = data['ride_time'].unique().astype(str)

data_filtered = data[
    (data.instructor.isin(selected_instructor) & 
     data.difficulty.isin(selected_difficulty) &
     data.ride_time.astype(str).isin(selected_ride_time) &
     (data.date >= date1) &
     (data.date <= date2)
     )]

most_difficult_ride = data_filtered[data_filtered['difficulty_rating'] == 
     data_filtered['difficulty_rating'].max()][['instructor', 'title','difficulty_rating']] \
    .drop_duplicates()

leaderboard_pct_by_instructor = data_filtered \
        .groupby('instructor') \
        .agg({'leaderboard_pct': np.mean}) \
        .reset_index() \
        .sort_values('leaderboard_pct', ascending = False)

tab1, tab2, tab3 = st.tabs(["Summary", "Charts", "Raw Data"])

with tab1:
    st.header("", divider='red')
    
    col1, col2 = st.columns(2)

    col1.write(f"Total Number of Rides: {data_filtered['ride_time'].count()}")
    col1.write(f"Top Instructor(s): {data_filtered['instructor'].mode().to_string(index=False)}")
    col2.write(f"Average Ride Time: {round(data_filtered['ride_time'].mean(), ndigits=2)} Minutes")
    col2.write(f"Average Difficulty Rating: {round(data_filtered['difficulty_rating'].mean(), ndigits=2)}")
    col2.write(f"Average Leaderboard Percentile: {round(1 - (data_filtered['leaderboard_rank'] / data_filtered['leaderboard_users']).mean(), ndigits=4)}%") 

    st.header("", divider='red')
    
    st.write("Most Difficult Ride by User Rating:")
    st.dataframe(most_difficult_ride)

    st.write("Best Leaderboard Performance (by Percentile Rank):")
    st.dataframe(data_filtered[data_filtered.leaderboard_pct == data_filtered.leaderboard_pct.max()].drop_duplicates())

with tab2:
    st.header("", divider='red')

    col1, col2 = st.columns(2)

    col1.write("Leaderboard Performance by Instructor")

    col1.write(
        alt.Chart(leaderboard_pct_by_instructor) \
        .mark_bar(color="#FF4B64") \
        .encode(x=alt.X('instructor', sort=None), y='leaderboard_pct') \
        .configure_axisX(title=None)
    )

    col2.write("Total Ride Time by Instructor")

    col2.write(
        alt.Chart(data=data_filtered[['instructor', 'ride_time']] \
            .groupby('instructor') \
            .sum() \
            .sort_values('ride_time', ascending=False) \
            .reset_index()
        ) \
        .mark_bar(color="#FF4B64") \
        .encode(x=alt.X('instructor', sort=None), y='ride_time') \
        .configure_axisX(title=None)
    )

    col1.write("Total Ride Time by Difficulty Rating")

    col1.write(
        alt.Chart(data=data_filtered[['difficulty', 'ride_time']] \
            .groupby('difficulty') \
            .sum() \
            .reset_index()
        ) \
        .mark_bar(color="#FF4B64") \
        .encode(x=alt.X('difficulty', sort=None), y='ride_time') \
        .configure_axisX(title=None)
    )

    col2.write("    Average Difficulty Rating by Instructor")

    col2.dataframe(data_filtered[['instructor', 'difficulty_rating']] \
        .groupby('instructor') \
        .mean() \
        .sort_values('difficulty_rating', ascending=False) \
        .style.background_gradient(cmap= 'bwr')
    )

    st.write("Average Leaderboard Ranking Percentile (monthly)")           

    st.line_chart(
        data=data_filtered.assign(
            leaderboard_percentile = 
            1 - (data_filtered['leaderboard_rank'] / data_filtered['leaderboard_users'])
            )[['date', 'leaderboard_percentile']].set_index('date').resample("M", kind='datetime').mean().reset_index(),
        x = 'date',
        y = 'leaderboard_percentile'
        )  
    
    # g = (
    #     ggplot(
    #         mapping=aes(x = 'date', y = 'leaderboard_pct'),
    #         data = data_filtered[['date', 'leaderboard_pct']] \
    #             .set_index('date') \
    #             .resample("M", kind='datetime') \
    #             .mean() \
    #             .reset_index()
    #     )
    #     + geom_line(color = 'blue')
    #     + geom_smooth(method = 'lm', se = False, color = 'red')
    #     + expand_limits(y = [0,1])
    #     + scale_x_datetime(date_labels = "%b-%Y", date_breaks = "1 month")
    #     + labs(x="", y="Leaderboard Ranking Percentile")
    #     + theme_minimal()
    #     + theme(axis_text_x=element_text(rotation = 90))
    # )

    # st.pyplot(ggplot.draw(g))
    
with tab3:
    st.header("", divider='red')
    st.write("All Filtered Data")
    st.dataframe(data_filtered.style.highlight_max(color='red'))
