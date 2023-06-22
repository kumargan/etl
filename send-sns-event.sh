
job_name1=$1
job_name2=$2
sns_topic=$3

file_path="/tmp/status.txt"
job_name="send-sns-event"

echo "*********** starting $job_name *************" >> $file_path

execute_job_name1_success=`hive -e "SET hive.cli.print.header=false;  SELECT success from status where job='"$job_name1"_success'"`
execute_job_name2_success=`hive -e "SET hive.cli.print.header=false;  SELECT success from status where job='"$job_name2"_success'"`


echo "job_name1 $job_name1 execute_job_name1_success $execute_job_name1_success" >> $file_path
echo "job_name2 $job_name2 execute_job_name2_success $execute_job_name2_success" >> $file_path

if [ $execute_job_name1_success == 'true' ] && [ $execute_job_name2_success == 'true' ]; then
	aws sns publish --topic-arn $sns_topic --message "data refreshed for last ${last_n_days} days"
	echo "SNS notification sent successfully" >> $file_path
else
    echo "Job did not finish successfully" >> $file_path
fi


echo "**************** STATUS LOGS *****************" >> $file_path
hive -e "set hive.cli.print.header=true; SELECT * FROM status" | sed 's/[\t]/,/g' >> $file_path
echo "$(<$file_path)"
