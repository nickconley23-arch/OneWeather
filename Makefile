# OneWeather Development Makefile

.PHONY: help build up down logs test clean db-shell api-shell ingest-shell

help: ## Show this help
	@echo "OneWeather Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose -f docker-compose.yml -f docker-compose.override.yml build

up: ## Start all services
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

down: ## Stop all services
	docker-compose -f docker-compose.yml -f docker-compose.override.yml down

logs: ## View logs from all services
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f

logs-api: ## View API logs
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f api

logs-ingestion: ## View ingestion logs
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f ingestion

logs-db: ## View database logs
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f db

test: ## Run tests
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec api pytest tests/
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion pytest tests/

test-api: ## Run API tests only
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec api pytest tests/

test-ingestion: ## Run ingestion tests only
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion pytest tests/

clean: ## Remove all containers, volumes, and images
	docker-compose -f docker-compose.yml -f docker-compose.override.yml down -v --rmi all

db-shell: ## Open PostgreSQL shell
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec db psql -U postgres -d oneweather

api-shell: ## Open shell in API container
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec api bash

ingest-shell: ## Open shell in ingestion container
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion bash

ingest-gfs: ## Run GFS ingestion for latest cycle
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion python3 gfs_poc.py --cycle 00 --forecast-hour 0

ingest-gfs-test: ## Test GFS ingestion with small file
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion python3 gfs_poc.py --cycle 00 --forecast-hour 0 --resolution 1p00

migrate: ## Run database migrations
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec api alembic upgrade head

format: ## Format code with black and isort
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec api black app tests
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec api isort app tests
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion black .
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion isort .

type-check: ## Run type checking with mypy
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec api mypy app
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec ingestion mypy .

status: ## Show service status
	docker-compose -f docker-compose.yml -f docker-compose.override.yml ps

init-db: ## Initialize database with schema
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec db psql -U postgres -d oneweather -f /docker-entrypoint-initdb.d/init.sql

monitor: ## Open monitoring dashboards
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "PgAdmin: http://localhost:5050 (admin@oneweather.dev/admin)"

# Development shortcuts
dev: build up ## Build and start development environment
	@echo "Development environment started!"
	@echo "Run 'make monitor' for dashboard URLs"
	@echo "Run 'make logs' to view logs"

reset: down clean ## Complete reset (stop, remove volumes, remove images)
	@echo "Environment completely reset"

.PHONY: git-push
git-push: ## Commit and push all changes with timestamp
	git add .
	git commit -m "Auto-commit: $(shell date +'%Y-%m-%d %H:%M:%S')"
	git push origin main