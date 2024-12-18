# Project name (adjust this if your project name is different)
PROJECT_NAME	:= ai_telegram

# FILES AND DIRS
COMPOSE_FILE	:= docker-compose.yml

# Docker compose command
DOCKER_COMPOSE	:= docker compose -f $(COMPOSE_FILE)

# Colors
BLUE := \033[34m
GREEN := \033[32m
RESET := \033[0m

# Help message
help:
	@echo "Available targets:"
	@echo "  run                    - Run the containers (detached)"
	@echo "  stop                   - Stop all running containers"
	@echo "  start                  - Start stopped containers"
	@echo "  remove                 - Remove the containers"
	@echo "  clean                  - Clean up secrets and environment files and prune system"
	@echo "  status                 - Show status of all containers"
	@echo "  help                   - Show this help message"

# Run containers in detached mode
run:
	@echo "$(BLUE)Starting containers ...$(RESET)"
	$(DOCKER_COMPOSE) up -d --force-recreate --build
	@echo "$(GREEN)Containers started$(RESET)"

# Stop all running containers
stop:
	@echo "$(BLUE)Stopping all containers ...$(RESET)"
	@$(DOCKER_COMPOSE) stop
	@echo "$(GREEN)Containers stopped$(RESET)"

# Start stopped containers
start:
	@echo "$(BLUE)Starting stopped containers ...$(RESET)"
	@$(DOCKER_COMPOSE) start
	@echo "$(GREEN)Containers started$(RESET)"

# Remove all containers
remove:
	@echo "$(BLUE)Removing containers ...$(RESET)"
	@$(DOCKER_COMPOSE) down -v
	@docker rm -f $$(docker ps -aq) || true
	@docker network rm $(PROJECT_NAME)_default 2>/dev/null || true
	@echo "$(GREEN)Containers removed$(RESET)"

# Clean up and prune docker system
clean: remove
	@echo "$(BLUE)Cleaning up and pruning Docker system ...$(RESET)"
	@docker system prune --all --force
	@echo "$(GREEN)Clean up and prune complete$(RESET)"

# Show status of all containers
status:
	@echo "$(BLUE)IMAGES OVERVIEW$(RESET)"
	@docker images
	@echo "$(BLUE)CONTAINER OVERVIEW$(RESET)"
	@docker ps -a
	@echo "$(BLUE)NETWORK OVERVIEW$(RESET)"
	@docker network ls
	@echo "$(BLUE)CONTAINER LOGS$(RESET)"
	@$(DOCKER_COMPOSE) logs

dev:
