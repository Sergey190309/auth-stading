FROM python:3.13-alpine AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY ./requirements.txt ./requirements.txt
COPY ./pyproject.toml ./pyproject.toml
# COPY ./alembic.ini ./alembic.ini

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

ENV PYTHONPATH=/code

# COPY  ./pytest.ini /code/pytest.ini

# COPY ./src ./src

# COPY ./tests ./tests

# COPY ./static ./static

# CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--reload"]
