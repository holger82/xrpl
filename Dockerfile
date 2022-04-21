FROM python:3.9-slim-bullseye

COPY requirements.txt ./

RUN pip install -r requirements.txt

EXPOSE 80

COPY log.ini ./
COPY ./app /app
COPY .env ./

RUN mkdir /var/log/xrpl/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--log-config", "log.ini"]