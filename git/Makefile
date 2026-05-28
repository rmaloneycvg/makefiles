# ====================================================================
# Git Workflow Makefile
# Requires: git, kiro-cli (for git-commit), gh CLI (for git-release)
# ====================================================================

PY             ?= python3
SCRIPTS_DIR    ?= $(HOME)/workspace/makefiles/scripts
GIT_SQUASH     ?= $(SCRIPTS_DIR)/git_squash.py
GIT_RESOLVE_WS ?= $(SCRIPTS_DIR)/git_resolve_whitespace.py

.PHONY: git-compare

# Default branch is main
b ?= "main"

# Set n=1 to enable name-only output
ifeq ($(n),1)
NAME_OPT = --name-only
else
NAME_OPT = 
endif

# Set v=1 to launch VS Code as your difftool
ifeq ($(v),1)
DIFF_CMD = git difftool --tool=vscode
else
DIFF_CMD = git diff
endif

git-compare: ## Compare unsync'd changes to a target branch, git-compare b=main v=1 n=1 | b -> target branch, v -> vscode difftool, n -> name-only output
	@echo "Comparing current state against $(b)..."
	@$(DIFF_CMD) --ignore-all-space $(NAME_OPT) $(b)

.PHONY: git-changed-branch
b ?= "main"
git-changed-branch: ## lists all files changed in this branch vs main
	@git diff --name-only $(b)...HEAD

.PHONY: git-changed
git-changed: ## lists uncommitted files
	@git status --short

BASE_MSG ?= Squashed commits
k ?= 1

.PHONY: git-squash
git-squash: ## Squash current branch onto target branch
	@$(PY) $(GIT_SQUASH) \
		--target-branch "$(if $(b),$(b),main)" \
		$(if $(n),--num-commits "$(n)") \
		$(if $(m),--message "$(m)") \
		--use-kiro $(k) \
		--base-msg "$(BASE_MSG)"

SIDE ?= theirs
.PHONY: resolve-whitespace
resolve-whitespace: ## Auto-resolves whitespace conflicts.
	@$(PY) $(GIT_RESOLVE_WS) --side $(SIDE)

.PHONY: git-commit
git-commit: ## Commit only staged changes with an AI-generated message
	@if git diff --cached --quiet; then \
		echo "Nothing to commit - no staged changes. Use 'git add' to stage files first."; \
	else \
		BASE_MSG=$$(kiro-cli chat --agent commit-msg -a -f plain --no-interactive "Generate a concise git commit message for these changes. Output ONLY the commit message, no introductory text.$$(echo; git diff --cached --stat | head -80)" | sed -e 's/\x1b\[[0-9;]*m//g' -e 's/\x1b\[//g' -e 's/^[> ]*//g' | tr -d '\000-\037' | grep -v '^$$' | head -1 | sed 's/[[:space:]]*$$//') && \
		if [ -n "$(m)" ]; then MSG="$(m) : $$BASE_MSG"; else MSG="$$BASE_MSG"; fi && \
		git commit -m "$$MSG"; \
		echo "Staged changes committed successfully."; \
	fi

.PHONY: git-release
git-release: ## Merge MAINBRANCH → RELEASEBRANCH and create a GitHub release | make git-release v=1.0.1 [b=development] [r=main]
	@if [ -z "$(v)" ]; then \
		echo "Error: Version parameter 'v' is required (e.g., make git-release v=1.0.1)"; \
		exit 1; \
	fi; \
	SRC="$(if $(b),$(b),$(or $(patsubst origin/%,%,$(MAINBRANCH)),development))"; \
	DST="$(if $(r),$(r),$(or $(patsubst origin/%,%,$(RELEASEBRANCH)),main))"; \
	echo "Merging $$SRC → $$DST and releasing $(v)..." && \
	gh pr create --base "$$DST" --head "$$SRC" --title "Release $(v)" --body "Merge $$SRC into $$DST for release $(v)" 2>/dev/null || true && \
	gh pr merge --merge --auto "$$SRC" 2>/dev/null || \
	gh api "workspace/{owner}/{repo}/merges" -f base="$$DST" -f head="$$SRC" -f commit_message="Release $(v)" && \
	gh release create "$(v)" --target "$$DST" --title "$(v)" --generate-notes && \
	echo "Release $(v) created on $$DST with changes from $$SRC."
