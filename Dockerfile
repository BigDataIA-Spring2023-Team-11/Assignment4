FROM apache/airflow:2.5.2
USER root
RUN apt-get update && apt-get install -y apt-transport-https
RUN apt-get update \
  && apt-get install -y ffmpeg \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
#USER airflow