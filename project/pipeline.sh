#!/bin/bash

# # Exit immediately if a command exits with a non-zero status
# set -e

# # Install all dependencies defined in Pipfile
# pipenv install

# # Run the Python script within the pipenv environment

echo "Running pipeline.sh..."
python project/pipeline.py
echo "Pipeline completed successfully!"