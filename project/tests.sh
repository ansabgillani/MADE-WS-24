#!/bin/bash

set -e  # Exit immediately on error

echo "Running test.sh..."
bash ./project/pipeline.sh

echo "Running tests..."
python ./project/tests.py
