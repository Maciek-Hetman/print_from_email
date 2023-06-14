FROM python:latest as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

# Install pipenv
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc nano

# Install python deps in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

RUN ["mv", "config_sample.json", "config.json"]
RUN ["nano", "config.json"]

# Install application into container
COPY . .

# Run the application
ENTRYPOINT ["python3", "runserver_daemon.py"]
