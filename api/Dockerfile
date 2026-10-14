FROM python:3.12-slim

WORKDIR /app

# Cache dependencies in their own layer so `docker build` only re-installs
# them when requirements.txt actually changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# fastembed downloads its ONNX model on first use; FASTEMBED_CACHE_PATH
# points it at a path that docker-compose mounts as a named volume, so the
# ~100 MB download survives container restarts.
ENV FASTEMBED_CACHE_PATH=/cache/fastembed

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
