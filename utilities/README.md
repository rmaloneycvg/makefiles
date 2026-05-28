# Utilities Makefile

Developer productivity tools — codebase search and Docker permission fixes.

## Prerequisites

- **Python 3.12+** — for the search script
- **sudo** — for docker-fix-permissions

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PY` | `python3` | Python interpreter |
| `SCRIPTS_DIR` | `$(HOME)/workspace/makefiles/scripts` | Scripts directory |
| `SEARCH_PY` | `$(SCRIPTS_DIR)/search.py` | Search script path |
| `MAKEFILES_DIR` | `$(HOME)/workspace/makefiles` | Repo root (for test targets) |

## Targets

### `code-search`

Search the codebase for a string pattern. Supports file type filtering and output saving.

```bash
gmake code-search q="<term>" [t=<type>] [o=1]
```

| Param | Description |
|-------|-------------|
| `q` | Search term (required) |
| `t` | File type: `cs`, `js`, `sql`, `logs`, `py`, `docs`, `go`, `vb`, `java` |
| `o` | Set to `1` to save results to `scripts/search-results/` |

**Examples:**
```bash
gmake code-search q="connectionString"
gmake code-search q="import os" t=py
gmake code-search q="TODO" t=py o=1
gmake code-search q="CREATE TABLE" t=sql
```

### `docker-fix-permissions`

Fix file ownership after Docker bind mounts create root-owned files.

```bash
gmake docker-fix-permissions
```

### Testing targets

| Target | Description |
|--------|-------------|
| `test` | Run all non-destructive tests (dryrun + mock) |
| `test-dryrun` | Validate every target parses correctly |
| `test-mock` | Validate CLI command construction |
| `test-integration` | Run live tests (requires credentials) |
