# Using multi-stage build to minimize the final image size

# Stage 1: Builder
FROM python:3.11-slim AS builder

RUN apt-get update && \
    apt-get install -y git curl && \ 
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: Final image
FROM python:3.11-slim


RUN apt-get update && \
    apt-get install -y curl --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

ENV PYTHONPATH=/app
ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE ${PORT}

CMD ["python", "src/app.py"]