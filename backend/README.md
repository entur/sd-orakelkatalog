# FDK LLM Python Backend

A simple fastapi project made with Python

## Requirements

Requirement        | Installation | Version  | Description
------------------ | ------------ | -------- | ----------------
Python             | Pre-installed on most systems | >2.7 (Poetry will take care of rest)     | Interpreter
Docker (optional!) | <https://docs.docker.com/get-docker/> | Recent | Builds images and runs containers
Poetry             | [See the docs here](https://python-poetry.org/docs/#osx-linux-bashonwindows-install-instructions) | ^1.1     | Version Management for Python projects

## Install

To install this project's package run:

```command
poetry shell
poetry install
```

## Run locally

### Run natively

```command
poetry run uvicorn --port 8080 --reload rocketlaunch.main:app
```

### Access locally

With the server running natively (or in `Docker`), visit <http://localhost:8080>.

### Run tests

```command
poetry run pytest tests --ignore=tests/resources --junitxml=junit/test-results.xml --cov=rocketlaunch/ --cov-report=xml --cov-report=html
```

### Docker

#### Build

```command
docker build . -f Dockerfile -t rocketlaunch
```

#### Run

```command
docker run -p 8080:8080 rocketlaunch:latest
```
