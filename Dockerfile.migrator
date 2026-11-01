FROM python:3.12-slim

WORKDIR /migrations

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir yoyo-migrations psycopg2-binary

CMD sh -c 'yoyo apply -vvv --batch --database "$DATABASE_URL" .'