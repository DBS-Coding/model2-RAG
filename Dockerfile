FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


COPY key.json /app/key.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/key.json

CMD ["python", "main.py"]
