FROM python:3.12-slim as python-base

# Poetry environment variables
ENV POETRY_VERSION=2.0.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VENV="/opt/poetry-venv" \
    POETRY_CACHE_DIR="/opt/poetry-cache"

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN python -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /home/app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-cache

# Copy project
COPY . .

# Run server
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]