FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE ${PORT}

CMD ["python", "src/app.py"]
