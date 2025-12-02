.PHONY: help build build-gpu up up-gpu down restart logs clean test status shell shell-backend install

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)PDF2Text Converter - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Create .env file from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file. Please review and adjust settings.$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists.$(NC)"; \
	fi

build: install ## Build Docker images (CPU mode)
	@echo "$(BLUE)Building Docker images (CPU mode)...$(NC)"
	docker-compose build

build-gpu: install ## Build Docker images (GPU mode)
	@echo "$(BLUE)Building Docker images (GPU mode)...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build

up: ## Start services (CPU mode)
	@echo "$(GREEN)Starting services (CPU mode)...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "Frontend: $(BLUE)http://localhost$(NC)"
	@echo "Backend API: $(BLUE)http://localhost:8000$(NC)"
	@echo "API Docs: $(BLUE)http://localhost:8000/docs$(NC)"

up-gpu: ## Start services (GPU mode)
	@echo "$(GREEN)Starting services (GPU mode)...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
	@echo "$(GREEN)Services started with GPU support!$(NC)"
	@echo "Frontend: $(BLUE)http://localhost$(NC)"
	@echo "Backend API: $(BLUE)http://localhost:8000$(NC)"
	@echo "API Docs: $(BLUE)http://localhost:8000/docs$(NC)"

down: ## Stop and remove services
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)Services stopped.$(NC)"

restart: down up ## Restart services (CPU mode)

restart-gpu: down up-gpu ## Restart services (GPU mode)

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

status: ## Show status of services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-backend: shell ## Alias for shell

clean: down ## Stop services and remove volumes
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Cleanup complete.$(NC)"

clean-all: clean ## Remove all Docker images and volumes
	@echo "$(YELLOW)Removing all images and volumes...$(NC)"
	docker-compose down -v --rmi all
	rm -rf uploads/*
	@echo "$(GREEN)Full cleanup complete.$(NC)"

test: ## Test the API with test.pdf
	@echo "$(BLUE)Testing API...$(NC)"
	@if [ ! -f uploads/test.pdf ]; then \
		echo "$(YELLOW)No uploads/test.pdf file found. Please add a test PDF.$(NC)"; \
		exit 1; \
	fi
	@echo "Testing extraction WITHOUT filtering..."
	@curl -s -X POST "http://localhost:8000/api/extract?use_ocr=true&chunk_processing=false&language=eng&remove_repetitive=false&remove_copyright=false" \
		-F "file=@uploads/test.pdf" | jq '{success, filename, pages, total_chars}' || echo "$(YELLOW)Test failed$(NC)"
	@echo ""
	@echo "Testing extraction WITH filtering..."
	@curl -s -X POST "http://localhost:8000/api/extract?use_ocr=true&chunk_processing=false&language=eng&remove_repetitive=true&remove_copyright=true" \
		-F "file=@uploads/test.pdf" | jq '{success, filename, pages, total_chars}' || echo "$(YELLOW)Test failed$(NC)"

test-all: ## Run comprehensive API tests
	@echo "$(BLUE)Running comprehensive tests...$(NC)"
	@bash tests/run-tests.sh

health: ## Check health of backend service
	@echo "$(BLUE)Checking backend health...$(NC)"
	@curl -s http://localhost:8000/health | jq '.' || echo "$(YELLOW)Backend not responding$(NC)"

dev: ## Start services in development mode with live reload
	@echo "$(GREEN)Starting in development mode...$(NC)"
	docker-compose up

rebuild: ## Rebuild and restart services (CPU mode)
	@echo "$(BLUE)Rebuilding services...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)Services rebuilt and started!$(NC)"

rebuild-gpu: ## Rebuild and restart services (GPU mode)
	@echo "$(BLUE)Rebuilding services (GPU mode)...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml down
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml build --no-cache
	docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
	@echo "$(GREEN)Services rebuilt and started with GPU support!$(NC)"

ps: status ## Alias for status

upload-test: ## Upload a test PDF file
	@echo "$(BLUE)Uploading test PDF...$(NC)"
	@if [ -f prova.pdf ]; then \
		curl -X POST "http://localhost:8000/api/extract" \
			-F "file=@prova.pdf" \
			-F "use_ocr=true" \
			-F "chunk_processing=true" \
			-F "language=eng"; \
	else \
		echo "$(YELLOW)No prova.pdf file found.$(NC)"; \
	fi

info: ## Show system information
	@echo "$(BLUE)System Information:$(NC)"
	@echo "Docker version: $$(docker --version)"
	@echo "Docker Compose version: $$(docker-compose --version)"
	@if command -v nvidia-smi &> /dev/null; then \
		echo "$(GREEN)NVIDIA GPU detected:$(NC)"; \
		nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader; \
	else \
		echo "$(YELLOW)No NVIDIA GPU detected$(NC)"; \
	fi
