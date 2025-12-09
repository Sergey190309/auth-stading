FROM python:3.14-slim-trixie AS base
# FROM python:3.14-alpine AS base

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*


# RUN apk add --no-cache \
# build-base \
# postgresql-dev \
# gcc \
# musl-dev

WORKDIR /code

COPY ./requirements.txt ./requirements.txt
COPY ./pyproject.toml ./pyproject.toml
# COPY ./alembic.ini ./alembic.ini

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

ENV PYTHONPATH=/code

# COPY  ./pytest.ini /code/pytest.ini

# COPY ./src ./src

# COPY ./tests ./tests

# COPY ./static ./static

# CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--reload"]
