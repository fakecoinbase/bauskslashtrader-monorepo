FROM python:3.7-slim
ARG env=production
ARG POETRY_VERSION=1.0.5
ENV ENV=$env \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=$POETRY_VERSION
RUN pip install "poetry==$POETRY_VERSION"
RUN apt-get update && apt-get install -y supervisor
WORKDIR /code
COPY poetry.lock pyproject.toml /code/
COPY ./traderutils /code/traderutils

RUN apt-get update \
  && apt-get install -y --no-install-recommends gcc libc-dev \
  && rm -rf /var/lib/apt/lists/*
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$ENV" = "production" && echo "--no-dev") --no-interaction --no-ansi \
  && apt-get purge -y --auto-remove gcc libc-dev

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY . /code
EXPOSE 5000
RUN chmod 777 ./scripts/migrate.sh
RUN chmod 644 ./test_migrations.py

CMD ["/usr/bin/supervisord"]

# CMD gunicorn --bind 0.0.0.0:5000 --worker-class aiohttp.GunicornWebWorker --workers 1 --access-logfile - --capture-output entrypoint:app 
