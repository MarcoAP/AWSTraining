import json
import urllib.parse
import boto3
import os
from time import sleep
from datetime import date, datetime

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
glue = boto3.client('glue', region_name='sa-east-1')

print("Starting Lambda: lambda-move-file")

def lambda_handler(event, context):
    
    print("Event:\n", event)
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    print("Bucket = ", bucket)
    print("Key = ", key)
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        print("Response = ", response)
        
        split_path_origem = key.split('/')
        print("split_path_origem = ", split_path_origem)
        
        file_name = split_path_origem[-1]
        print("file_name = ", file_name)
        
        dynamodb.put_item(TableName='tb_awstraining', Item={'bucketName':{'S':bucket},'fileName':{'S':file_name}})
        print("Recording the name of the file received in DynamoDB Table")
        
        # load Raw filw and decode in UTF-8
        raw_file = response['Body'].read().decode('utf-8')
        print("raw_file_CONTENT = ", raw_file)
        
        # From = s3://bucket-raw-training-2021/input/
        # To   = s3://bucket-raw-training-2021/staging/
        
        bucketNameSource = 'bucket-raw-training-2021'
        fileKeySource = key
        
        sub_folder = 'staging'
        file_destination = file_name
        
        copySource = {'Bucket': bucketNameSource, 'Key': fileKeySource}
        copyDestination = "{sub_folder}/{file_destination}".format(sub_folder=sub_folder,file_destination=file_destination)
        copy(copySource, copyDestination)
        
        dctOtherProperties = {
            'bucketNameSource': str(bucketNameSource),
            'fileKeySource': str(fileKeySource),
            'fileName': str(file_destination),
            "kms_key": os.environ.get('KMS_KEY', '6cf8ba8c-a35c-4b7e-ae6d-d756247e4243'),
            'bucket_raw': os.environ.get('RAW_BUCKET', 'bucket-raw-training-2021'),
            'env': os.environ.get('ENV', 'develop_env')
        }
        
        print(f"dctOtherProperties= : {dctOtherProperties}")

        start = True
        
        if start:
            try:
                
                delete(bucket_=bucketNameSource, file_=fileKeySource)
                print("[!] [ Deleting file in raw folder: " + fileKeySource)
                
                workflowName = 'GlueWorkflowTraining'
                print("# Workflow: " + workflowName)
                
                response = glue.start_workflow_run(Name=workflowName)
                print(f"[+] Printing all response of one the Workflow {response}")
                
                workflow_id = response['RunId']
                print(f"[+] Starting Glue Workflow {workflow_id}")
                
                glue.put_workflow_run_properties(
                    Name=workflowName, 
                    RunId=workflow_id, 
                    RunProperties=dctOtherProperties
                )
                
                print("[!] [ Finishing Glue Workflow: " + workflow_id)
                
                return {
                    'statusCode': 0,
                    'message': f'Workflow {workflow_id} started'
                }
                
            except Exception as e:
                print(e)
                print(f" [!] Error with Glue Workflow {e}.")
                return {
                    'statusCode': -1,
                    'message': e
                }
        else:
            response = f"{file_name} file repeated or not found."
            print("[!] Finishing Lambda")
            return {
                'statusCode': -1,
                'message': response
            }

    except Exception as e:
        print(e)
        print('Error when I get the file {} in the bucket {}. Have certain your file exist.'.format(key, bucket))
        raise e
        

########################################################################
# Other python functions to be used for you
########################################################################
def copy(source, destination):
    try:
        response = s3.copy_object(
            CopySource=source,
            Bucket="bucket-raw-training-2021",
            Key=destination,
            MetadataDirective='COPY',
            TaggingDirective='COPY')
    except Exception as e:
        print(e)
        raise e
    return response['ResponseMetadata'].get('HTTPStatusCode')

def delete(bucket_, file_):
    s3.delete_object(Bucket=bucket_, Key=file_)
    
