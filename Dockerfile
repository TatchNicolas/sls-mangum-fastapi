FROM python:3.8

RUN pip install poetry
RUN poetry config virtualenvs.create false

ADD pyproject.toml .
ADD poetry.lock .
RUN poetry install

ADD sls_mangum_fastapi sls_mangum_fastapi
