# ====================================================================
# Utilities Makefile
# Requires: python3
# ====================================================================

PY            ?= python3
SCRIPTS_DIR   ?= $(HOME)/workspace/makefiles/scripts
SEARCH_PY     ?= $(SCRIPTS_DIR)/search.py
MAKEFILES_DIR ?= $(HOME)/workspace/makefiles

.PHONY: docker-fix-permissions
docker-fix-permissions: ## Fix file permissions after Docker bind mounts create root-owned files
	@echo "Fixing permissions in project directory..."
	@sudo chown -R $$(id -u):$$(id -g) .
	@echo "Done. You may need to restart your IDE to see changes."

.PHONY: code-search
code-search: ## Search codebase for a string (t: cs, js, sql, logs, or omit for all; o=1 saves output) | make code-search q="term" [t=cs] [o=1]
	@if [ -z "$(q)" ]; then \
		echo "Usage: make search q=\"<term>\" [t=cs|js|sql|logs|py|docs|java] [o=1]"; \
		exit 1; \
	fi
	@SAVE_FLAG=""; if [ -n "$(o)" ]; then SAVE_FLAG="--save"; fi; \
	if [ -n "$(t)" ]; then \
		$(PY) $(SEARCH_PY) "$(q)" "$(t)" $$SAVE_FLAG; \
	else \
		$(PY) $(SEARCH_PY) "$(q)" $$SAVE_FLAG; \
	fi

##@ Testing
.PHONY: test test-dryrun test-mock test-integration

test-dryrun: ## Run dry-run syntax tests on all Makefiles
	cd $(MAKEFILES_DIR) && uv run pytest tests/test_dryrun_*.py -v

test-mock: ## Run mock/stub tests
	cd $(MAKEFILES_DIR) && uv run pytest tests/test_mock_*.py -v

test-integration: ## Run integration tests (requires live credentials)
	cd $(MAKEFILES_DIR) && uv run pytest tests/test_integration_*.py -v -m integration

test: test-dryrun test-mock ## Run all non-destructive tests
