# Build context for this Dockerfile is the REPO ROOT (not backend/), so it
# can bake data/sample/ into the image -- see docker-compose.yml and
# render.yaml, both of which set the backend service's build context to ".".
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends default-libmysqlclient-dev build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Bundled synthetic placeholder sample videos (see data/sample/README.md).
# Baking these into the image means video playback works out of the box on
# any platform, including Render, where there's no host volume mount.
# (Only *.mp4 is copied -- not data/sample/'s README/script -- so the
# static mount at /media/sample only ever serves video files.)
COPY data/sample/*.mp4 /media/sample/

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
