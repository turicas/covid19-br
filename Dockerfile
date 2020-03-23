FROM python:3.8-slim

COPY requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y \
        g++ \
    && python -m pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt \
    && apt-get remove -y g++ \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/*

RUN mkdir -p /opt/covid19-br
COPY ./ /opt/covid19-br

VOLUME [ "/opt/covid19-br/data/output" ]

WORKDIR /opt/covid19-br

CMD [ "/opt/covid19-br/run.sh"]