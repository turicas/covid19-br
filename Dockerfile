FROM python:3.8-slim

WORKDIR /app

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

RUN mkdir -p /app
COPY ./ /app

VOLUME [ "/app/data/output" ]

CMD [ "/app/web.sh" ]
