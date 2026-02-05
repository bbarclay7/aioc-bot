CONDA_ENV   := aioc-bot
CONDA_PREFIX := $(shell conda run -n $(CONDA_ENV) python -c "import sys; print(sys.prefix)")
PYTHON       := $(CONDA_PREFIX)/bin/python
PIP          := $(CONDA_PREFIX)/bin/pip

.PHONY: setup install run dry-run clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Create conda env + install deps
	conda create -n $(CONDA_ENV) python=3.12 -y
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "Setup complete. Before running:"
	@echo "  1. ollama serve"
	@echo "  2. ollama pull llama3.1:8b"

install: ## Update deps in existing env
	$(PIP) install -r requirements.txt

run: ## Run the bot (requires AIOC hardware)
	$(PYTHON) main.py

dry-run: ## Run without hardware (system mic/speakers, no PTT)
	$(PYTHON) main.py --dry-run

monitor: ## Show live audio levels (calibrate VOX threshold)
	$(PYTHON) main.py --dry-run --monitor

clean: ## Remove logs
	rm -rf logs/*.wav logs/*.log
