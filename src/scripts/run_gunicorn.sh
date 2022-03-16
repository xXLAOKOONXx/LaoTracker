#!/bin/sh

# Script to run web app with gunicorn

# Install poetry packages
poetry install

# kill all existing gunicorn processes
# TODO: Do not kill all gunicorns, but just the relevant one
pkill gunicorn

# Start the app on port 80
poetry run gunicorn lao_tracker.app:server -b :80