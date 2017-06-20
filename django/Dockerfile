FROM python:3.4

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y freetds-dev
RUN apt-get install -y freetds-bin
RUN apt-get install -y libpq-dev
COPY requirements.txt /tmp/
RUN pip3 install --upgrade pip
RUN pip3 install -r /tmp/requirements.txt
RUN useradd celery
COPY locum /locum
RUN chown -R celery:celery /locum

WORKDIR /locum
