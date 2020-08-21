FROM debian:bullseye-slim

WORKDIR /app

COPY *.py ./
COPY static ./static
COPY templates ./templates
COPY requirements.txt ./
COPY docker ./docker

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3-pip
RUN pip install --no-cache-dir -r requirements.txt



EXPOSE 5000

ENV FLASK_APP=fts.py
ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
