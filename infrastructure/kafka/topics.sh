#!/bin/bash
set -euo pipefail

KAFKA_BROKER=${KAFKA_BROKER:-localhost:9092}

echo "Creating Kafka topics..."

docker exec kafka kafka-topics --bootstrap-server "$KAFKA_BROKER" \
  --create --if-not-exists \
  --topic dip-events \
  --partitions 3 \
  --replication-factor 1

docker exec kafka kafka-topics --bootstrap-server "$KAFKA_BROKER" \
  --create --if-not-exists \
  --topic dip-dlq \
  --partitions 3 \
  --replication-factor 1

docker exec kafka kafka-topics --bootstrap-server "$KAFKA_BROKER" \
  --create --if-not-exists \
  --topic dip-enriched \
  --partitions 3 \
  --replication-factor 1

echo "Kafka topics created successfully."
docker exec kafka kafka-topics --bootstrap-server "$KAFKA_BROKER" --list
