import os, json,boto3,math
from datetime import datetime

env                     = os.getenv('ENV')
CONFIG_FILE             ='./cfg.json'
today                   = datetime.now()
job_name                = 'class-data-etl'

NA='NOT_AVAILABLE'
scoop_executors         =NA
last_n_days             =NA
sns_topic               =NA
s3_code_folder          =NA
s3_emr_logs_folder      =NA
Ec2SubnetId             =NA
Ec2KeyName              =NA
instance_profile        = NA
number_of_nodes         =1

#define missing variables
def lambda_handler(event, context):

    connection = boto3.client('emr', region_name='ap-south-1')
    #initialise configuration
    initializeConfigValues()
    
    cluster_id = connection.run_job_flow(
    Name=job_name+'-'+env,
    ReleaseLabel='emr-6.11.0',
    LogUri='s3://'+s3_emr_logs_folder+'/'+job_name+'/',
    Instances={
        'InstanceGroups': [
            {
                'Name': "Master nodes",
                'Market': 'ON_DEMAND',
                'InstanceRole': 'MASTER',
                'InstanceType': 'm5a.xlarge',
                'InstanceCount': 1,
                "EbsConfiguration": {
                    'EbsOptimized': True,
                    "EbsBlockDeviceConfigs": [
                    {
                      "VolumeSpecification": {
                        "Iops": 3000,
                        "VolumeType": "gp3",
                        "SizeInGB": 100
                      },
                      "VolumesPerInstance": 1
                    }
                  ]
                }
            },
            {
                'Name': "Slave nodes",
                'Market': 'ON_DEMAND',
                'InstanceRole': 'CORE',
                'InstanceType': 'm5a.xlarge',
                'InstanceCount': 4,
                'EbsConfiguration': {
                    'EbsOptimized': True,
                    "EbsBlockDeviceConfigs": [
                    {
                      "VolumeSpecification": {
                        "Iops": 3000,
                        "VolumeType": "gp3",
                        "SizeInGB": 100
                      },
                      "VolumesPerInstance": 1
                    }
                  ]
                }
            }
        ],
        'KeepJobFlowAliveWhenNoSteps': False,
        'TerminationProtected': True,
        'Ec2SubnetId': Ec2SubnetId,
        'Ec2KeyName': Ec2KeyName
    },
    Steps=[
         {
            'Name': 'create-table.hql',
            'ActionOnFailure': 'TERMINATE_CLUSTER',
            'HadoopJarStep': 
                {   
                    'Jar': 'command-runner.jar',
                    'Args': [ "hive","-f","s3://"+s3_code_folder+"/resources/create-table.hql","-d","s3_data_folder="+s3_data_folder ] 
                } 
        },
        {
            'Name': 'execute-scoop.sh',
            'ActionOnFailure': 'TERMINATE_CLUSTER',
            'HadoopJarStep': 
                {   
                    'Jar': 's3://ap-south-1.elasticmapreduce/libs/script-runner/script-runner.jar',
                    'Args': [ "s3://"+s3_code_folder+"/resources/execute-sqoop.sh", db_conn_string, db_user, db_pwd, table1, table2,query_param, scoop_hive_table_name_1, scoop_hive_table_name_2, scoop_executors, last_n_days, job1, job2 ] 
                } 
        },
        {
            'Name': 'write-to-s3-eq.sh',
            'ActionOnFailure': 'TERMINATE_CLUSTER',
            'HadoopJarStep': 
                {   
                    'Jar': 's3://ap-south-1.elasticmapreduce/libs/script-runner/script-runner.jar',
                    'Args': [ "s3://"+s3_code_folder+"/resources/write-to-s3-eq.sh", s3_data_folder ,last_n_days, job1, job2, table_1 ] 
                } 
        },
        {
            'Name': 'write-to-s3-fno.sh',
            'ActionOnFailure': 'TERMINATE_CLUSTER',
            'HadoopJarStep': 
                {   
                    'Jar': 's3://ap-south-1.elasticmapreduce/libs/script-runner/script-runner.jar',
                    'Args': [ "s3://"+s3_code_folder+"/resources/write-to-s3-fno.sh", s3_data_folder ,last_n_days, job1, job2, table_1 ] 
                } 
        },
        {
            'Name': 'send-sns-event.sh',
            'ActionOnFailure': 'TERMINATE_CLUSTER',
            'HadoopJarStep': 
                {   
                    'Jar': 's3://ap-south-1.elasticmapreduce/libs/script-runner/script-runner.jar',
                    'Args': [ "s3://"+s3_code_folder+"/resources/send-sns-event.sh", job1, job2, sns_topic ] 
                } 
        }
    ], 
    BootstrapActions= [
        {
            "Name": "bootstrap",
            "ScriptBootstrapAction": {
                "Path": "s3://"+s3_code_folder+"/resources/bootstrap.sh",
                "Args":[s3_code_folder]
            }
        }
    ],
    VisibleToAllUsers=True,
    JobFlowRole=instance_profile,
    Applications=[{'Name':'Hadoop'},{'Name':'Hive'},{'Name':'sqoop'}],
    Configurations=[
      {
        "Classification": "hive-site",
        "Properties": {
          "hive.server2.tez.sessions.per.default.queue": "5",
          "hive.exec.parallel":"true",
          "hive.exec.dynamic.partition":"true",
          "hive.exec.dynamic.partition.mode":"nonstrict",
          "hive.exec.max.dynamic.partitions.pernode":"20000",
          "hive.exec.max.dynamic.partitions":"500000",
          "hive.auto.convert.join.noconditionaltask" : "true",
          "hive.auto.convert.join.noconditionaltask.size": "209715200",
          "hive.optimize.bucketmapjoin":"true",
          "hive.cli.print.header":"true",
          "mapred.reduce.tasks":"50",
          "hive.tez.auto.reducer.parallelism":"true"
        }
      }
    ],
    ServiceRole='EMR_DefaultRole',
    Tags=[
        {
            "Key":"name",
            "Value":job_name
        }
    ])

    return {
        'statusCode': 200,
        'body': "started"
    }

def initializeConfigValues():

    global sns_topic
    global s3_emr_logs_folder
    global Ec2SubnetId
    global Ec2KeyName
    global instance_profile
    
    s3                      = boto3.resource('s3')
    f                       = open(CONFIG_FILE, "r").read()
    CONFIG_JSON             = json.loads(f)
    sns_topic               = CONFIG_JSON[env]['sns_topic']
    s3_emr_logs_folder      = CONFIG_JSON[env]['s3_emr_logs_folder']
    Ec2SubnetId             = CONFIG_JSON[env]['Ec2SubnetId']
    Ec2KeyName              = CONFIG_JSON[env]['Ec2KeyName']
    instance_profile        = CONFIG_JSON[env]['instance_profile']


    print("env :",env)
    print("sns_topic :",sns_topic)
    print("s3_emr_logs_folder :",s3_emr_logs_folder)
    print("Ec2SubnetId :",Ec2SubnetId)
    print("Ec2KeyName :",Ec2KeyName)
    print("instance_profile :",instance_profile)
    print("today :",today)





   
