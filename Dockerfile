FROM python:latest

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN dpkg --add-architecture i386
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential cups libcups2 libcups2-dev python3-dev libcups2:i386 cups-client telnet

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

# Copy virtual env from python-deps stage
ENV PATH="/.venv/bin:$PATH"

# Install application into container
COPY . /app
WORKDIR /app

EXPOSE 8000

# Run the application
ENTRYPOINT [ "python3", "runserver_daemon.py" ]
