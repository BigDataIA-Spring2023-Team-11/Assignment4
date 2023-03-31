import io
import os
import json
import time
import boto3
import openai
import requests
from dotenv import load_dotenv
import datetime


load_dotenv()

# Create an AWS S3 client to store in user bucket
s3_client = boto3.client('s3',
                         region_name='us-east-1',
                         aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                         aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                         )

s3_resource = boto3.resource('s3',
                             region_name='us-east-1',
                             aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                             aws_secret_access_key = os.environ.get('AWS_SECRET_KEY'))

s3_logs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('LOG_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('LOG_SECRET_KEY')
                        )

s3_bucket = os.environ.get('SOURCE_BUCKET')
user_bucket_access = s3_resource.Bucket(s3_bucket)
openai.api_key = os.environ.get('API_KEY')

with open('config.json', 'r') as f:
    config = json.load(f)

adhoc_endpoint = config['endpoints']['adhoc']

"""
writing logs to cloudwatch
"""
def write_logs_to_cloudwatch(message: str, log_stream):
    s3_logs.put_log_events(
        logGroupName = "model_as_a_service",
        logStreamName = log_stream,
        logEvents = [
            {
                'timestamp' : int(time.time() * 1e3),
                'message' : message
            }
        ]
    )

"""
get all files from a s3 directory
"""
def list_files_in_folder(folder_name: str):
    files = []
    user_s3_bucket_files = s3_client.list_objects(Bucket = s3_bucket, Prefix =f"{folder_name}/").get('Contents')
    for obj in user_s3_bucket_files:
        file_path = obj['Key'].split('/')
        if file_path[-1] != '':
            files.append(file_path[-1])
    if (len(files)!=0):
        return files

"""
Uploading files to s3 bucket
"""
def send_files_to_s3(audio_file: str, folder_name: str):
    audio_name = audio_file.name
    s3_object_file = f'{folder_name}/{audio_name}'
    s3_resource.Bucket(s3_bucket).put_object(Key=s3_object_file, Body=audio_file.read())



"""
asks a user inputed question on text and returns response
"""
def answer_custom_question(question_input, selected_file_content):
    prompt = f'Question: {question_input}\nContext: {selected_file_content}\nAnswer:'
    response = openai.Completion.create(
        engine='text-davinci-002',
        prompt=prompt,
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    answer = response.choices[0].text.strip()
    return answer

def trigger_adhoc_dag():
    # Generate timestamp
    timestamp = datetime.datetime.utcnow().isoformat()

    payload = json.dumps({
        "dag_run_id": f"run_via_api_{timestamp}",
        "conf": {}
    })
    headers = {
        'Authorization': 'Basic YTRAdGVhbTExOnRlYW0xMQ==',
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", adhoc_endpoint, headers=headers, data=payload)
    return response


def retrive_answers_from_default_answers_json(filename, question_asked):
    bucket_name = s3_bucket
    directory_name = 'Default-Questions'

    response = s3_client.get_object(Bucket=bucket_name, Key=f'{directory_name}/{filename}')
    file_content = response['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    answer = ""
    for q in json_content['default_questions'].values():
        if q['question'] == question_asked:
            answer = str(q['answer']).strip()
            break

    return answer.strip()

def get_all_default_answers(filename):
    bucket_name = s3_bucket
    directory_name = 'Default-Questions'

    response = s3_client.get_object(Bucket=bucket_name, Key=f'{directory_name}/{filename}')
    file_content = response['Body'].read().decode('utf-8')
    json_content = json.loads(file_content)
    return json_content["default_questions"]["question1"]["answer"] + json_content["default_questions"]["question2"]["answer"] + json_content["default_questions"]["question3"]["answer"]

def get_transcribed_file_content(file_name):

    file_path = f'Processed-Text/{file_name.split(".")[0]}.txt'
    response = s3_client.get_object(Bucket=s3_bucket, Key=file_path)
    text = response['Body'].read().decode('utf-8')
    return text


