IMAGE    ?= ghcr.io/blackbms/resume-tracker
TAG      ?= latest

.PHONY: build up down restart publish logs

## Build the Docker image
build:
	docker compose build

## Start all containers in the background
up:
	docker compose up -d

## Stop and remove all containers
down:
	docker compose down

## Restart containers (full stop/start)
restart: down up

## Publish the image to GitHub Container Registry
## Usage: make publish TAG=1.0.0
publish:
	docker tag resume-tracker-web $(IMAGE):$(TAG)
	docker push $(IMAGE):$(TAG)

## Tail logs from all containers
logs:
	docker compose logs -f
