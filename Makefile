.PHONY: help install setup run test clean docker-build docker-run docker-stop

help:
	@echo "Cardiology RAG Bot - Make Commands"
	@echo "=================================="
	@echo "install        - Install dependencies"
	@echo "setup          - Process PDF and build vector store"
	@echo "run            - Run the Telegram bot"
	@echo "test           - Run tests"
	@echo "clean          - Clean generated files"
	@echo "docker-build   - Build Docker image"
	@echo "docker-run     - Run with Docker Compose"
	@echo "docker-stop    - Stop Docker containers"
	@echo "logs           - View bot logs"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

setup:
	@echo "Setting up RAG system..."
	python setup.py

run:
	@echo "Starting Telegram bot..."
	python -m src.telegram_bot

test:
	@echo "Running tests..."
	pytest tests/ -v

clean:
	@echo "Cleaning generated files..."
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -rf build dist
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

clean-all: clean
	@echo "Cleaning all data..."
	rm -rf chroma_db logs

docker-build:
	@echo "Building Docker image..."
	docker-compose build

docker-run:
	@echo "Starting with Docker Compose..."
	docker-compose up -d

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f

logs:
	@echo "Viewing logs..."
	tail -f logs/telegram_bot.log
