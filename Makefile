.PHONY: dev

dev:
	docker compose -f docker-compose-dev.yml up -d --build

prod:
	docker compose -f docker-compose.yml up -d