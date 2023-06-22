#add missing variables
db_pwd=${3}
last_n_days=${10}

sqoop import --connect ${db_conn_string}  --username ${db_user} --password ${db_pwd} --table ${table}  --where "TRADE_TIME > '${start_date}'"  --hive-import  --hive-table ${scoop_hive_table_name} --m ${scoop_executors}

if [ $? -eq 0 ]; then
	hive -e "INSERT INTO status VALUES('$job_name','$d','true')"
	echo "Sqoop successful "  >> $file_path
else
    echo " Sqoop Failed"  >> $file_path
fi

echo "starting sqoop for $last_n_days days, data pull start_date is $start_date "  >> $file_path
