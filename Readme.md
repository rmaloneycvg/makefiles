# Makefiles — Infrastructure & Developer Workflow Automation

A collection of self-contained Makefiles for managing cloud infrastructure (Azure, AWS), secrets (Infisical), git workflows, and developer utilities. All targets are accessible via a single `gmake` alias from anywhere in your terminal.

Every target is clearly prefixed by its module (`az-`, `aws-`, `infisical-`, `git-`, `docker-`, `code-`) so intent is unambiguous.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Quick Start](#quick-start)
- [Modules](#modules)
- [Variables Reference](#variables-reference)
- [Testing](#testing)
- [Examples & Use Cases](#examples--use-cases)

---

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| GNU Make 4.0+ | Task runner | `sudo apt install make` |
| [uv](https://docs.astral.sh/uv/) | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) | Azure infrastructure | `curl -sL https://aka.ms/InstallAzureCLIDeb \| sudo bash` |
| [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) | AWS infrastructure | See AWS docs |
| [Infisical CLI](https://infisical.com/docs/cli/overview) | Secrets management | `curl -1sLf https://dl.infisical.com/setup.deb.sh \| sudo -E bash && sudo apt install infisical` |
| [kiro-cli](https://github.com/aws/kiro-cli) | AI-assisted git commits | `npm install -g @anthropic-ai/kiro-cli` |
| [gh CLI](https://cli.github.com/) | GitHub releases | `sudo apt install gh` |
| Python 3.12+ | Helper scripts | Managed by uv |

---

## Installation & Setup

### 1. Clone the repo

```bash
git clone <your-repo-url> ~/workspace/makefiles
cd ~/workspace/makefiles
uv sync
```

### 2. Add to your `.zshrc`

```bash
# Python wrapper — auto-detects uv projects
python() {
  local target_dir="."
  local shifted=false
  local original_first_arg="$1"
  if [[ -n "$1" && -d "$1" ]]; then
    target_dir="$1"; shift; shifted=true
  fi
  if [[ -f "$target_dir/uv.lock" || -f "$target_dir/pyproject.toml" ]]; then
    uv run --directory "$target_dir" python "$@"
  elif [[ -d "$target_dir/.venv" ]]; then
    "$target_dir/.venv/bin/python" "$@"
  else
    if $shifted; then command python "$original_first_arg" "$@"; else command python "$@"; fi
  fi
}

# Primary invocation alias
alias gmake="make -f ~/Makefile"

# Infisical env vars (create from .infisical.env.example)
source "$HOME/.infisical.env"

# Auto-login and export secrets on shell start
eval "$(make -f ~/workspace/makefiles/infisical/Makefile infisical-shell-init)"
```

### 3. Create `~/.infisical.env`

Copy from the example and fill in your values:

```bash
cp ~/.infisical.env.example ~/.infisical.env
```

Required variables:

```bash
export INFISICAL_API_URL="http://localhost:9999/api"
export INFISICAL_GLOBAL_CONFIG_ID="<your-project-id>"
export INFISICAL_ORG_ID="<your-org-id>"
# Optional: for CI/CD universal auth
#export INFISICAL_UNIVERSAL_AUTH_CLIENT_ID=""
#export INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET=""
```

### 4. Get your Azure credentials

```bash
az login
az account show --query '{subscriptionId:id, tenantId:tenantId}' -o table
```

Set these in `~/workspace/makefiles/azure/.env`:

```
SUBSCRIPTION_ID=<your-subscription-id>
TENANT_ID=<your-tenant-id>
```

### 5. Configure AWS

```bash
aws configure
# Or use SSO:
aws sso login --profile your-profile
```

---

## Quick Start

```bash
# See all available targets
gmake help

# Azure: create a resource group
gmake az-create-rg PROJECT=myapp LOCATION=eastus

# AWS: create a secret
gmake aws-create-secret n=my-api-key v=sk-12345

# Git: commit staged changes with AI-generated message
gmake git-commit

# Search codebase
gmake code-search q="TODO" t=py
```

---

## Modules

| Module | Prefix | Description | README |
|--------|--------|-------------|--------|
| [git](git/) | `git-` | Git workflows — compare, squash, commit, release | [git/README.md](git/README.md) |
| [azure](azure/) | `az-` | Full Azure stack — RG, KV, Functions, APIM, VNet, Front Door | [azure/README.md](azure/README.md) |
| [aws](aws/) | `aws-` | Full AWS stack — Lambda, API GW, Cognito, S3, DynamoDB, RDS | [aws/README.md](aws/README.md) |
| [infisical](infisical/) | `infisical-` | Secrets management — push/pull/export/sync | [infisical/README.md](infisical/README.md) |
| [utilities](utilities/) | `docker-`, `code-` | Developer tools — search, fix-permissions | [utilities/README.md](utilities/README.md) |

---

## Variables Reference

All variables use `?=` (conditional assignment) — override via CLI or `.env` files.

### Global (all modules)

| Variable | Default | Description |
|----------|---------|-------------|
| `PY` | `python3` | Python interpreter |
| `INFISICAL_ENV` | `dev` | Infisical environment slug |
| `INFISICAL_SYNC` | `python3 ~/workspace/makefiles/scripts/infisical_sync.py` | Sync script path |

### Git

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRIPTS_DIR` | `$(HOME)/workspace/makefiles/scripts` | Scripts directory |
| `b` | `main` | Target branch |
| `SIDE` | `theirs` | Conflict resolution side |
| `BASE_MSG` | `Squashed commits` | Default squash message |

### Azure (`az-` prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT` | `myapp` | Project name (derives all resource names) |
| `LOCATION` | `eastus` | Azure region |
| `RG_NAME` | `rg-$(PROJECT)` | Resource group name |
| `KV_NAME` | `kv-$(PROJECT)` | Key Vault name |
| `FUNC_NAME` | `fn-$(PROJECT)` | Function App name |
| `APIM_NAME` | `agw-$(PROJECT)` | API Management name |

### AWS (`aws-` prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT` | `myapp` | Project name (derives all resource names) |
| `AWS_REGION` | `us-east-1` | AWS region |
| `BUCKET_NAME` | `st-$(PROJECT)` | S3 bucket name |
| `FUNC_NAME` | `fn-$(PROJECT)` | Lambda function name |
| `API_NAME` | `agw-$(PROJECT)` | API Gateway name |
| `POOL_NAME` | `auth-$(PROJECT)` | Cognito User Pool name |

---

## Invocation

**Primary (from anywhere):**

```bash
gmake <target> [VAR=value ...]
```

**Alternative:**

```bash
make -f ~/Makefile <target> [VAR=value ...]
```

**Standalone (from module directory):**

```bash
cd ~/workspace/makefiles/azure
make az-create-rg PROJECT=myapp
```

---

## Testing

The test suite uses pytest with three tiers:

```bash
cd ~/workspace/makefiles

# Run all non-destructive tests (dry-run + mock)
gmake test

# Dry-run only — validates every target parses correctly
gmake test-dryrun

# Mock tests — validates CLI command construction
gmake test-mock

# Integration tests — creates real cloud resources (with cleanup)
gmake test-integration
```

### Test markers

| Marker | Description |
|--------|-------------|
| `dryrun` | Syntax validation via `make -n` |
| `mock` | Command construction with fake CLI shims |
| `integration` | Live tests against real Azure/AWS/Infisical |

### Running directly with pytest

```bash
uv run pytest tests/test_dryrun_*.py -v          # 147 targets
uv run pytest tests/test_mock_*.py -v             # 17 command validations
uv run pytest tests/test_integration_*.py -v -m integration  # 10 live tests
```

---

## Examples & Use Cases

### Azure: Full stack provisioning

```bash
# Foundation
gmake az-create-rg PROJECT=webapp LOCATION=eastus
gmake az-create-kv PROJECT=webapp

# Monitoring
gmake az-create-app-insights PROJECT=webapp

# Compute
gmake az-create-storage env=dev use=functions STORAGE_NAME=stwebappfunc
gmake az-create-funcapp env=dev runtime=python
gmake az-create-funcapp-insights

# Auth
gmake az-create-app-reg PROJECT=webapp
gmake az-create-app-roles
gmake az-create-api-groups
gmake az-assign-groups-to-roles

# API Gateway
gmake az-create-apim PROJECT=webapp APIM_PUBLISHER_EMAIL=admin@example.com
gmake az-apim-add-funcapp swagger=https://fn-webapp.azurewebsites.net/api/swagger.json
gmake az-apim-restrict-funcapp
gmake az-apim-add-oauth

# Cleanup
gmake az-delete-rg PROJECT=webapp
```

### AWS: Serverless API

```bash
# Account setup
gmake aws-show-account

# Compute
gmake aws-create-lambda-role LAMBDA_ROLE_NAME=role-myapi-lambda
gmake aws-create-lambda FUNC_NAME=fn-myapi runtime=python3.12

# API
gmake aws-create-api-gw API_NAME=agw-myapi
gmake aws-create-user-pool POOL_NAME=auth-myapi
gmake aws-create-user-pool-client CLIENT_NAME=app-myapi callback=http://localhost:3000
gmake aws-api-gw-add-authorizer
gmake aws-api-gw-add-lambda FUNC_NAME=fn-myapi path=/items method=GET
gmake aws-api-gw-deploy stage=prod

# Cleanup
gmake aws-delete-secret n=my-secret
gmake aws-purge-secret n=my-secret
```

### Git: Daily workflow

```bash
# See what's changed
gmake git-changed
gmake git-changed-branch b=main

# Compare with VS Code difftool
gmake git-compare b=main v=1

# Commit with AI message
gmake git-commit

# Squash and merge
gmake git-squash b=main

# Create a release
gmake git-release v=1.2.0 b=development r=main
```

### Secrets: Sync workflow

```bash
# Login to Infisical
gmake infisical-login

# Push local .env to Infisical
gmake infisical-push-env

# Export secrets for shell
eval "$(gmake infisical-export)"

# Sync between Infisical and Azure Key Vault
gmake infisical-pull KV_NAME=kv-myapp
gmake infisical-push KV_NAME=kv-myapp

# AWS sync
gmake aws-pull-secrets
gmake aws-push-secrets
```

### Utilities

```bash
# Search all file types
gmake code-search q="connectionString"

# Search only Python files
gmake code-search q="import os" t=py

# Save results to file
gmake code-search q="TODO" o=1

# Fix Docker bind mount permissions
gmake docker-fix-permissions
```
