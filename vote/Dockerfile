# Imagen del servicio WEB (Python)
FROM python:3.12-slim

WORKDIR /app

# Primero las dependencias: así Docker reutiliza esta capa si solo cambia el código.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:80", "--workers", "2", "--access-logfile", "-"]
