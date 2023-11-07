FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y python3-pip python3-dev \
  && apt-get install -y wget vim git curl bash \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip \
  && pip3 install requests paramiko scp celery redis numpy pandas matplotlib

WORKDIR /peri_tasks
COPY . ./
RUN chmod +x /peri_tasks/summarize.py
ENV PATH=/peri_tasks:$PATH

CMD /usr/local/bin/celery -A peri_tasks worker -B -l DEBUG -f /tmp/qa_metrics.log

