FROM python:3.8-slim

WORKDIR /opt/covid19-br

ARG PYTHON_REQUIREMENTS=collect

COPY requirements.txt .
COPY requirements-${PYTHON_REQUIREMENTS}.txt .

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y \
        build-essential \
        wget \
    && python -m pip install --upgrade pip \
    && pip install -r  requirements-${PYTHON_REQUIREMENTS}.txt\
    && apt-get remove -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/covid19-br
COPY ./ /opt/covid19-br

VOLUME [ "/opt/covid19-br/data/output" ]

WORKDIR /opt/covid19-br

CMD [ "/opt/covid19-br/run.sh"]