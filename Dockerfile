FROM python:3.7

ADD . /src

WORKDIR /src

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "kopf", "run", "operator/handlers.py", "--verbose" ]
