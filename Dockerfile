FROM python:3.8-slim

WORKDIR /app

ARG PYTHON_REQUIREMENTS=requirements.txt

COPY ${PYTHON_REQUIREMENTS} .

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y \
        aria2 \
        build-essential \
        wget \
    && python -m pip install --upgrade pip \
    && pip install -r ${PYTHON_REQUIREMENTS} \
    && apt-get remove -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app
COPY ./ /app

VOLUME [ "/app/data/output" ]

CMD [ "/app/web.sh" ]
