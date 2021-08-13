FROM python:3.7-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

ENTRYPOINT [ "python", "-u", "./main.py" ]
