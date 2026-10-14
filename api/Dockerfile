FROM python:3.12-slim

WORKDIR /app

# Cache dependencies in their own layer so `docker build` only re-installs
# them when requirements.txt actually changes. --only-binary forces prebuilt
# wheels, so no dependency's setup.py/build script ever runs during install.
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt

COPY app ./app

# fastembed downloads its ONNX model on first use; FASTEMBED_CACHE_PATH
# points it at a path that docker-compose mounts as a named volume, so the
# ~100 MB download survives container restarts.
ENV FASTEMBED_CACHE_PATH=/cache/fastembed

# Run as a non-root user rather than the image's default root. Needs a real
# home directory: huggingface_hub writes its own cache/log files under $HOME,
# separately from FASTEMBED_CACHE_PATH above.
RUN groupadd --system app && useradd --system --create-home --gid app app \
    && mkdir -p /cache/fastembed && chown -R app:app /cache/fastembed
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
