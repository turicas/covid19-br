FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1
WORKDIR /app

RUN apt update \
  && apt install -y build-essential libz-dev python3-dev aria2 curl wget vim \
  && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY requirements-development.txt .
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements-development.txt

COPY . .

VOLUME [ "/app" ]
