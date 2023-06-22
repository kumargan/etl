s3_code_folder=$1

sudo aws s3 cp s3://$s3_code_folder/resources/external-jars/mssql-jdbc-12.2.0.jre8.jar /usr/lib/sqoop/lib/mssql-jdbc-12.2.0.jre8.jar
sudo aws s3 cp s3://$s3_code_folder/resources/external-jars/hive-contrib-3.0.0.jar /usr/lib/hive-hcatalog/share/hcatalog/hive-contrib-3.0.0.jar
