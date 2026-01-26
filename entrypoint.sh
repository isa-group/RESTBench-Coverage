#!/bin/bash
set -e

# Read environment variables, default to 0 (root) if not set
CURRENT_UID=${HOST_UID:-0}
CURRENT_GID=${HOST_GID:-0}

# If UID is not 0, create the specified user
if [ "$CURRENT_UID" -ne 0 ]; then
    echo "Starting with specified UID: $CURRENT_UID, GID: $CURRENT_GID"

    groupadd -g "$CURRENT_GID" appgroup
    useradd -s /bin/bash -u "$CURRENT_UID" -g appgroup -m appuser

    # If the DOCKER_GID environment variable exists, configure the docker group
    if [ -n "$DOCKER_GID" ]; then
        # Check if the docker group exists, create it if it doesn't
        if ! getent group docker >/dev/null; then
            groupadd -g "$DOCKER_GID" docker
        else
            # If it exists, modify the GID
            groupmod -g "$DOCKER_GID" docker
        fi
        usermod -aG docker appuser
    fi

    chown -R appuser:appgroup /app

    mkdir -p /home/appuser

    if [ -d /root/.m2 ] && [ ! -d /home/appuser/.m2 ]; then
        cp -r /root/.m2 /home/appuser/
        chown -R appuser:appgroup /home/appuser/.m2
    fi

    # Use gosu to drop privileges to the newly created user and execute the command
    exec gosu appuser "$@"
else
    # Otherwise, execute the command directly as root
    echo "Starting as root"
    exec "$@"
fi