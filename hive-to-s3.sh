
# write daily data into datalake

s3_data_folder=${1}
last_n_days=${2}
write_to_s3_job=${3}
scoop_pull_job=${4}
scoop_hive_table_name=${5}

file_path="/tmp/status.txt"
#current job name
job_name=$write_to_s3_job

echo "*********** starting $job_name *************" >> $file_path
#scoop job name onto which this job is dependent. check previous step in lambda-function.py
scoop_job_name=$scoop_pull_job

execute_sqoop_success=`hive -e "SET hive.cli.print.header=false; SELECT success from status where job='$eq_scoop_job_name'"`
echo "execute_sqoop_success $execute_sqoop_success" >> $file_path

if [ $execute_sqoop_success == 'true' ]; then
	## if scoop job pushed data into hive successfully, then pull data from hive and create csv	
	i=$last_n_days						# last_n_days use to iterate till that month only
	deduct_month=0 						# deduct month is used to deduct from current month after iterating each month
	current_month_days=$(date +%e)		# Default Take number of days of current month 
	current_flag=1;						# Set current month flag 
	fail_status=0;						# maintain failed status 

	while [ $i -gt 0 ] ; do
				
		# Fetch month in MM after iterating each month		
		month=$(date -d "$(date +%Y-%m-1) -$deduct_month month" +%Y-%m)

		#log time
		start_time_h=`date +%s`
		# pull data from hive into files
		echo "Hive Execution Started for date ${month}" >> $file_path
		#aws s3 rm --recursive s3://$s3_data_folder/output/equity/month=${month}
		hive -e "INSERT OVERWRITE TABLE table_out PARTITION (month='${month}') SELECT * FROM ${scoop_hive_table_name} where SUBSTR(trade_time, 1, 7) = '${month}'"
		#save command status for next condition
		hive_to_s3_push=$?
		#log time
		end_time_h=`date +%s`
		tot_time_h=$(($end_time_h-$start_time_h))
		echo "hive to S3 for date ${month}, time taken : $tot_time_h " >> $file_path

		if [ $hive_to_s3_push -eq 0 ]; then
			echo "hive_to_s3_push execution completed for $scoop_hive_table_name, date ${month}, job status till now ${fail_status}" >> $file_path

			#log time
			start_time_HS=`date +%s`
			# insert success into hive status table
			hive -e "INSERT INTO status VALUES('"$job_name"_"${month}"','${month}','true')" >> $file_path
			#log time
			end_time_HS=`date +%s`
			tot_time_HS=$(($end_time_HS-$start_time_HS))
			echo "insert status for ${month}, time taken : $tot_time_HS " >> $file_path		
			

		else
			echo "Hive Execution Failed for date ${month}" >> $file_path
			fail_status=1
		fi

		# iterate loop	
		if [ $current_flag -eq 1 ];
		then	
			# current month flag enable then just deduct default current month days from  i days 
			i=$(($i-$current_month_days))
			current_flag=0
		else				
			# deduct days after count number of days of that month from  i days
			i=$(($i-$(date -d "-$(date +%d) days -$(($deduct_month-1)) month" +%d)))		
		fi
		deduct_month=$(($deduct_month+1))
		echo "i:$i" >>$file_path

	done
	
	# insert status 
	if [ $fail_status -eq 1 ]; then
		hive -e "INSERT INTO status VALUES('"$job_name"_success','$month','false')"
	else
		hive -e "INSERT INTO status VALUES('"$job_name"_success','$month','true')"
	fi
else
    echo "$scoop_job_name did not finish successfully" >> $file_path
fi

echo "$(<$file_path)"



