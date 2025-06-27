#       syntax=docker/dockerfile:1.4.2
FROM    ubuntu:24.04 AS base

RUN     apt-get update && apt-get install -y \
        curl \
        python3 \
        python3-pip \
        ;

FROM    base AS builder
RUN     apt update && apt install -y \
        bash \
        build-essential \
        cargo \
        curl \
        git \
        jq \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-wheel \
        python3-yaml \
        rustc \
        ;

COPY    --link requirements.txt /whl/
COPY    --link requirements-dev.txt /whl/
RUN     --mount=type=cache,target=/root/.cache/pip \
        python3 -m pip -vvv wheel --wheel-dir=/whl -r /whl/requirements-dev.txt
COPY    src /opt/omnicoder/matching

# ===========================

# Isolated layer for credentials
FROM base AS fetch

RUN apt-get update && \
    apt-get install -y wget && \
    wget -O azcopy.tar.gz https://aka.ms/downloadazcopy-v10-linux

RUN mkdir -p /usr/local/azcopy && \
    tar -zxvf azcopy.tar.gz --strip-components=1 -C /usr/local/azcopy && \
    mv /usr/local/azcopy/azcopy /usr/local/bin/azcopy && \
    chmod 755 /usr/local/bin/azcopy

ENV SAS=sp=r&st=2025-04-11T14:51:43Z&se=2035-04-11T22:51:43Z&spr=https&sv=2024-11-04&sr=c&sig=UGBoGHgKEbBTUK6REUrwvGq%2BAwTKct02FcLl9VW3np0%3D

RUN mkdir /data
RUN azcopy copy "https://nuprodsandbox.blob.core.windows.net/models/document-pairing-svm.pkl?${SAS}" /data/document-pairing-svm.pkl --log-level=INFO

# ===========================

FROM    base AS final
WORKDIR /opt/omnicoder/matching
COPY    . .
ENV     PYTHONPATH=/opt/omnicoder/matching/src
RUN     mkdir -p ./models
COPY    --from=fetch /data/document-pairing-svm.pkl ./data/models/document-pairing-svm.pkl

# Kill PEP668
RUN     find /usr -name 'EXTERNALLY-MANAGED' -exec rm -f {} +

RUN     --mount=target=/mnt,from=builder \
        --mount=type=cache,target=/root/.cache/pip \
        python3 -m pip install --progress-bar off --no-index --find-links=/mnt/whl -r requirements.txt

RUN     --mount=type=cache,target=/root/.cache/pip \
        python3 -m nox -f noxfile.py -s test

# ===========================

EXPOSE  5024
CMD     ["sh","-xc","uvicorn --log-level=warning --port=5024 --host=0.0.0.0 app:app"]
