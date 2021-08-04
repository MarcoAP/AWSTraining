import json
import urllib.parse
import boto3

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

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
        
        dynamodb.put_item(TableName='tb_awstraining', Item={'records':{'S':file_name}})
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
        delete(bucketNameSource, fileKeySource)

        print("CONTENT TYPE: " + response['ContentType'])
        
        print("Ending Lambda: lambda-move-file")

        return response['ContentType']
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
