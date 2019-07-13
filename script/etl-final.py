import configparser
import os
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql import SQLContext
from pyspark.sql import types as T
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.functions import year, month, dayofmonth, hour, weekofyear, date_format
from pyspark import SparkConf


config = configparser.ConfigParser()
config.read('dl.cfg')

# Enter your AWS ACCESS KEY ID and SECRET ACCESS KEY
os.environ['AWS_ACCESS_KEY_ID']= 
os.environ['AWS_SECRET_ACCESS_KEY']= 

def create_spark_session():
    spark = SparkSession \
        .builder \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:2.7.3") \
        .getOrCreate()
    return spark

def process_song_data(spark, input_data, output_data):
    # get filepath to song data file
    song_data = os.path.join(input_data, "song_data/A/A/A/*")
    
    # read song data file
    df = spark.read.json(song_data)

    # extract columns to create songs table
    songs_table = df.select(df['song_id'],df['title'],df['artist_id'],df['year'],df['duration'])
    songs_table.show(n=5)
    
    # write songs table to parquet files partitioned by year and artist
    songs_table.write.partitionBy('artist_id','year').parquet("",mode = 'overwrite')

    # extract columns to create artists table
    artists_table =df.select(df['artist_id'],df['artist_name'],df['artist_location'],df['artist_latitude'],df['artist_longitude'])
    artists_table.show(n=5)

    # write artists table to parquet files
    artists_table.write.parquet("",mode = 'overwrite')


def process_log_data(spark, input_data, output_data):
    # get filepath to log data file
    log_data = os.path.join(input_data, "log_data/2018/11/*.json")

#      read log data file
    df = spark.read.json(log_data)
    print(df)
    
#      filter by actions for song plays
    df = df[df['page'] == 'NextSong']

    df.orderBy("userId", F.col("level").desc()).dropDuplicates(["userId"])
    
    df.show()
#      extract columns for users table    
    users_table = df.select(df['userId'],df['firstName'],df['lastName'],df['gender'],df['level'])
    
#      write users table to parquet files
    users_table.write.parquet("", mode = 'overwrite')

#      create timestamp column from original timestamp column
    get_timestamp = F.udf(lambda x: str(int(int(x) / 1000)))
    df = df.withColumn("Timestamp", get_timestamp(F.col('ts')))
         
#      create datetime column from original timestamp column
    get_datetime = F.udf(lambda x: datetime.fromtimestamp((x/1000.0)),T.TimestampType())
    df = df.withColumn("DateTime", get_datetime(F.col('ts')))
    
#      extract columns to create time table
    time_table = df.withColumn('Start_Time', col('DateTime')).\
    withColumn('Hour',hour(col('DateTime'))).withColumn('Day',dayofmonth(col('DateTime'))).\
    withColumn('Week',weekofyear(col('DateTime'))).withColumn('Month',month(col('DateTime'))).\
    withColumn('Year',year(col('DateTime'))).withColumn('WeekDay',date_format(col('DateTime'),'u'))
    
    
#      write time table to parquet files partitioned by year and month
    time_table.write.parquet("", mode = 'overwrite')
#     time_table.show(n=5)

#      read in song data to use for songplays table
    song_df = spark.read.parquet("")

#      extract columns from joined song and log datasets to create songplays table 
    song_df.createOrReplaceTempView('songView')
    
    df.createOrReplaceTempView('logView')
    
    songplays_table = spark.sql("""
                                 SELECT from_unixtime(lv.ts,'yyyy-MM-dd hh:mm:ss') as start_time,
                                 lv.userId    as user_id,
                                 lv.level     as level,
                                 sv.song_id   as song_id,
                                 sv.artist_id as artist_id,
                                 lv.sessionId as session_id,
                                 lv.location  as location,
                                 lv.userAgent as user_agent
                                 FROM logView lv
                                 JOIN songView sv ON (lv.song == sv.title)
                       """)
    songplays_table.show(n=5)
    
#   write songplays table to parquet files partitioned by year and month
    songplay = songplays_table.withColumn('year',col('start_time')).withColumn('month',col('start_time'))

    songplay.write.partitionBy("year","month").parquet("file:///tmp/songplaydata", mode ='overwrite')
    
    sp_df = spark.read.parquet("file:///tmp/songplaydata")
    sp_df.write.parquet("", mode = 'overwrite')

    sp_df.createOrReplaceTempView("songParquet")
    
    spark.sql("SELECT * FROM songParquet").show()

def main(): 
    spark = create_spark_session()
    input_data = "s3a://udacity-dend/"
    output_data = ""
    
    process_song_data(spark, input_data, output_data)    
    process_log_data(spark, input_data, output_data)


if __name__ == "__main__":
    main()
