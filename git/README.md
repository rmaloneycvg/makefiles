# Git Workflow Makefile

Automated git operations — branch comparison, AI-assisted commits, squash merges, and GitHub releases.

## Prerequisites

- **git** — version control
- **kiro-cli** — AI commit message generation (for `git-commit`)
- **gh CLI** — GitHub releases (for `git-release`)
- **Python 3.12+** — squash and whitespace resolution scripts

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PY` | `python3` | Python interpreter |
| `SCRIPTS_DIR` | `$(HOME)/workspace/makefiles/scripts` | Path to helper scripts |
| `b` | `main` | Target branch for comparisons |
| `SIDE` | `theirs` | Conflict resolution preference |
| `BASE_MSG` | `Squashed commits` | Default squash commit message |
| `k` | `1` | Use kiro for squash messages (0/1) |

## Targets

### `git-changed`

List uncommitted files (staged + unstaged).

```bash
gmake git-changed
```

### `git-changed-branch`

List all files changed in the current branch vs a target.

```bash
gmake git-changed-branch b=main
gmake git-changed-branch b=development
```

### `git-compare`

Diff current state against a target branch. Supports VS Code difftool and name-only mode.

```bash
# Terminal diff
gmake git-compare b=main

# VS Code difftool
gmake git-compare b=main v=1

# Name-only (just file paths)
gmake git-compare b=main n=1
```

### `git-squash`

Squash commits on the current branch.

```bash
gmake git-squash b=main
gmake git-squash b=main m="feat: add user auth"
gmake git-squash n=3
```

### `resolve-whitespace`

Auto-resolve whitespace-only merge conflicts.

```bash
gmake resolve-whitespace
gmake resolve-whitespace SIDE=ours
```

### `git-commit`

Commit staged changes with an AI-generated commit message via kiro-cli.

```bash
git add src/auth.py
gmake git-commit
gmake git-commit m="feat(auth)"
```

### `git-release`

Create a GitHub release by merging a source branch into a release branch.

```bash
gmake git-release v=1.0.0
gmake git-release v=2.1.0 b=staging r=production
```
