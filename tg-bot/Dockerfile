FROM python:3.8

RUN mkdir -p /app
WORKDIR /app

COPY . .

ENV TOKEN="5488409861:AAHzpFNAAyDPehYJFcQN0oWisKdA3dHrkwQ"

RUN pip install -U pip aiogram && apt-get update && pip install -r requirements.txt

ENTRYPOINT ["python", "telegram_bot.py"]