# Python 3.14
FROM python:3.14-slim

WORKDIR /app

# Instalar dependencias (equivale a "buildCommand" de Render)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Puerto (equivale a "PORT" de Render)
EXPOSE 7860

# Comando de inicio (equivale a "startCommand" de Render)
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "app:app", "--bind", "0.0.0.0:7860"]