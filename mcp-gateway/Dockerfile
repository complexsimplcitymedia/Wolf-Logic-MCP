FROM python:3.12-slim

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fastapi_server.py .

EXPOSE 8080

CMD ["python", "fastapi_server.py"]
