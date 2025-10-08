#!/bin/bash

echo "System Info:"
uname -a

echo

# array of network names
NETWORKS=("net-auth")

for NETWORK in "${NETWORKS[@]}"; do
    if ! docker network inspect "$NETWORK" > /dev/null 2>&1; then
        echo "Creating network: $NETWORK"
        docker network create "$NETWORK"
    else
        echo "Network '$NETWORK' already exists ✅"
    fi
done
echo

# array of network names
VOLUMES=("vol-pgadmin" "vol-db-auth")

for VOLUME in "${VOLUMES[@]}"; do
    if ! docker volume inspect "$VOLUME" > /dev/null 2>&1; then
        echo "Creating volume: $VOLUME"
        docker volume create "$VOLUME"
    else
        echo "Volume '$VOLUME' already exists ✅"
    fi
done
