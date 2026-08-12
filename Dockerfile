# Skiptracer — Python 3 OSINT web-scraping framework
FROM python:3.13-slim

LABEL org.opencontainers.image.title="skiptracer" \
      org.opencontainers.image.version="4.0.0" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.description="OSINT web-scraping framework (Python 3)."

WORKDIR /app

# Install build deps, then the package (leverages Docker layer caching).
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN pip3 install --no-cache-dir .

# Drop into the source tree and launch the CLI (interactive by default;
# `docker run skiptracer --version` prints the version and exits).
WORKDIR /app/src
ENTRYPOINT ["python3", "-m", "skiptracer"]
