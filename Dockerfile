FROM python:latest

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN dpkg --add-architecture i386
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential cups libcups2 libcups2-dev python3-dev libcups2:i386 cups-client telnet

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


# Install application into container
COPY . /app
WORKDIR /app

RUN python3 manage.py migrate
RUN echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'example@gmail.com', 'password123')" | python3 manage.py shell

# Run the application
ENTRYPOINT [ "python3", "runserver_daemon.py" ]
