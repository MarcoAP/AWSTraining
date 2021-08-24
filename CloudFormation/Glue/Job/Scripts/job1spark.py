import sys
import boto3
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

glue_client = boto3.client('glue', region_name='sa-east-1')

# @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['WORKFLOW_NAME', 'WORKFLOW_RUN_ID', 'JOB_NAME'])
workflow_name = args['WORKFLOW_NAME']
workflow_run_id = args['WORKFLOW_RUN_ID']

workflow_params = glue_client.get_workflow_run_properties(
    Name=workflow_name,
    RunId=workflow_run_id
)["RunProperties"]

print("Params= ", workflow_params)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

df = spark.sql("show databases")
df.show()

path_in = "s3://bucket-raw-training-2021/staging/" + workflow_params['fileName']
df = spark.read.format("csv").option("delimiter",",").option("header","true").load(path_in)
df.show()

path_out = "s3://bucket-datas-training-2021/raw/" + workflow_params['fileName'].split(".")[0] + "/"
df.write.format("parquet").mode("overwrite").save(path_out)

job.commit()
