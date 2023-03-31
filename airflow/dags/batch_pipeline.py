from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from batch import get_audio_file, clean_dir, transcribe_audio_file, upload_text_file_s3, add_generic_questions

# Define DAG arguments
default_args = {
    'owner': 'Team11',
    'depends_on_past': False,
    # 'start_date': datetime(2022, 3, 25),
    'start_date': datetime.today(),
    'retries': 5
}

# Define DAG
batch_dag = DAG('Batch_Dag',
                default_args=default_args,
                schedule='0 0 * * *'
                )

get_all_audio_task = PythonOperator(
    task_id='get_all_audio_files',
    python_callable=get_audio_file,
    dag=batch_dag
)

transcribe_all_task = PythonOperator(
    task_id='transcribe_all_audio_files',
    python_callable=transcribe_audio_file,
    dag=batch_dag
)

upload_all_task = PythonOperator(
    task_id='upload_all_transcriptions_to_S3',
    python_callable=upload_text_file_s3,
    dag=batch_dag
)

default_questions_task = PythonOperator(
    task_id='run_and_save_default_questions_on_S3',
    python_callable=add_generic_questions,
    dag=batch_dag
)

archive_and_cleanup_task = PythonOperator(
    task_id='archive_S3_and_cleanup',
    python_callable=clean_dir,
    dag=batch_dag
)

# Set up dependencies
get_all_audio_task >> transcribe_all_task >> upload_all_task >> default_questions_task >> archive_and_cleanup_task

