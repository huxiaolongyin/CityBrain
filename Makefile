.PHONY: build-dev

build-dev:
	docker compose -f docker-compose-dev.yml up -d --build