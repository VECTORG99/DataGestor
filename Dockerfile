# Dockerfile - Desarrollo de Gestión de Datos para IA

# Utilizar una imagen oficial de Python
FROM python:3.9-slim

# Evitar que Python genere archivos .pyc y habilitar modo unbuffered
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias de sistema y herramientas necesarias
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    git \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar el Google Cloud SDK para interactuar con BigQuery
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# El comando por defecto será una shell interactiva
CMD ["/bin/bash"]
