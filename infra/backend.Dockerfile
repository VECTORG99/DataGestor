# Dockerfile - Desarrollo de Gestión de Datos para IA

ARG PYTHON_IMAGE=python:3.9-slim
FROM $PYTHON_IMAGE

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g $APP_GID appuser && useradd -m -u $APP_UID -g appuser appuser

WORKDIR /app
RUN chown -R appuser:appuser /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

USER appuser

CMD ["/bin/bash"]
