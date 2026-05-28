# ====================================================================
# Infisical Secrets Makefile
# Requires: infisical CLI installed
# ====================================================================

SHELL := /bin/bash
PY             ?= python3
SCRIPTS_DIR    ?= $(HOME)/workspace/makefiles/scripts
INFISICAL_SYNC ?= $(PY) $(SCRIPTS_DIR)/infisical_sync.py
INFISICAL_ENV  ?= dev
INFISICAL_URL  ?= $(INFISICAL_API_URL)
INFISICAL_PROJECT_ID ?= $(INFISICAL_GLOBAL_CONFIG_ID)
INFISICAL_ORG  ?= $(INFISICAL_ORG_ID)

# Auto-update infisical.example manifest after changes
define update_manifest
	@if command -v infisical >/dev/null 2>&1; then \
		$(INFISICAL_SYNC) manifest --env $(INFISICAL_ENV) --out infisical.example 2>/dev/null || true; \
	fi
endef

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m [VAR=value ...]\n\n"} \
		/^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Authentication
.PHONY: infisical-login infisical-set-token infisical-init

infisical-login: ## Log in to Infisical CLI (opens browser)
	infisical login --domain $(INFISICAL_URL)

infisical-set-token: ## Log in via universal auth and print token
	@export INFISICAL_TOKEN=$$(infisical login \
		--domain "$(INFISICAL_URL)" \
		--method=universal-auth \
		--client-id="$(INFISICAL_UNIVERSAL_AUTH_CLIENT_ID)" \
		--client-secret="$(INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET)" \
		--silent \
		--plain); \
	echo "Token acquired: $$INFISICAL_TOKEN"

infisical-init: ## Initialize local project link (.infisical.json)
	infisical init --domain $(INFISICAL_URL)

##@ Secrets Management
.PHONY: infisical-push-env infisical-pull infisical-push infisical-export infisical-manifest infisical-get infisical-purge

infisical-push-env: ## Push .env key/value pairs to Infisical
	@while IFS='=' read -r key value; do \
		[ -z "$$key" ] || [ "$${key#\#}" != "$$key" ] && continue; \
		infisical secrets set "$$key=$$value" --env $(INFISICAL_ENV) --domain $(INFISICAL_URL) --silent; \
		echo "  ✓ $$key"; \
	done < .env
	@echo "✅ .env pushed to Infisical ($(INFISICAL_ENV))."

infisical-pull: ## Pull secrets from Azure Key Vault → Infisical
	@$(INFISICAL_SYNC) pull --provider azure --vault-name $(KV_NAME) --env $(INFISICAL_ENV)

infisical-push: ## Push secrets from Infisical → Azure Key Vault
	@$(INFISICAL_SYNC) push --provider azure --vault-name $(KV_NAME) --env $(INFISICAL_ENV)

infisical-export: ## Export Infisical secrets to stdout (dotenv format)
	@$(INFISICAL_SYNC) export --env $(INFISICAL_ENV) --format dotenv

infisical-manifest: ## Generate infisical.example (secret names only)
	@$(INFISICAL_SYNC) manifest --env $(INFISICAL_ENV) --out infisical.example

infisical-get: ## Get a single secret (usage: make get-secret key=SECRET_KEY)
	@$(INFISICAL_SYNC) get --env $(INFISICAL_ENV) --key $(key) --format plain

infisical-purge: ## Delete all secrets from Infisical project environment
	@infisical secrets --env $(INFISICAL_ENV) --domain $(INFISICAL_URL) --plain -o json 2>/dev/null | \
		$(PY) -c "import sys,json;[print(s['secretKey']) for s in json.loads(sys.stdin.read())]" | \
		while read -r key; do \
			infisical secrets delete "$$key" --env $(INFISICAL_ENV) --domain $(INFISICAL_URL) --type shared --silent; \
			echo "  🗑 $$key"; \
		done
	@echo "✅ All secrets purged from Infisical ($(INFISICAL_ENV))."

##@ Shell Init (for .zshrc)
.PHONY: infisical-shell-init

infisical-shell-init: ## Force login + export GlobalConfig/dev secrets as env vars
	@infisical login --domain $(INFISICAL_URL) >/dev/tty 2>/dev/tty
	@infisical export --env $(INFISICAL_ENV) --domain $(INFISICAL_URL) \
		--projectId "$(INFISICAL_PROJECT_ID)" --format dotenv | sed 's/^/export /'
