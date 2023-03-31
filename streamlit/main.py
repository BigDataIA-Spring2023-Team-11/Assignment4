import os
import time
import json
import boto3
from PIL import Image
import main as st
from dotenv import load_dotenv
import requests
import datetime
from utils import list_files_in_folder, send_files_to_s3, answer_custom_question, trigger_adhoc_dag, \
    get_all_default_answers, retrive_answers_from_default_answers_json, get_transcribed_file_content, write_logs

# Generate timestamp
timestamp = datetime.datetime.utcnow().isoformat()


load_dotenv()

s3_resource = boto3.resource('s3',
                             region_name='us-east-1',
                             aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                             aws_secret_access_key = os.environ.get('AWS_SECRET_KEY'))

# Lets Define user bucket to save file
s3_bucket = os.environ.get('SOURCE_BUCKET')
user_bucket_access = s3_resource.Bucket(s3_bucket)
with open('config.json', 'r') as f:
    config = json.load(f)

audio_file_dir = config['dir']['audio_file']
default_questions_dir = config['dir']['default_questions']
adhoc_endpoint = config['endpoints']['adhoc']





def upload_file_to_s3_bucket():
    uploaded_file = st.file_uploader('Please attach an audio file', type=["mp3"])
    
    if uploaded_file is not None:
        write_logs(f"{uploaded_file.name} File attached to upload","file_upload_logs")
        size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f'Size: {size_mb:.2f} MB')

        audio_file_types = ["audio/mpeg", "audio/wav", "audio/x-wav", "audio/mpeg3", "audio/x-mpeg-3"]
        
        if uploaded_file.type not in audio_file_types:
            st.error('Uploaded file type not supported')
        else:
            upload_button = st.button('Upload and transcribe!')
            if upload_button:
                audiofile_folder = f'{audio_file_dir}/'
                file_key = audiofile_folder + uploaded_file.name
                keys_s3_files = []
                for list_s3_files in user_bucket_access.objects.all():
                    keys_s3_files.append(list_s3_files.key)
                if file_key in keys_s3_files:
                    write_logs(f"{file_key} File already available in the user bucket folder.","file_upload_logs")
                    st.error('File already exists, please select another file')

                
                else:
                    with st.spinner('Uploading'):
                        try:
                            send_files_to_s3(uploaded_file, "Adhoc")
                            with st.expander(f"Successfully Uploaded the File, expand for more info"):
                                st.write(f"filename {uploaded_file.name}")
                                st.write(f"Uploaded to S3 Bucket: {s3_bucket}")
                                response = trigger_adhoc_dag()
                                if response.ok:
                                    st.write("Audio transcripted successfully")
                                else:
                                    st.write("Failed to transcribe the audio: {}".format(response.text))
                                write_logs(f"Successfully uploaded {uploaded_file.name} to Audio_files.","file_upload_logs")
                        except Exception as e:
                            st.error(f'Error while Uploading the File: {str(e)}')
                            write_logs(f"Error uploading file: {str(e)}","file_upload_logs")

# def transcribe_file():
#     selected_file = st.selectbox('Please Select the media file to transcribe:', [" "] + list_files_in_folder('Adhoc-Folder'))
#     transcribe_file = st.button('Transcribe the file')
#     if transcribe_file:
#         if selected_file != " ":
#             with st.spinner('Transcribing...'):
#                 try:
#                     s3_object_key = f'Adhoc-Folder/{selected_file}'
#                     transcript = transcribe_media_file(s3_object_key)
#                     st.write(transcript)
#                     st.success('File transcribed successfully !!!')
                    # write_logs(f"File transcribed successfully {transcript}")
#                     st.write('')
#
#                     key = transcript_file_s3(s3_object_key, transcript)
#                     st.success(f"Successfully uploaded transcript to {key}")
#                     # write_logs(f"Successfully uploaded transcript to {key}")
#
#                 except Exception as  e:
#                     st.error('Error transcribing the file: ' + str(e))
#                     # write_logs(f"Error transcribing file: {str(e)}")
#                     st.write('Please try again later !!!')
#         else:
#             st.warning('Please select the file first !!!')
#     else:
#         st.write('Please upload the file first !!!')

# def get_text_analysis():
#     selected_file = st.selectbox('Please Select the transcript file from the processed list:', [" "] + list_files_in_folder('Processed-Text-Folder'))
#     default_button = st.button('Generate Deafult Question:')
#     question_input = st.text_input("Please Enter Your Questions:")
#     ask_button = st.button('Ask Question:')
#
#     if selected_file != " ":
#         if default_button:
#             st.write('')
#             default_answer = gpt_default_questions(selected_file)
#             # write_logs(f"Default Questions: {default_answer}")
#             st.write(default_answer)
#         else:
#             st.warning('Please generate default questions')
#
#         if ask_button:
#             # write_logs(f"Asking Question: {question_input}")
#             answer = generate_answer(question_input, selected_file)
#             # write_logs(f"Answers: {answer}")
#             st.write(answer)
#         else:
#             st.warning("Please ask the question from the transcript file selected")
#     else:
#         st.warning("Please select the file first !!!")

# Function to display Streamlit Homepage App
# def homepage_application():

def question_answering():
    files_list = list_files_in_folder(default_questions_dir)
    selected_file = st.selectbox("Select a file to ask questions",files_list)
    st.markdown(
        "<h5 style='text-align: left'><span style='color: #2A76BE;'>Questions we got you covered</span></h5>",
        unsafe_allow_html=True)
    st.markdown("1. What is the context of this meeting?")
    st.markdown("2. What are the key points of this meeting?")
    st.markdown("3. What is the summary of this meeting?")
    st.markdown("")
    answer_all_btn = st.button("Answer all the above questions!")
    if answer_all_btn:
        combined_answer = get_all_default_answers(selected_file)
        with st.expander("Expand for answer"):
            st.write(combined_answer)
            write_logs(f"Answer retrieved for all questions", "questions_logs")

    st.markdown("")
    st.markdown("<span style='color: #2A76BE;'>--------------------------------------------------------------------------------------------------------------------------------------------</span>",unsafe_allow_html=True)
    default_questions = [
        "What is the context of this meeting?",
        "What are the key points of this meeting?",
        "What is the summary of this meeting?"
    ]
    selected_question = st.selectbox("Select Question",default_questions)
    get_answer_btn = st.button("Get answer for selected question")
    if get_answer_btn:
        answer = retrive_answers_from_default_answers_json(selected_file,selected_question)
        with st.expander(f"Expland to know answer for {selected_question}"):
            st.write(answer)
            write_logs(f"Answer retrieved for {selected_question}", "questions_logs")

    st.markdown("<span style='color: #2A76BE;'>--------------------------------------------------------------------------------------------------------------------------------------------</span>",unsafe_allow_html=True)
    question_input = st.text_input('Enter your question')
    if st.button("Get answer"):
        selected_file_content = get_transcribed_file_content(selected_file)
        answer_to_custom_ques = answer_custom_question(question_input,selected_file_content)
        write_logs(f"Answer generated for {question_input}","questions_logs")
        with st.expander("Expand for answer"):
            st.write(answer_to_custom_ques)








if __name__ == '__main__':

    c1, c2, c3 = st.columns([0.1, 2, 0.1])
    with c2:
        st.title('Meeting Intelligence Application')
        # selected_operation = st.sidebar.selectbox("Select a Operation",
        #                                           ["Homepage", "Upload & Transcribe Media File", "Ask Questions?"])

        selected_operation = st.sidebar.radio("Select a Operation",  ["Homepage", "Upload & Transcribe Media File", "Ask Questions?"])

    if selected_operation == "Upload & Transcribe Media File":
        st.markdown('')
        st.markdown('')
        st.markdown('')
        st.subheader('Upload & Transcribe the Media File')
        st.markdown('')
        upload_file_to_s3_bucket()

    elif selected_operation == "Homepage":
        st.markdown('')
        st.markdown('')
        st.markdown('')
        st.markdown('This project is designed to provide an efficient way to comprehend meeting content. By enabling users to upload an audio file of their choice for transcription, they can easily review and analyze meeting transcripts. Additionally, the project allows users to ask questions related to the meeting content, making it a comprehensive tool for extracting useful insights.')
    else:
        st.markdown('')
        st.markdown('')
        st.markdown('')
        question_answering()
