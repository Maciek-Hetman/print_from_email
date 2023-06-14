# Print from email

## Local setup

``` bash
pip3 install pipenv
pipenv install
pipenv shell
mv config_sample.json config.json
nano config.json
python3 manage.py migrate
python3 runserver_daemon
```

You may have to adjust ip address in runserver_daemon.py if it defaults to 127:0.1.1:8000

## Docker setup

- Create my_secrets/secrets.py with your Django secret key inside `SECRET_KEY = "Your secret key"`
- Rename config_sample.json to config.json and edit the file with your email credentials
- Check your ip address with `ifconfig` or `ip addr`
- Replace temporary IP address and hostname in docker-compose.yml with your IP address and hostname
- `docker-compose build`
- `docker-compose up`
