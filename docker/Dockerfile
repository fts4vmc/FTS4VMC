FROM debian:bullseye-slim

WORKDIR /app

COPY src ./src
COPY requirements.txt ./
COPY vmc65-linux ./
COPY docker ./docker

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3-pip graphviz
RUN pip install --no-cache-dir -r requirements.txt



EXPOSE 5000

ENV FLASK_APP=src/fts.py
ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
