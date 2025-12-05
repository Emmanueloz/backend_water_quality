# Imagen base de Python
FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer el puerto de FastAPI
EXPOSE 3000

# Comando para ejecutar FastAPI usando el paquete app/
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]
