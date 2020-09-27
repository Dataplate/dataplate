FROM python:3.8-slim-buster AS base

# Install 3rd party dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libldap2-dev \
      libpq-dev \
      libsasl2-dev \
      libssl-dev \
      python3-dev

# Setup virtual environment with all the dependencies
RUN python3 -m venv /opt/dataplate/venv
ENV PATH=/opt/dataplate/venv/bin:$PATH
COPY requirements.txt .
RUN pip install -r requirements.txt

# Build target image
FROM python:3.8-slim-buster AS target

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libldap-2.4-2 \
      libpq5 \
      libsasl2-2 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=base /opt/dataplate /opt/dataplate
COPY dataaccess /opt/dataplate/dataaccess
COPY migrations /opt/dataplate/migrations
COPY entrypoint.sh /opt/dataplate/

ENV PATH=/opt/dataplate/venv/bin:$PATH \
    FLASK_APP=dataaccess.app

WORKDIR /opt/dataplate

ENTRYPOINT ["/opt/dataplate/entrypoint.sh"]
CMD ["run"]
