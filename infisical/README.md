# Infisical Secrets Makefile

Manage secrets via [Infisical](https://infisical.com/) — push/pull between local `.env` files, cloud vaults (Azure Key Vault, AWS Secrets Manager), and Infisical's central store.

All targets are prefixed with `infisical-`.

## Prerequisites

- **Infisical CLI** — `infisical login` completed
- **Python 3.12+** — for the sync script
- **Running Infisical instance** — default: `http://localhost:9999/api`

## Setup

### 1. Configure environment variables

In `~/.infisical.env`:

```bash
export INFISICAL_API_URL="http://localhost:9999/api"
export INFISICAL_GLOBAL_CONFIG_ID="<your-project-id>"
export INFISICAL_ORG_ID="<your-org-id>"
```

### 2. Login

```bash
gmake infisical-login
```

### 3. Initialize project link

```bash
cd ~/workspace/makefiles/azure  # or any project dir
gmake infisical-init
```

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PY` | `python3` | Python interpreter |
| `SCRIPTS_DIR` | `$(HOME)/workspace/makefiles/scripts` | Scripts directory |
| `INFISICAL_SYNC` | `$(PY) $(SCRIPTS_DIR)/infisical_sync.py` | Sync script |
| `INFISICAL_ENV` | `dev` | Environment slug (dev/staging/prod) |
| `INFISICAL_URL` | `$(INFISICAL_API_URL)` | API endpoint |
| `KV_NAME` | — | Azure Key Vault name (for pull/push) |

## Targets

| Target | Description |
|--------|-------------|
| `infisical-login` | Open browser login to Infisical |
| `infisical-set-token` | Login via universal auth (CI/CD) and print token |
| `infisical-init` | Initialize `.infisical.json` in current directory |
| `infisical-push-env` | Push all `.env` key/value pairs to Infisical |
| `infisical-pull` | Pull secrets from Azure Key Vault into Infisical |
| `infisical-push` | Push secrets from Infisical to Azure Key Vault |
| `infisical-export` | Export secrets to stdout in dotenv format |
| `infisical-manifest` | Generate `infisical.example` (names only, safe to commit) |
| `infisical-get` | Get a single secret value |
| `infisical-purge` | Delete ALL secrets from environment (**destructive**) |
| `infisical-shell-init` | Force login + export secrets as env vars (for `.zshrc`) |

## Examples

```bash
# Login and initialize
gmake infisical-login
gmake infisical-init

# Push local .env to Infisical
gmake infisical-push-env
gmake infisical-push-env INFISICAL_ENV=staging

# Export for shell use
eval "$(gmake infisical-export)"

# Sync with Azure Key Vault
gmake infisical-pull KV_NAME=kv-myapp
gmake infisical-push KV_NAME=kv-myapp INFISICAL_ENV=prod

# Get a single secret
gmake infisical-get key=DATABASE_URL

# Generate manifest (commit-safe)
gmake infisical-manifest
```
