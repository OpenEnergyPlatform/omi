#!/usr/bin/env bash

isort -rc *.py ./src/ ./tests/
black *.py src/ tests/
