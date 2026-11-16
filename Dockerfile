# datasniff as a container: profile a file without installing Python.
#   docker run --rm -v "$PWD:/data" ghcr.io/kaajjalchoudhary/datasniff orders.csv
FROM python:3.12-slim

LABEL org.opencontainers.image.description="Profile, validate and generate dbt tests and DDL for CSV, Parquet and JSON files"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --create-home sniff

USER sniff
WORKDIR /data
ENTRYPOINT ["datasniff"]
CMD ["--help"]
