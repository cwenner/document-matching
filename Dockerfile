#       syntax=docker/dockerfile:1.4.2
FROM    ubuntu:22.04 AS base
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
RUN     --mount=type=cache,target=/root/.cache/pip \
        python3 -m pip wheel --wheel-dir=/whl -r /whl/requirements.txt
COPY    src /opt/omnicoder/matching

FROM    base AS final
EXPOSE  5024
RUN     --mount=target=/mnt,from=builder \
        --mount=type=cache,target=/root/.cache/pip \
        python3 -m pip install --no-index --find-links=/mnt/whl -r /mnt/whl/requirements.txt
COPY    src /opt/omnicoder/matching
ENV     PYTHONPATH=/opt/omnicoder/matching
CMD     ["sh","-xc","uvicorn --log-level=warning --port=5024 --host=0.0.0.0 app:app"]
