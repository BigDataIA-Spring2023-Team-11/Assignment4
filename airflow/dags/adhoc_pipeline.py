from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from adhoc import get_audio_file, transcribe_audio_file, upload_text_file_s3, add_generic_questions, clean_dir

# Define DAG arguments
default_args = {
    'owner': 'Team11',
    'depends_on_past': False,
    'start_date': datetime.today(),
    'retries': 5
}

# Define DAG
adhoc_dag = DAG('Adhoc_Dag',
                default_args=default_args
                )

get_audio_task = PythonOperator(
    task_id='get_latest_audio_file',
    python_callable=get_audio_file,
    dag=adhoc_dag
)

transcribe_task = PythonOperator(
    task_id='translate_and_transcribe_audio_file',
    python_callable=transcribe_audio_file,
    dag=adhoc_dag
)

upload_task = PythonOperator(
    task_id='upload_transcription_to_S3',
    python_callable=upload_text_file_s3,
    dag=adhoc_dag
)

default_questions_task = PythonOperator(
    task_id='upload_default_questions_to_S3',
    python_callable=add_generic_questions,
    dag=adhoc_dag
)

cleanup_task = PythonOperator(
    task_id='cleanup_and_archive_files',
    python_callable=clean_dir,
    dag=adhoc_dag
)

# Set up dependencies
get_audio_task >> transcribe_task >> upload_task >> default_questions_task >> cleanup_task
