###################
### Build stage ###
###################
FROM python:3.11-slim AS build

ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH" \
    APP_DIR=/app

# Install build dependencies (glibc-based)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    librdkafka-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv ${VIRTUAL_ENV} && \
    pip install --upgrade pip && \
    pip install poetry

WORKDIR ${APP_DIR}

# Install Python deps
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-ansi && \
    rm -rf /root/.cache/pip

# Copy application code
COPY . .


#####################
### Runtime stage ###
#####################
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/venv \
    PATH="/venv/bin:$PATH" \
    APP_DIR=/app \
    KAFKA_SCRIPT=/start-kafka

# Runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    librdkafka1 \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_DIR}

# Copy venv + app
COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=build ${APP_DIR} ${APP_DIR}

# Optimize binary size
RUN strip --strip-unneeded /venv/bin/* || true

# Entrypoint
COPY ./deployment/local/kafka/start ${KAFKA_SCRIPT}
RUN sed -i 's/\r$//' ${KAFKA_SCRIPT} && chmod +x ${KAFKA_SCRIPT}

# Set the working directory to the Django project root
WORKDIR ${APP_DIR}/crosslink
CMD ["/bin/sh", "/start-kafka"]
