## Airflow Setup and Instructions

<a href="http://23.21.117.161:8080/home" target="_blank">Airflow Public Instance</a>


### Branch Structure

* [airflow/dags](./airflow/dags)
  * [adhoc.py](./airflow/dags/adhoc.py)
  * [adhoc_pipeline.py](./airflow/dags/adhoc_pipeline.py)
  * [batch.py](./airflow/dags/batch.py)
  * [batch_pipeline.py](./airflow/dags/batch_pipeline.py)
* [Dockerfile](./Dockerfile)
* [docker-compose.yaml](./docker-compose.yaml)
* [requirements.txt](./requirements.txt)
* [README.md](./README.md)

### Pre-requisites

1. Code Editor (PyCharm, VS Code, etc)
2. Docker
3. Python v3.2 or later

### Steps on run Airflow locally

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




