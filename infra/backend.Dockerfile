# Dockerfile - Desarrollo de Gestión de Datos para IA

# Utilizar una imagen oficial de Python
FROM python:3.9-slim

# Evitar que Python genere archivos .pyc y habilitar modo unbuffered
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias de sistema y herramientas necesarias
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# El comando por defecto será una shell interactiva
CMD ["/bin/bash"]
