FROM python:3.8

RUN mkdir -p /app
WORKDIR /app

COPY . .

RUN pip install -U pip && pip install -r requirements.txt

ENTRYPOINT ["python", "server.py"]