FROM --platform=linux/amd64 ubuntu

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

RUN pip3 install cython falcon gunicorn



WORKDIR /
COPY webHooker.py /
COPY mylogger.py /
COPY falcon_util.py /
RUN echo 'gunicorn -b 0.0.0.0:9090 webHooker:app' > /entrypoint.sh

ENTRYPOINT ["/bin/bash","--","/entrypoint.sh"]
