ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .

RUN pip install uv && \
    uv pip install --system -e .

COPY . .

EXPOSE 8000


CMD alembic upgrade head && uvicorn app.main:app --host=0.0.0.0 --port=8000
