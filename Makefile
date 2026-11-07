-include .env

PYTHON      = python3
ENV         = .venv/
RAW         = data/raw/vllm-0.10.1/docs/

MAX_CHUNK_SIZE  = 2000

OLLAMA_LOG      = .ollama.log
QDRANT_STORAGE  = qdrant_storage/

METHOD  = bm25
K       = 10
KEEP    = 3
Q       =

GREEN   = \033[0;32m
CYAN    = \033[0;36m
YELLOW  = \033[0;33m
RED     = \033[0;31m
BOLD    = \033[1m
RESET   = \033[0m

.PHONY: all help install lint \
	check-ollama up down clean fclean re \
	index retrieve answer check-q

all: help

help:
	@printf "$(BOLD)RAG$(RESET) — available targets\n\n"
	@printf "$(BOLD)Setup$(RESET)\n"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "install"  "Install dependencies via uv"
	@printf "\n$(BOLD)Services$(RESET)\n"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "up"       "Check ollama, start ollama serve + Qdrant container"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "down"     "Stop the Qdrant container"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "clean"    "down + stop ollama serve + remove venv, index, caches"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "fclean"   "clean + delete Qdrant storage"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "re"       "clean + up"
	@printf "\n$(BOLD)Pipeline$(RESET)\n"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "index"    "Index RAW with METHOD"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "retrieve" "Top-K chunks for Q=\"...\""
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "answer"   "LLM answer for Q=\"...\" (needs make up)"
	@printf "\n$(BOLD)Lint$(RESET)\n"
	@printf "  $(CYAN)%-12s$(RESET) %s\n" "lint"        "flake8 + mypy (standard rules)"
	@printf "\n$(BOLD)Overridable variables$(RESET)\n"
	@printf "  $(YELLOW)%-16s$(RESET) %s\n" "RAW"            "$(RAW)"
	@printf "  $(YELLOW)%-16s$(RESET) %s\n" "METHOD"         "$(METHOD)"
	@printf "  $(YELLOW)%-16s$(RESET) %s\n" "K"              "$(K)"
	@printf "  $(YELLOW)%-16s$(RESET) %s\n" "KEEP"           "$(KEEP)"
	@printf "  $(YELLOW)%-16s$(RESET) %s\n" "MAX_CHUNK_SIZE" "$(MAX_CHUNK_SIZE)"
	@printf "\n$(BOLD)Example$(RESET)\n"
	@printf "  make answer Q=\"what is BM25?\" K=5\n"

install:
	@uv sync


check-ollama:
	@command -v ollama >/dev/null 2>&1 || { \
		printf "$(RED)ollama is not installed: https://ollama.com/download$(RESET)\n"; exit 1; }

up: check-ollama
	@if curl -sf $(OLLAMA_URL) >/dev/null 2>&1; then \
		printf "$(GREEN)ollama already running at $(OLLAMA_URL)$(RESET)\n"; \
	else \
		printf "$(GREEN)Starting ollama serve (logs: $(OLLAMA_LOG))...$(RESET)\n"; \
		OLLAMA_HOST=$(OLLAMA_URL) nohup ollama serve > $(OLLAMA_LOG) 2>&1 & \
	fi
	@docker compose up -d

down:
	@docker compose down

clean: down
	@pkill -f "ollama serve" 2>/dev/null || true
	@printf "$(GREEN)Services stopped.$(RESET)\n"
	@echo "$(GREEN)Cleaning temporary files and caches...$(RESET)"
	@rm -rf ${ENV}
	@rm -rf .uv_cache
	@rm -rf .hf_cache
	@rm -f $(OLLAMA_LOG)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.pyd" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(RESET)"

fclean: clean
	@rm -rf $(QDRANT_STORAGE)
	@rm -rf ${CHUNKS_DIR}
	@rm -rf ${INDEX_DIR}
	@printf "$(GREEN)Qdrant storage $(QDRANT_STORAGE) removed.$(RESET)\n"

re: clean up

check-q:
	@test -n "$(Q)" || { printf "$(RED)Usage: make $(MAKECMDGOALS) Q=\"your question\"$(RESET)\n"; exit 1; }

index:
	@uv run $(PYTHON) -m src index $(RAW) --max-chunk-size $(MAX_CHUNK_SIZE) --method $(METHOD)

retrieve: check-q
	@uv run $(PYTHON) -m src retrieve "$(Q)" -k $(K) --method $(METHOD)

answer: check-q
	@uv run $(PYTHON) -m src answer "$(Q)" -k $(K) --keep $(KEEP) --method $(METHOD)


lint:
	@echo "$(GREEN)Running linters...$(RESET)"
	@uv run flake8 --exclude=$(ENV),${UV_CACHE},${RAW},data/ .
	@uv run mypy . --exclude '$(ENV)|${UV_CACHE}|${RAW},data/' \
		--warn-return-any --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs
	@echo "$(GREEN)Lint complete!$(RESET)"
