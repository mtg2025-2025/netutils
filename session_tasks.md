# Parallel Agent Session Tasks

Module 1.2, Exercise 1. Target Codebase: Netutils fork (github.com/mtg2025-2025/netutils).
"Main" for this exercise is the `agent-sandbox` branch. The fork has no branch named main, and `agent-sandbox`
is the working branch that holds the Module 1.1 sandbox (Dockerfile.agent, egress proxy, setup.md).

## Session A

Branch name: feature/lint-report
Worktree directory: ../netutils-lint-report
Task: Run the project's configured linters on the netutils/ package and write a short report of the most important findings, grouped by severity, with file and line for each.
Files or folders the agent may write to: agent/reports/lint-report.md (new file only)
Files or folders the agent may read but not write to: everything else, especially netutils/, tests/ and pyproject.toml
Commands the agent may run: ruff check netutils/, pylint netutils, mypy netutils (read-only checks; no --fix or auto-format)
Definition of done: lint-report.md exists, lists findings by tool and severity, names the top 5 issues worth fixing, and no other file is changed.

## Session B

Branch name: feature/vlan-tests
Worktree directory: ../netutils-vlan-tests
Task: Add edge-case unit tests for netutils/vlan.py (vlanlist_to_config and vlanconfig_to_list), such as invalid input and boundary VLAN IDs 1 and 4094.
Files or folders the agent may write to: tests/unit/test_vlan.py, and new files under tests/unit/mock/vlan/
Files or folders the agent may read but not write to: everything else, especially netutils/vlan.py (do not change the code under test)
Commands the agent may run: pytest tests/unit/test_vlan.py (with the sandbox's standard flags from setup.md)
Definition of done: new tests pass, existing vlan tests still pass, netutils/vlan.py is unchanged, and no file outside the write scope is changed.

## Both sessions

No git commands inside the container. Git doesn't work inside a worktree container, so the orchestrator reviews and commits from the Windows host.
