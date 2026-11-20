# Parallel Agent Session Tasks

Module 1.2, Exercise 1. Target Codebase: Netutils fork (github.com/mtg2025-2025/netutils).
The main branch for this exercise is `agent-sandbox`, the working branch for the course. It holds the Module 1.1
sandbox (Dockerfile.agent, egress proxy, setup.md). Both feature branches start from it and merge back into it.
The task definitions below (Session A, Session B, Both sessions) were committed in 4a67b4a, before the worktrees
were created and before any agent ran. The Results, verification and rationale sections were added after the run.

## Session A

Branch name: feature/lint-report
Worktree directory: ../netutils-lint-report
Task: Run the project's configured linters on the netutils/ package and write a short report of the most important findings, grouped by severity, with file and line for each.
Files or folders the agent may write to: agent/reports/lint-report.md (new file only)
Files or folders the agent may read but not write to: everything else, especially netutils/, tests/ and pyproject.toml
Commands the agent may run: ruff check netutils/, pylint netutils, mypy netutils (read-only checks; no --fix or auto-format)
Definition of done: lint-report.md exists, lists findings by tool and severity, names the top 5 issues worth fixing, and no other file is changed.

### Results

Merge decision: Merged

Reason: The report is accurate, it stayed inside its file scope, and its top finding is a real bug I verified in the code. It adds one new file and changes no project code, so merging it carries no risk to the library.

Correctness and usefulness: All three linters passed with zero findings (ruff "All checks passed", pylint 10.00/10, mypy "no issues found in 35 source files"). The report states that accurately, then reviews the project's inline suppressions and picks the five that hide real risk. I checked its top finding in netutils/acl.py:

    for item in self.rules:
        if item.match(self.class_obj(rule)):
            return str(item.action)
    return str(item.deny)  # pylint: disable=undefined-loop-variable

With an empty rule list, `item` is never set, so ACLRules.match raises UnboundLocalError instead of returning the default deny. The finding is real.

Scope check (contract vs. actual):

| Contract item | Allowed | Actual | Result |
|---|---|---|---|
| Write scope | agent/reports/lint-report.md (new file only) | `git status --short -uall` in the worktree: `?? agent/reports/lint-report.md` | In scope |
| Read-only files | everything else | No other file in `git status` | In scope |
| Commands | ruff check, pylint, mypy, with no --fix | The three linters, plus read-only shell tools (ls, cat, grep, sed -n) to inspect the layout, count suppressions and read code around them. Linter output and cache folders went to a scratch folder in the container's /tmp. Found in its transcript (39d3ee7d); unlike Session B, it didn't list these in its summary. | Outside the list (read-only, no repo file changed) |
| Definition of done | report exists; findings by tool and severity; top 5; no other file changed | All four met | Met |

Production-appropriateness: Ready as a report. It's a prioritized list of real issues, not a fix, so each of its top 5 items is a candidate task for a future agent session.

How a review finding drove the decision: The task asked for linter findings, and the linters found none, so the agent widened its review to suppressed warnings on its own. That could have been drift. I accepted it because it stayed read-only and inside its file scope, and its top finding was verifiably real. Without that check, I would have treated the extra material as out of scope.

Commits on this branch (`git log --oneline agent-sandbox..feature/lint-report`, captured before merging):
e9f1436 (HEAD -> feature/lint-report) Module 1.2, Exercise 1: Session A lint report for netutils/

## Session B

Branch name: feature/vlan-tests
Worktree directory: ../netutils-vlan-tests
Task: Add edge-case unit tests for netutils/vlan.py (vlanlist_to_config and vlanconfig_to_list), such as invalid input and boundary VLAN IDs 1 and 4094.
Files or folders the agent may write to: tests/unit/test_vlan.py, and new files under tests/unit/mock/vlan/
Files or folders the agent may read but not write to: everything else, especially netutils/vlan.py (do not change the code under test)
Commands the agent may run: pytest tests/unit/test_vlan.py (with the sandbox's standard flags from setup.md)
Definition of done: new tests pass, existing vlan tests still pass, netutils/vlan.py is unchanged, and no file outside the write scope is changed.

### Results

Merge decision: Merged, with follow-up

Reason: The tests are correct, in scope and pass the project's own checks, and they exposed four real bugs I reproduced independently. Merging test code doesn't change how the library behaves, so it was safe to accept now. The follow-up below is needed before I'd call it production-ready.

Correctness and usefulness: The 152 added lines cover the cases a network engineer would check: VLAN IDs 1 and 4094 alone and at range edges, invalid IDs 0, -1 and 4095, the full 1-4094 range, duplicates and unsorted input, the 48-character first-line limit, and malformed config lines. Each test asserts an exact expected output. An independent run in a separate container gave `57 passed, 6 xfailed`. I reproduced each bug the agent reported:

    vlanlist_to_config([1,2,3], min_grouping_size=4)            -> ['1,2']    (VLAN 3 silently dropped)
    vlanlist_to_config([4095], min_grouping_size=1)             -> ['4095']   (range check skipped)
    vlanconfig_to_list('switchport trunk allowed vlan 0,1')     -> [0, 1]     (VLAN 0 accepted)
    vlanconfig_to_list('')                                      -> IndexError (should be ValueError)

Scope check (contract vs. actual):

| Contract item | Allowed | Actual | Result |
|---|---|---|---|
| Write scope | tests/unit/test_vlan.py; new files under tests/unit/mock/vlan/ | `git diff --stat`: `tests/unit/test_vlan.py \| 152 +++`, 1 file changed. No mock files added. | In scope |
| Read-only files | everything else, especially netutils/vlan.py | vlan.py not in the diff (the agent also checked its md5sum before and after) | In scope |
| Commands | pytest on test_vlan.py | pytest, plus cat, ls, md5sum (read), sed and heredoc appends (to edit the allowed file), and one empty python command. The agent listed these itself. | Outside the list (no file outside scope changed) |
| Definition of done | new tests pass; existing tests pass; vlan.py unchanged; no other file changed | Existing tests pass, vlan.py unchanged, no other file changed. 6 of the new tests are strict xfail (expected failures), not passes. | Met, with a deviation (see below) |

Production-appropriateness: Passes the project's checks. `ruff check tests/unit/test_vlan.py` reports "All checks passed!", and `ruff format --check` with the project's config reports "already formatted". Not yet production-ready, because the xfail reasons say "Known bug: ..." but don't point to a tracked issue.

How a review finding drove the decision: The definition of done said "new tests pass", but 6 new tests are expected failures. I had to decide whether that broke the contract. The diff showed each one is marked `@pytest.mark.xfail(strict=True, reason="Known bug: ...")` and documents a bug I reproduced. That's the right way to record a bug without changing vlan.py, which was off-limits, so I kept them instead of discarding the branch. Because they're strict, a future fix to vlan.py will make its test pass unexpectedly and fail the run, which signals that the marker should come off. What's missing is traceability, which became the follow-up.

Follow-up: file the 4 bugs as GitHub issues and add each issue number to its xfail reason (like tracking a vendor bug ID).

Commits on this branch (`git log --oneline agent-sandbox..feature/vlan-tests`, captured before merging):
5b086f9 (HEAD -> feature/vlan-tests) Module 1.2, Exercise 1: Session B edge-case tests for netutils/vlan.py

## Both sessions

No git commands inside the container. Git doesn't work inside a worktree container, so the orchestrator reviews and commits from the Windows host.

## Why these two tasks are safe to run in parallel

- **Write scopes don't overlap.** Session A writes one new file under agent/reports/. Session B writes one test file and its mock-data folder. No file can be written by both sessions.
- **Shared files are kept out of both write scopes.** Each of these could affect the other session if changed:
  - netutils/ (all library code): Session A lints it, and Session B tests it. If either changed it, the other would be checking code that is moving underneath it.
  - pyproject.toml: it holds both the linter settings Session A relies on and the pytest settings Session B relies on. Changing it could silence a lint rule or change how the tests run.
  - tests/unit/conftest.py: shared test fixtures used by every test file. Only test_vlan.py itself is writable.
  - session_tasks.md, setup.md, Dockerfile.agent: the contract and the sandbox definition. Only I change these.
- **Session A is read-only for code.** Its only commands are check-mode linters with no --fix, so it can't reformat a file Session B is reading.
- **Each definition of done can be checked on its own.** Session A's is about one file's contents. Session B's is a pytest result on one file plus an unchanged vlan.py. Neither depends on the other session's output, so each branch can be judged and merged or discarded separately.

## Isolation rationale

- **Separate worktrees.** Each session works in its own folder on its own branch, so its changes can be reviewed, committed, merged or discarded without touching the other's. If both sessions shared one folder, their changes would land on the same branch as one mixed set of uncommitted edits. I couldn't keep one session's work and discard the other's. And if both edited the same file, the later write would silently replace the earlier one, with no merge conflict to warn me.
- **One container per worktree.** Each container mounts only its own worktree at /workspace, so an agent can't see or change the other session's folder, the main worktree or anything else on the computer.
- **Same sandbox as Module 1.1.** Both containers run on the internal network agent-net, with HTTPS_PROXY pointing at the egress-proxy allowlist (Anthropic's domains only). The shared claude-auth volume holds only the login, and the shared agent-history folder holds the session transcripts, outside the repository.

## Setup verification (actual output)

Worktrees, from the main repo folder:

    PS C:\Users\JEREMY\Projects\netutils> git worktree list
    C:/Users/JEREMY/Projects/netutils             4a67b4a [agent-sandbox]
    C:/Users/JEREMY/Projects/netutils-lint-report 4a67b4a [feature/lint-report]
    C:/Users/JEREMY/Projects/netutils-vlan-tests  4a67b4a [feature/vlan-tests]

Branch in each worktree:

    PS C:\Users\JEREMY\Projects\netutils-lint-report> git branch --show-current
    feature/lint-report
    PS C:\Users\JEREMY\Projects\netutils-vlan-tests> git branch --show-current
    feature/vlan-tests
    PS C:\Users\JEREMY\Projects\netutils-vlan-tests> git branch
    + agent-sandbox
      develop
    + feature/lint-report
    * feature/vlan-tests

Container launch (same command in each worktree; `${PWD}` makes each container mount its own folder):

    docker run -it --rm --network agent-net -e HTTPS_PROXY=http://egress-proxy:8888 -e HTTP_PROXY=http://egress-proxy:8888 -v claude-auth:/claude-auth -v "${PWD}:/workspace" -v "${PWD}/../agent-history:/root/.claude/projects" netutils-agent

`ls /workspace` inside each container (identical, because both branches start at 4a67b4a):

    ai-course:/workspace# ls /workspace
    Dockerfile        README.md            changes                 docs                mkdocs.yml   pyproject.toml    tasks.py
    Dockerfile.agent  agent                development             flat_postprocess    netutils     session_tasks.md  tests
    LICENSE           agent-smoke-test.md  development_scripts.py  invoke.example.yml  poetry.lock  setup.md

Which host folder each running container mounted, checked from the host with `docker inspect`:

    /nervous_merkle: /run/desktop/mnt/host/c/Users/JEREMY/Projects/netutils-vlan-tests
    /eloquent_shaw: /run/desktop/mnt/host/c/Users/JEREMY/Projects/netutils-lint-report

## Run and merge record

- Each session received one task prompt and needed no corrective prompt.
  - Session A: transcript 39d3ee7d, 5.0 min, 376k tokens in / 4.9k out.
  - Session B: transcript 154c65ab, 42.5 min until /exit, 290k tokens in / 6.7k out.
  - Session A finished before Session B got going, so the sessions overlapped by only about a minute.
- Merges into agent-sandbox, with no conflicts:
  - Session A: fast-forward (4a67b4a..e9f1436).
  - Session B: ort strategy merge, commit 0e6063a.
- Full unit suite on agent-sandbox after both merges: 880 passed, 4 failed (test_dns.py, expected: the sandbox blocks DNS), 2 skipped, 6 xfailed. Before the exercise: 836 passed, 4 failed, 2 skipped. So the 44 new passing tests and 6 xfails came from Session B, and nothing that passed before broke.
