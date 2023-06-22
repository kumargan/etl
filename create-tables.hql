CREATE TABLE IF NOT EXISTS status ( job String, rundate String,success String );

CREATE EXTERNAL TABLE tale1_out
(
  is string,
  name string
)
PARTITIONED BY (month string)
ROW FORMAT SERDE 'org.apache.hadoop.hive.contrib.serde2.MultiDelimitSerDe' 
WITH SERDEPROPERTIES ("field.delim"="$###$")
STORED AS TEXTFILE 
LOCATION 's3://${s3_data_folder}/output/equity';
