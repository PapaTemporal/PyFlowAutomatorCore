FROM python:3.11-slim-buster

WORKDIR /app
COPY . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 80

CMD [ "python", "run.py", "--http", "--host", "0.0.0.0", "--port", "80" ]