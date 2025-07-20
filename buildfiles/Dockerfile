FROM huecker.io/library/python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client

RUN pip install --upgrade pip "poetry==1.5.1"
RUN poetry config virtualenvs.create false
COPY ../pyproject.toml poetry.lock ./
RUN poetry install

COPY .. .


