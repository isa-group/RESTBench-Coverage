#!/bin/bash
echo "UID=$(id -u)" > .env
echo "GID=$(id -g)" >> .env

if getent group docker >/dev/null; then
  echo "DOCKER_GID=$(getent group docker | cut -d: -f3)" >> .env
else
  echo "# DOCKER_GID is not set as docker group was not found" >> .env
fi

echo "Generated .env file for this machine:"
cat .env