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
prefix = 'Batch/'
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)


def get_audio_file(ti):
    # List all objects in the bucket with the specified prefix
    all_files = [obj['Key'] for obj in response['Contents'] if obj['Key'] != prefix]
    print(f'all_files --> {all_files}')
    for file in all_files:
        filename_ext = str(file.split('/')[-1])
        # audio_file_path = '/tmp/' + filename_ext
        audio_file_path = f'{loc}{filename_ext}'
        filename = str(os.path.splitext(filename_ext)[0])
        s3.download_file(bucket_name, file, audio_file_path)
        print(f'{file} downloaded to {audio_file_path} ...')
    ti.xcom_push(key="all_files", value=all_files)


def transcribe_audio_file(ti):
    # all_files = ti.xcom_pull(task_ids="get_audio", key="all_files")
    all_files = [obj['Key'] for obj in response['Contents'] if obj['Key'] != prefix]
    # Loop through all files in working_dir
    for file in all_files:
        if file.endswith('.mp3') or file.endswith('.m4a'):  # check for audio file extensions
            filename_ext = str(file.split('/')[-1])
            audio_file_path = f'{loc}{filename_ext}'
            filename = str(os.path.splitext(filename_ext)[0])
            sound = AudioSegment.from_file(audio_file_path)
            split_time = 1 * 60 * 1000  # 1 minute to milliseconds
            sound_parts = make_chunks(sound, split_time)
            text_file_path = os.path.join(loc, f'{loc}{filename}_text.txt')
            with open(text_file_path, 'a+') as f:
                for i, part in enumerate(sound_parts):
                    part_name = os.path.join(loc, f'{filename}_{i}.wav')
                    print(f'Splitting file : {part_name}')
                    part.export(part_name, format='wav')
                    model_id = 'whisper-1'
                    with open(part_name, 'rb') as audio_file:
                        translation = openai.Audio.translate(
                            api_key=openai.api_key,
                            model=model_id,
                            file=audio_file,
                            response_format='text'
                        )

                    # Save the translated and transcribed text to text file
                    f.write(translation)
                    print(f'{part_name} translated...')
            print(f'Audio file {filename_ext} : translated...')


def upload_text_file_s3(ti):
    text_files = [f for f in os.listdir(loc) if f.endswith('.txt')]
    for file in text_files:
        # Upload the text files to the same S3 bucket
        text_file_path = os.path.join(loc, f'{loc}{file}')
        s3_file_path = 'Processed-Text/' + file
        s3_resource.Object(bucket_name, s3_file_path).put(Body=open(text_file_path, 'rb'))
        print(f'Transcribed text saved to {s3_file_path}')


def add_generic_questions():
    # all_files = ti.xcom_pull(task_ids="get_audio", key="all_files")

    all_files = [obj['Key'] for obj in response['Contents'] if obj['Key'] != prefix]
    for file in all_files:
        filename_ext = str(file.split('/')[-1])
        filename = str(os.path.splitext(filename_ext)[0])
        text_file_path = os.path.join(loc, f'{loc}{filename}_text.txt')

        with open(text_file_path, "r") as f:
            transcription = f.read().strip()

        print('Writing default questions...')
        # generate answers to default  questions
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
            trans_text = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt_text,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.8,
            )
            generated_text = trans_text.choices[0].text

            answers.append(generated_text)

        print('Generating answers for default questions...')

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
        ques_file_path = f'{loc}{filename}.json'
        with open(ques_file_path, "w") as f:
            json.dump(result, f, indent=4)

        # Upload questionnaire file to the same S3 bucket
        filename_json = f'{filename}.json'
        s3_file_path = f'Default-Questions/{filename_json}'

        s3_resource.Object(bucket_name, s3_file_path).put(Body=open(ques_file_path, 'rb'))
        print(f'Questionnaire for file {filename_ext} saved to {s3_file_path}')


def clean_dir():
    if not os.listdir(loc):
        print(f"{loc} is empty")
    else:
        # Remove all files from the directory
        for f in os.listdir(loc):
            os.remove(os.path.join(loc, f))
        print(f"Files removed from {loc}")


