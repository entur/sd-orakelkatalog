# Getting Started Python

A simple rocket-launch project made with Python

## Contribute

### Requirements

Requirement        | Installation | Version  | Description
------------------ | ------------ | -------- | ----------------
Python             | Pre-installed on most systems | >2.7 (Poetry will take care of rest)     | Interpreter
Docker (optional!) | <https://docs.docker.com/get-docker/> | Recent | Builds images and runs containers
Poetry             | [See the docs here](https://python-poetry.org/docs/#osx-linux-bashonwindows-install-instructions) | ^1.1     | Version Management for Python projects
pre-commit         | <https://pre-commit.com/#install> | Latest | Framework for managing and maintaining multi-language pre-commit hooks

### Add a new dependency

To add a new dependency to the project, just run `poetry add <package_name>`. This will install the package from the PyPi servers into the virtual environment, and record the installed version in `pyproject.toml` and in `poetry.lock`. When `poetry install` is run, the *exact* versions recorded in `poetry.lock` will be installed.

It is also possible to manually edit `pyproject.toml` to change, add or remove dependencies. Be aware that this won't have any effect on running `poetry install` unless you first run `poetry update` to apply the changes to your local environment and `poetry.lock`.

### Install

To install this project's package run:

```command
poetry shell
poetry install
pre-commit install
```

### Code format

This project makes use of the opinionated code formatting tool [Black](https://github.com/psf/black). This ensures consistency in code formatting across the project and avoids unnecessary flame wars over style.

It is recommended to run black automatically every time you change files. This is supported by use of the [pre-commit](https://pre-commit.com/) tool. To set it up, just run `pre-commit install` the first time you set up the project.

## Run locally

### Run natively

```command
poetry run uvicorn --port 8080 --reload rocketlaunch.main:app
```

### Access locally

With the server running natively (or in `Docker`, visit <http://127.0.0.1:8080/docs> to see all available endpoints and test them.

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

## Secret Manager

To add additional secrets for demo, you can add secrets using this command, or use terraform/api.
<https://cloud.google.com/sdk/gcloud/reference/secrets/create>

```sh
printf "50M3 53[R37" | \
  gcloud secrets create ROCKET-SCIENCE --data-file=- \
    --locations=europe-west1 \
    --project=$PROJECT \
    --replication-policy="user-managed"
```
