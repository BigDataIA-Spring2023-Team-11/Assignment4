import boto3
import os
import openai
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.utils import make_chunks
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Set all credentials and variables
aws_access_key_id = os.getenv('ACCESS_KEY')
aws_secret_access_key = os.getenv('SECRET_KEY')

s3 = boto3.client('s3',
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)
s3_resource = boto3.resource('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)
openai.api_key = os.getenv('API_KEY')
bucket_name = os.getenv('SOURCE_BUCKET')

loc = '/opt/airflow/working_dir/'


def get_audio_file(ti):
    # Download the latest audio file from S3 bucket
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix='Audio_files/')
    latest_object = sorted(response['Contents'], key=lambda obj: obj['LastModified'], reverse=True)[0]
    filename_ext = str(latest_object['Key'].split('/')[-1])
    # audio_file_path = '/tmp/' + filename_ext
    audio_file_path = str(f'{loc}{filename_ext}')
    filename = str(os.path.splitext(filename_ext)[0])
    s3.download_file(bucket_name, latest_object['Key'], audio_file_path)
    print(f'Audio file {filename} downloaded at {audio_file_path}...')
    ti.xcom_push(key="file_path", value=audio_file_path)
    ti.xcom_push(key="filename", value=filename)
    ti.xcom_push(key="filename_ext", value=filename_ext)


def transcribe_audio_file(ti):
    audio_file_path = ti.xcom_pull(task_ids="get_latest_audio_file", key="file_path")
    print(f'audio_file_path is {audio_file_path}')
    sound = AudioSegment.from_file(audio_file_path)
    split_time = 1 * 60 * 1000  # 1 minute to milliseconds
    sound_parts = make_chunks(sound, split_time)
    # text_file_path = f'/tmp/translated_text.txt'
    text_file_path = f'{loc}translated_text.txt'
    print(f'Output to be saved in : {text_file_path}')
    with open(text_file_path, 'a+') as f:
        for i, part in enumerate(sound_parts):
            # file_name = f"/tmp/audio{i}.wav"
            file_name = f"{loc}audio{i}.wav"
            print(f'Splitting file : {file_name}')
            part.export(file_name, format='wav')
            model_id = 'whisper-1'
            with open(file_name, 'rb') as audio_file:
                translation = openai.Audio.translate(
                    api_key=openai.api_key,
                    model=model_id,
                    file=audio_file,
                    response_format='text'
                )

            # Save the translated and transcribed text to text file
            f.write(translation)
            print(f'{file_name} translated...')
    ti.xcom_push(key="transcription", value=text_file_path)


def upload_text_file_s3(ti):
    text_file_path = ti.xcom_pull(task_ids="translate_and_transcribe_audio_file", key="transcription")
    filename = ti.xcom_pull(task_ids="get_latest_audio_file", key="filename")

    # Upload the text file to the same S3 bucket
    filename_with_txt = f'{filename}.txt'
    s3_file_path = 'audio_to_text/' + filename_with_txt
    s3_resource.Object(bucket_name, s3_file_path).put(Body=open(text_file_path, 'rb'))
    print(f'Transcribed text saved to {s3_file_path}')


def add_generic_questions(ti):
    text_file_path = ti.xcom_pull(task_ids="translate_and_transcribe_audio_file", key="transcription")
    filename = ti.xcom_pull(task_ids="get_latest_audio_file", key="filename")
    filename_ext = ti.xcom_pull(task_ids="get_latest_audio_file", key="filename_ext")

    with open(text_file_path, "r") as f:
        transcription = f.read().strip()

    print('creating generic questions...')
    # generate answers to default generic questions
    prompts = [
        "What is the context of this meeting?",
        "What are the key points of this meeting?",
        "What is the summary of this meeting?"
    ]

    answers = []

    for prompt in prompts:
        # Combine the prompt with the entire transcription text
        prompt_text = prompt + "\nText: " + transcription

        # Generate text using `openai.Completion.create()`
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt_text,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.8,
        )
        generated_text = response.choices[0].text

        answers.append(generated_text)

    print('Writing answers for default questions...')

    # create a dictionary with the results
    result = {
        "file": filename_ext,
        "processed_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": transcription,
        "default_questions": {
            "question1": {
                "question": prompts[0],
                "answer": answers[0]
            },
            "question2": {
                "question": prompts[1],
                "answer": answers[1]
            },
            "question3": {
                "question": prompts[2],
                "answer": answers[2]
            },
        }
    }

    print('Writing Q/A file...')

    # Save the results to a JSON file
    ques_file_path = f'/tmp/{filename}.json'
    with open(ques_file_path, "w") as f:
        json.dump(result, f, indent=4)

    # Upload questionare file to the same S3 bucket
    filename_json = f'{filename}.json'
    s3_file_path = f'default_questions/{filename_json}'

    s3_resource.Object(bucket_name, s3_file_path).put(Body=open(ques_file_path, 'rb'))
    print(f'Questionare saved to {s3_file_path}')


def clean_dir():
    if not os.listdir(loc):
        print(f"{loc} is empty")
    else:
        # Remove all files from the directory
        for f in os.listdir(loc):
            os.remove(os.path.join(loc, f))
        print(f"Files removed from {loc} ...")

