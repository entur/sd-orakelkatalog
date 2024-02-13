FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv" \
    DEBIAN_FRONTEND=noninteractive \
    DEBCONF_NONINTERACTIVE_SEEN=true \
    TZ=Europe/Oslo
# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

###############################################
# Builder Image
###############################################
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR $PYSETUP_PATH
#COPY \
#    poetry.lock  \
#    requirements.txt \
#    pyproject.toml \
#    ./
# Update, install, cleanup and user/group creation
# hadolint ignore=DL3008,DL3013
RUN apt-get update && \
    apt-get install --no-install-recommends -y build-essential tini && \
    # upgrade pip \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    poetry install --only main --no-ansi && \
    echo 'tzdata tzdata/Areas select Europe' | debconf-set-selections && \
    echo 'tzdata tzdata/Zones/Etc select Oslo' | debconf-set-selections && \
    # remove build dependencies and cache \
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip && \
    # gid/pid over 10k is best practice \
    groupadd -g 10101 appgroup && \
    useradd -u 10100 -g 10101 --create-home appuser
# run as appuser:appgroup
USER 10100:10101

# Copy the app code from the host machine
#COPY src/ rocketlaunch/

# Serve the application with the gunicorn server
# Arguments explanation:
# Spin up 1 worker (1x CPU core)
# Each worker can handle 8 concurrent requests
# Use the Uvicorn class worker (for asynchronous requests)
# Bind to port 8080
# Log all access to the app to stdout
# Serve the app found in the module rocketlaunch.main
EXPOSE 8080
# use tini as entrypoint, https://cloud.google.com/architecture/best-practices-for-building-containers
ENTRYPOINT ["/usr/bin/tini", "--", "gunicorn"]
# arguments to gunicorn
CMD [ "--workers", "1", "--threads", "8", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "--access-logfile", "-", "src.main:app" ]
