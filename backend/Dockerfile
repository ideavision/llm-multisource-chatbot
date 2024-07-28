FROM python:3.11.7-slim-bookworm

# ARG PAYSERAI_VERSION=0.3-dev
# ENV PAYSERAI_VERSION=${PAYSERAI_VERSION}
# RUN echo "PAYSERAI_VERSION: 0.3-dev"

# Install system dependencies
# cmake needed for psycopg (postgres)
# libpq-dev needed for psycopg (postgres)
# curl included just for users' convenience
# zip for Vespa step futher down
# ca-certificates for HTTPS
RUN pwd && ls -la
RUN apt-get update && \
    apt-get install -y cmake curl zip ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Install Python dependencies
# Remove py which is pulled in by retry, py is not needed and is a CVE
COPY ./requirements/default.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt && \
    pip uninstall -y py && \
    playwright install chromium && playwright install-deps chromium && \
    ln -s /usr/local/bin/supervisord /usr/bin/supervisord

# Cleanup for CVEs and size reduction
# https://github.com/tornadoweb/tornado/issues/3107
# xserver-common and xvfb included by playwright installation but not needed after
# perl-base is part of the base Python Debian image but not needed for Payserai functionality
# perl-base could only be removed with --allow-remove-essential
RUN apt-get remove -y --allow-remove-essential perl-base xserver-common xvfb cmake libldap-2.5-0 libldap-2.5-0 && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm /usr/local/lib/python3.11/site-packages/tornado/test/test.key

# Set up application files
WORKDIR /app
COPY ./backend/payserai /app/payserai
COPY ./backend/shared_models /app/shared_models
COPY ./backend/alembic /app/alembic
COPY ./backend/alembic.ini /app/alembic.ini
COPY ./backend/supervisord.conf /usr/etc/supervisord.conf

# Create Vespa app zip
WORKDIR /app/payserai/document_index/vespa/app_config
RUN zip -r /app/payserai/vespa-app.zip .
WORKDIR /app

ENV PYTHONPATH /app

# Default command which does nothing
# This container is used by api server and background which specify their own CMD
CMD ["tail", "-f", "/dev/null"]
