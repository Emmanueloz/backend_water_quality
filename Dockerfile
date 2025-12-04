FROM python:3.13.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependencias del sistema necesarias para numpy/pandas/matplotlib/scikit-learn
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    libjpeg62-turbo \
    zlib1g \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiamos solo requirements primero (para cache)
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Crear usuario seguro
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
