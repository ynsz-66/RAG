
PYTHON      = python3
ENV         = .venv/
UV_CACHE    = .uv_cache/
RAW         = data/raw/

CHUNKS_DIR      = data/processed/chunks/
BM25_DIR        = data/processed/bm25_index/
HISTORY_DIR     = .history/
MAX_CHUNK_SIZE  = 2000


GREEN   = \033[0;32m
CYAN    = \033[0;36m
YELLOW  = \033[0;33m
BOLD    = \033[1m
RESET   = \033[0m

.PHONY: all help install app lint lint-strict clean

all: help

help:
	@printf "$(BOLD)RAG$(RESET) — available targets\n\n"
	@printf "$(BOLD)Setup$(RESET)\n"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "install"  "Install dependencies via uv"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "clean"    "Remove venv, caches, index and chat history"
	@printf "\n$(BOLD)Pipeline$(RESET)\n"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "app"      "Launch the Textual UI (main_visu.py)"
	@printf "\n$(BOLD)Lint$(RESET)\n"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "lint"        "flake8 + mypy (standard rules)"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "lint-strict" "flake8 + mypy --strict"
	@printf "\n$(BOLD)Overridable variables$(RESET)\n"
	@printf "  $(YELLOW)%-16s$(RESET) %s\n" "MAX_CHUNK_SIZE" "$(MAX_CHUNK_SIZE)"

install:
	@uv sync

app:
	@uv run ${PYTHON} main_visu.py

lint:
	@echo "$(GREEN)Running linters...$(RESET)"
	@uv run flake8 --exclude=$(ENV),${UV_CACHE},${RAW} .
	@uv run mypy . --exclude '$(ENV)|${UV_CACHE}|${RAW}' \
		--warn-return-any --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs
	@echo "$(GREEN)Lint complete!$(RESET)"

lint-strict:
	@echo "$(GREEN)Running linters in strict mode...$(RESET)"
	@uv run flake8 --exclude=$(ENV),${UV_CACHE},${RAW} .
	@uv run mypy . --exclude '$(ENV)|${UV_CACHE}|${RAW}' --strict
	@echo "$(GREEN)Strict lint complete!$(RESET)"

clean:
	@echo "$(GREEN)Cleaning temporary files and caches...$(RESET)"
	@rm -rf ${ENV}
	@rm -rf ${CHUNKS_DIR}
	@rm -rf ${BM25_DIR}
	@rm -rf ${HISTORY_DIR}
	@rm -rf .uv_cache
	@rm -rf .hf_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.pyd" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(RESET)"
