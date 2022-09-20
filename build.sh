#!/bin/bash


# AWS_PROFILE=osuka DJANGO_SETTINGS_MODULE=dognews.settings.local ./manage.py collectstatic

VERSION=$(head -1 VERSION)
COMMIT_ID=$(git rev-parse HEAD)
COMMIT_ID=${COMMIT_ID:0:8}
IMAGE_NAME=dognews-server
TAG=${VERSION}_${COMMIT_ID}
docker build -t local/${IMAGE_NAME}:${TAG} -t local/${IMAGE_NAME}:latest .
