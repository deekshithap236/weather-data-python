#!/usr/bin/env python
# coding: utf-8

#importing libraries
import pandas as pd
from pprint import pprint
import requests
import logging 
import input_config
from pandas.io import sql
from sqlalchemy import create_engine
import sys
import os
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
import datetime

#global params
log_path = input_config.log_dir
api_key = input_config.api_key
input_path = input_config.input_path
output_path = input_config.output_path
base_weather_url = input_config.base_weather_url
database = input_config.database
connection_url = "mysql://root:{}@localhost/{}".format(input_config.root_password,database)
table_name = input_config.table_name
fail_count = 0 

#initalizing  logger
var_datetime = datetime.datetime.now().strftime('weather_%Y%m%d_%H%M%S.log')
var_pylogflnm = log_path + "/" + var_datetime
logging.basicConfig(filename=var_pylogflnm, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',datefmt = "%Y-%M-%d %H:%M:%S",filemode ='w')
logger = logging.getLogger()
logger.setLevel("INFO")

def main():
    logger.info("weather data collection started")
    current_date =  datetime.datetime.now().strftime('%Y-%m-%d')
    current_time =  datetime.datetime.now().strftime('%H:%M:%S')
    cities_df = pd.read_csv(input_path,encoding='iso-8859-1')
    columns_list1 = ["id","city",'longitude', 'laitude',"temp","temp_min","temp_max",'pressure', 'humidity','wind_speed', 'wind_deg','timezone']
    columns_list2 = ["id","name",'coord.lon', 'coord.lat',"main.temp","main.temp_min","main.temp_max",'main.pressure', 'main.humidity','wind.speed', 'wind.deg','timezone']
    weather_df = pd.DataFrame(columns =columns_list1)

    for city_name in cities_df["city"]:
        complete_weather_url = base_weather_url + "&q="+ city_name + "&appid=" +api_key
        weather_response =  requests.get(complete_weather_url)
        weather_json = weather_response.json()
        if weather_json["cod"] == 404:
            fail_count = fail_count+1
            logger.info("failed to get data for city - {}".format(city_name))
        df = pd.json_normalize(weather_json)
        df= df[columns_list2]
        df.columns = columns_list1
        weather_df = weather_df.append(df,ignore_index=True)

    weather_df =weather_df.replace("Dehra Dūn","Dehra Dun")
    complete_weather_df = weather_df.merge(cities_df,on=["city"])
    complete_weather_df =complete_weather_df.drop(["lat","lng","iso2","population_proper","population","capital"],axis=1)
    complete_weather_df["date_captured"] = current_date
    complete_weather_df["time_captured"] = current_time 
    logger.info("completed dataframe manipulation")     
    out_file = output_path + "/" + "weather_report_{}.csv".format(current_date)
    if os.path.isfile(out_file):
        complete_weather_df.to_csv(out_file, mode='a', header=False,index=False)
    else:
        complete_weather_df.to_csv(out_file, mode='w', header=True,index=False)
    try: 
        logger.info("writing to database , user - root , database - {} , table - {}".format(database,table_name))
        engine = create_engine(connection_url)
        con = engine.connect()
        sql.to_sql(complete_weather_df, con=con, name=table_name, if_exists="append",index=False)
        logger.info("wriritng to database successful")
    except:
        logger.info("unable to connect to database/ write to table. ERROR - {}".format(sys.exc_info()[0]))
    finally:
        logger.info("connection closed to database")
        con.close()        
        logging.shutdown()


if __name__ =="__main__":
     main()                