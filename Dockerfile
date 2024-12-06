FROM python:3.10 AS base

WORKDIR /app/src

RUN useradd -m auth_user \
&& chown -R auth_user:auth_user /app

USER auth_user

ENV PATH=$PATH:/home/auth_user/.local/bin

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt \
&& mkdir /app/logs

COPY ./src /app/src

COPY ./src/.env /app/src/.env

FROM base AS test

COPY ./tests /app/tests

RUN chmod +x /app/tests/functional/start_tests.sh

ENV PYTHONPATH=/app

FROM base AS deploy

EXPOSE 8000

ENTRYPOINT ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "-k", "uvicorn_worker.UvicornWorker"]
