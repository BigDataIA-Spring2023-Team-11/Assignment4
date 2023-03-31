# Assignment4 - Meeting Intelligence Application

### Links
<ul>
<li>💻 <a href="https://meetingintelligence-vbs-bigdata.streamlit.app/">Streamlit</a> </li>
<li>⏰ <a href="http://23.21.117.161:8080/home">Airflow</a> </li>
<li>📖 <a href="https://codelabs-preview.appspot.com/?file_id=1Kvr1U-_Q8uHod0Vy34imUPMNgoC8hk50rDscrkmy26A#0">Codelab </a> </li>
</ul>



### Table of Content

1️⃣ [Objective](#objective) <br>
2️⃣ [Architecture Diagram](#architecture-diagram) <br>
3️⃣ [S3 Bucket Design](#s3-bucket-design) <br>
4️⃣ [Steps to run the application](#steps-to-run-the-application) <br>
5️⃣ [Attestation](#attestation) <br>

___


## Objective
The objective is to develop a Meeting Intelligence Application and evaluate its performance by recording four 10-minute-long meetings. The application will utilize Whisper and GPT 3.5 APIs, integrated with Streamlit and Airflow. The recorded meetings will be converted to transcripts using the Whisper API. Ask some generic questions to these transcripts using ChatGPT and provide the user an option to ask custom questions.
## Architecture Diagram
![image](/Users/akshaysawant/Downloads/Assignment4_bhakti/architecture_diagram/final_cloud_architecture_diagram.png)

## S3 Bucket Design
![image](/Users/akshaysawant/Downloads/Assignment4_bhakti/s3_images/pasted_image.png)


## Steps to run the application
1. Clone the airflow branch using the following code on terminal - 
````
git clone --branch airflow https://github.com/BigDataIA-Spring2023-Team-11/Assignment4.git
````
2. Move to the project directory and run the following command in terminal to create a .env file
````
nano .env
````
3. Add the following environment variables with values:
```
AIRFLOW_UID=501
AIRFLOW_PROJ_DIR=./airflow
ACCESS_KEY=
SECRET_KEY=
SOURCE_BUCKET=
API_KEY=
KMP_DUPLICATE_LIB_OK=TRUE
```
4. Save file while exiting the editor -> *control* + *x* 
5. Install requirements using command - 
```commandline
pip install -r requirements.txt
```
6. Ensure docker is running in background. Run following commands - 
```commandline
docker-compose build
docker compose up airflow-init
docker compose up
```
7. Once the localhost URL is shared, go to : https://localhost:8080/
8. Login using following credentials -
```commandline
Username: a4@team11
Password: team11
```
9. Review DAGS: Adhoc_DAG and Batch_DAG
10. Go to individual dags to trigger run, view logs, graphs etc.

## Attestation
WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT
AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK
Contribution:
<ul>
<li>Aakash: 25%</li>
<li>Bhakti: 25%</li>
<li>Bhargavi: 25%</li>
<li>Charu: 25%</li>
</ul>


