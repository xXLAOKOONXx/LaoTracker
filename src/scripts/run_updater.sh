#!/bin/sh

# Script to run updater

# Install poetry packages
poetry install


# Start the updater
poetry run nohup python lao_tracker/main.py