# Makefile — IntelliDD Pro developer commands
# Usage: make <target>

.PHONY: run test lint clean setup install-playwright check

# ── App ───────────────────────────────────────────────────────────────────────
run:
	uv run streamlit run main.py

run-debug:
	LANGCHAIN_TRACING_V2=true uv run streamlit run main.py

# ── Pipeline CLI (quick test without UI) ─────────────────────────────────────
research:
	@read -p "Enter company URL: " url; uv run python pipeline/runner.py $$url

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	uv run pytest tests/ -v --tb=short

test-fast:
	uv run pytest tests/ -v --tb=short -x   # stop on first failure

test-coverage:
	uv run pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Individual test files
test-config:
	uv run pytest tests/test_config.py -v

test-tools:
	uv run pytest tests/test_tools.py -v

test-detector:
	uv run pytest tests/test_change_detector.py -v

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	uv run black . --line-length 100
	uv run isort . --profile black

lint-check:
	uv run black . --check --line-length 100
	uv run isort . --check-only --profile black

type-check:
	uv run mypy . --ignore-missing-imports --no-strict-optional

# ── Setup ─────────────────────────────────────────────────────────────────────
setup:
	uv sync
	uv run playwright install chromium
	cp .env.example .env
	@echo ""
	@echo " Setup complete!"
	@echo "   1. Edit .env and add your API keys"
	@echo "   2. Run: make run"

install:
	uv sync

install-playwright:
	uv run playwright install chromium

# ── Database ──────────────────────────────────────────────────────────────────
init-db:
	uv run python persistence/db.py

check-db:
	uv run python -c "
from persistence.db import init_db, get_db_stats
init_db()
stats = get_db_stats()
print('DB Stats:', stats)
"

# ── Validation ────────────────────────────────────────────────────────────────
check:
	uv run python config.py
	uv run python tools/llm_factory.py
	uv run python tools/search.py
	uv run python rag/vector_store.py
	uv run python persistence/db.py
	@echo " All checks passed!"

check-langsmith:
	uv run python -c "
from tools.observability import check_langsmith_config
cfg = check_langsmith_config()
for k, v in cfg.items():
    print(f'  {k}: {v}')
"

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo " Cleaned!"

clean-outputs:
	rm -rf outputs/*
	@echo " Outputs cleaned!"

clean-db:
	rm -f intellidd.db
	rm -rf chroma_store/
	@echo " Database cleaned! Run 'make init-db' to reinitialize."

clean-all: clean clean-outputs clean-db

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "IntelliDD Pro — Developer Commands"
	@echo "─────────────────────────────────────────────────"
	@echo "  make setup          First-time project setup"
	@echo "  make run            Start Streamlit app"
	@echo "  make research       Run pipeline via CLI"
	@echo "  make test           Run all tests"
	@echo "  make lint           Format code (black + isort)"
	@echo "  make check          Validate all tool connections"
	@echo "  make check-db       Show database stats"
	@echo "  make clean          Remove cache files"
	@echo "  make clean-all      Reset everything (DB + outputs)"
	@echo ""