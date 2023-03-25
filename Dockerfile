FROM python:bullseye
LABEL authors="cheaterpaul"

WORKDIR /app

ENV DB_DATABASE modstats
ENV DB_PORT 3306
ENV DB_USER modstats

RUN apt-get update && apt-get install -y gcc wget cron vim python3-pymysql python3-requests
RUN pip3 install pymysql requests

COPY main.py .
COPY run.sh .
COPY start.sh .
COPY cronjob /etc/cron.d/cronjob

RUN chmod 0644 /etc/cron.d/cronjob && crontab /etc/cron.d/cronjob


CMD /app/start.sh