<<<<<<< HEAD
=======
# Python 3.14
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
FROM python:3.14-slim

WORKDIR /app

<<<<<<< HEAD
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
=======
# Instalar dependencias (equivale a "buildCommand" de Render)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Puerto (equivale a "PORT" de Render)
EXPOSE 7860

# Comando de inicio (equivale a "startCommand" de Render)
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "app:app", "--bind", "0.0.0.0:7860"]
>>>>>>> 24f7449b8031a198d335047b14c3df39f734c939
