from diagrams import Cluster, Diagram, Edge
from diagrams.aws.storage import S3
from diagrams.onprem.workflow import Airflow
from diagrams.aws.storage import SimpleStorageServiceS3 as S3
from diagrams.aws.compute import ECS, EKS, Lambda
from diagrams.aws.database import RDS
from diagrams.c4 import Person, Container, Database, System, SystemBoundary, Relationship
#from diagrams.onprem.container import Docker
from diagrams.aws.compute import EC2Instance as EC2
from diagrams.aws.management import Cloudwatch
from diagrams.gcp.compute import ComputeEngine as GCE
from diagrams.k8s.controlplane import API
from diagrams.digitalocean.compute import Docker
from diagrams.aws.database import Database
from diagrams.azure.compute import CloudServicesClassic


with Diagram("Final Cloud Architecture Diagram", direction="LR", show=False):
    with Cluster("EC2 Hosted"):
        with Cluster("Airflow"):
            with Cluster(""):
                airflow1 = Airflow("Adhoc Dag")
            with Cluster(""):
                airflow2 = Airflow("Batch Dag")

    with Cluster("Steamlit Hosted"):
        with Cluster("User Interface"):
            ui = Docker("Streamlit")


    with Cluster("Aws Services"):
        bucket = S3("Assignment 4 Bucket")
        activity = Cloudwatch("Logging user activity")

    RestApI = API("Chat GPT API")

    RestApI >> Edge(label="get default questions", color="darkblue") << airflow1
    RestApI >> Edge(label="ask question", color="darkblue") << ui

    ui >> Edge(label="get meeting questions", color="purple") >> bucket

    ui >> Edge(label="Trigger", color="black") >> airflow1

    airflow1 >> Edge(label="Update Files", color="darkorange") >> bucket
    ui << Edge(label="Upload audio file", color="black") << bucket

    ui >> Edge( color="purple") >> activity



