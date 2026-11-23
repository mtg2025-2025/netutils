# Iteration Log

This is a running record of what was tried, what happened, and what changed as a result. Each entry links a change to the evidence that caused it. Newest entries go at the bottom.

Format: **Date. What was tried.** What happened (evidence). What changed.

Naming: the course is split into sections (Module 1.1, 1.2, 2.1 and so on), and exercise numbers restart in each section. Work is always labeled with the full name, for example "Module 1.1, Exercise 2". Commit `5023f60` says "Module 1, Exercise 2". That means Module 1.1, and the message was left as is because the commit was already pushed.

---

## 2026-11-18: Module 1.1, Exercise 1. Choosing the Target Codebase

- **Tried:** two candidates, `networktocode/netutils` and `alxgb/sip-parser`.
- **Evidence:** Netutils' last release was v1.19.2 (2026-09-23), with 32 open issues and 840 unit tests plus 117 doctests passing. sip-parser's last commit was in 2019, it had 21 commits in total, and its README says the tests are incomplete.
- **Decision:** forked Netutils to `mtg2025-2025/netutils`. The planned improvements are issues #765 (LibreNMS mappings), #27 (IP randomization helper) and #859 (consecutive Cisco banners).
- **Note:** the tests can't run natively on Windows, because `netutils/password.py` imports `crypt`, which only exists on Linux. They have to run in a Linux container.

## 2026-11-18: Module 1.1, Exercise 2. First container build

- **Tried:** copied the course's `module_1/Dockerfile` as `Dockerfile.agent`. It was renamed so it doesn't overwrite the project's own `Dockerfile`, which CI uses. Replaced the course's general Python packages with `poetry install --with dev --all-extras`, and removed OpenCode and ngrok.
- **Evidence:** the first build ran, but in the container pytest had 64 collection errors: `PackageNotFoundError: No package metadata was found for netutils`. Netutils reads its own installed version at import time, so the dependencies alone weren't enough.
- **Changed:** the build now installs the Netutils package itself, using a placeholder for the code that's replaced by the real code mounted at `/workspace`. After the rebuild: 840 passed, 2 skipped, and 117 doctests passed.

## 2026-11-18: Windows line endings break container scripts

- **Tried:** ran the container with the course's helper scripts (`docker-entrypoint.sh`, `statusline.sh`) copied from a Windows checkout.
- **Evidence:** Git for Windows (`core.autocrlf=true`) had saved the scripts with CRLF line endings, and a Linux shell can't run a script with CRLF endings.
- **Changed:** `Dockerfile.agent` strips `\r` from both scripts at build time (`sed -i 's/\r$//'`). Added `.gitattributes` so `.sh` files are always stored with LF.

## 2026-11-18: Smoke test 1 (default network)

- **Tried:** Claude Code inside the container was asked to run the unit tests and write a summary to `/workspace/agent-smoke-test.md`, without modifying, committing, pushing or installing anything.
- **Evidence:** 840 passed, 2 skipped. The agent stayed within its instructions, and `git status` on Windows showed only new files. But Git inside the container reported about 610 modified files, each with equal lines added and removed.
- **Changed:** the cause was line endings again: Windows checkout, Linux Git. Added `git config --global core.autocrlf true` to `Dockerfile.agent`. After the rebuild, Git in the container went from 613 changed entries to only the 3 real new files. This had to be fixed before any agent makes commits, or a single commit could rewrite all 610 files.

## 2026-11-18: Self-review against the exercise rubric, then network egress

- **Tried:** checked the submission against the Module 1.1, Exercise 2 rubric before submitting.
- **Evidence:** the rubric's Proficient level requires "a network egress check… the curl output confirms that outbound requests fail". Docker's default network allowed all outbound traffic, which the rubric lists as Developing ("network egress is unconstrained").
- **Changed:** added an allowlist egress proxy (`agent/proxy/`) and an internal Docker network (`agent-net`). See [ADR 0001](adr/0001-agent-network-egress.md).
- **Result:** `curl https://example.com` failed with 403, and bypassing the proxy failed with "Could not resolve host". `api.anthropic.com` was reachable, and Claude Code worked normally.

## 2026-11-18: Smoke test 2 (restricted network)

- **Tried:** the same smoke-test prompt, on the restricted network.
- **Evidence:** 836 passed, 4 failed, 2 skipped. All 4 failures are in `tests/unit/test_dns.py`, which looks up google.com and yahoo.com. Git inside the container showed no false modifications, which confirms the line-ending fix.
- **Interpretation:** the 4 DNS failures are expected inside the sandbox and show the network boundary holding. Reviewers and agents must treat them as known failures, without letting them hide a real failure in the same file.
- **Proxy log** (`logs/2026-11-18-egress-proxy.log`): during the sessions, Claude Code also tried to reach `github.com`, `api.github.com`, `raw.githubusercontent.com`, `registry.npmjs.org`, `downloads.claude.ai` (its update check), `mcp-proxy.anthropic.com` and a Datadog telemetry endpoint. **The proxy refused all of them**, and the agent kept working. Only `api.anthropic.com` was allowed (43 connections).

## 2026-11-18: Persist session history for metrics

- **Tried:** after smoke test 2, tried to recover token and cost numbers for the two agent sessions.
- **Evidence:** they were gone. Claude Code keeps session transcripts in `/root/.claude/projects` inside the container, and `--rm` deletes them on exit. Only the login (in the `claude-auth` volume) survived.
- **Changed:** the run command now also mounts `../agent-history`, a host folder next to the repository, at `/root/.claude/projects`. Added `agent/tools/session_report.py`, which prints duration, prompts, API calls and tokens for each session. Tested with a one-prompt session, which recorded 1 prompt, 1 API call, 21,029 input tokens and 4 output tokens.
- **Trade-off:** this deliberately widens what persists. The agent can write to one more host folder, and transcripts contain everything the agent read. The folder is kept outside the repository so transcripts are never committed.

## 2026-11-18: End-of-exercise checkup

- **Tried:** reviewed the problems that came up during Module 1.1, Exercise 2: Notepad escaping Markdown, Notepad saving `Dockerfile` as `Dockerfile.txt` (and once emptying it), Windows line endings in shell scripts, and a personal Windows path in `setup.md`. Each was caught by hand, some only after the files had been submitted.
- **Changed:** added `agent/tools/checkup.py`, a deterministic checkup to run at the end of every exercise. It checks for required and empty files, `.txt` misnames, Markdown damage, BOM and encoding problems, LF line endings for scripts, secrets and personal paths, transcripts kept out of the repo, whether everything is committed and pushed, and whether the iteration log is current. With `--docker` it also rebuilds both images, confirms egress is blocked and the API is reachable, and reruns the tests.
- **Evidence it works:** on the current repo, 16 checks ran with 0 failures. With planted damage (escaped Markdown, an empty `Dockerfile.txt`, a fake `sk-ant-` key, a Windows user path and a BOM in a `.sh` file), it reported 4 failures covering all of them and exited with code 1.
- **Capstone note:** this is a candidate for a CI guardrail (a GitHub Action that runs the checkup on every pull request).

## 2026-11-19: Grader feedback on Module 1.1, Exercise 2 (7/8), applied to setup.md

- **Feedback:** Sandboxed Environment scored 3/4 and Governance, Security and CI/CD scored 4/4. The submission passed and doesn't need resubmitting. The grader raised four points:
  1. `nano` and `procps` were described as "inherited from the course image" instead of being tied to a task.
  2. The smoke test relied on the agent's own reply, without the exact pytest command or host-side output.
  3. "The login can never be committed" was too absolute, given that the agent can read the credential.
  4. The egress checks were described as if they proved every other destination is unreachable.
- **Investigated (point 1):** `python:3.12-slim` has no `ps`, `vi`, `vim` or `nano` (`command -v` in the base image). The Claude Code program in the agent image (version 2.1.327) runs `ps -o ppid=`, `ps -o command=` and `ps -o lstart=` to track and clean up the processes it starts. When `EDITOR` isn't set, it looks for `code`, then `vi`, then `nano` as its text editor. **Decision:** keep both. They have identified needs. Removing them was the alternative, and it was rejected: Claude Code's process handling would be missing `ps`, and its editor features would have no editor.
- **Changed in `setup.md`:**
  - a table giving each Linux tool's reason (point 1)
  - the exact pytest command from `agent-smoke-test.md`, plus host-side evidence: `Get-Item agent-smoke-test.md` and `git show --stat 5023f60`, which shows only new files and no deletions (point 2)
  - qualified wording for the login, the mount boundary, ephemerality and the image (point 3)
  - egress results scoped to the cases tested, with the design (an internal network and a default-deny proxy) as the reason the rest should be blocked (point 4)
- **Process change:** after every agent run, paste the host-side `git status` and file listing as is, at the time. The Module 1.1, Exercise 2 `git status` output wasn't saved, so the commit record had to stand in for it. The grader's four points are now a checklist for every write-up before it's submitted.

## 2026-11-19: Module 1.2 lesson practice (course repo, not graded)

- **Tried:** the lesson's two-worktree, two-container workflow on the course's sandbox example repo (LaunchCodeAgenticEngineer), before running it on Netutils.
- **Evidence:** Git inside a worktree container failed: `fatal: not a git repository: /workspace/C:/Users/JEREMY/Projects/LaunchCodeAgenticEngineer/.git/worktrees/repo-agent-b`. A worktree's `.git` is a one-line file pointing at the main repo by its Windows path, and that path doesn't exist inside the Linux container. Review also caught a docstring example with the wrong output (7 mask characters where the real output had 6) and a README file tree missing a file. `git diff main` doesn't show untracked files.
- **Changed for the exercise:** agents get no Git commands, and all commits and merges happen on the Windows host. New files are made visible to `git diff` with `git add -N`. Merges use `--no-edit` so Git doesn't open an editor. Agent claims are checked against real output, not trusted.

## 2026-11-20: Module 1.2, Exercise 1. Two parallel agent sessions on Netutils

- **Scope contract:** `session_tasks.md`, committed in 4a67b4a before the worktrees were created.
  - Session A (`feature/lint-report`, worktree `../netutils-lint-report`): run ruff, pylint and mypy on `netutils/` and write `agent/reports/lint-report.md`.
  - Session B (`feature/vlan-tests`, worktree `../netutils-vlan-tests`): add edge-case tests for `netutils/vlan.py` in `tests/unit/test_vlan.py`.
  - Chosen from 5 audited candidates. The others were tests for `lib_helpers.py`, a docstring example for `running_config.py`, and a developer note on `lib_mapper.py`. These two were picked because they have fully separate write scopes, one changes no code at all, and the user can judge VLAN behaviour from network experience.
- **Decision: the sandbox `docker run` for both containers, not the exercise's basic command.** The exercise's command has no `--network` or proxy settings, so it would have dropped the Module 1.1 egress boundary. Both containers ran on `agent-net` with `HTTPS_PROXY=http://egress-proxy:8888`, each mounting only its own worktree. `docker inspect` confirmed the mounts: `eloquent_shaw` used `netutils-lint-report`, and `nervous_merkle` used `netutils-vlan-tests`. See ADR 0002.
- **Decision: no Git inside the agent containers.** The alternatives were relative worktree paths (`git worktree add --relative-paths`) plus mounting the main `.git` into each container, which was rejected. It would give the agent write access to the shared `.git` database that every worktree uses, which breaks the isolation the exercise is about. See ADR 0002.
- **Runs:** each session got one task prompt, with no corrective prompts.

  | Session | Transcript | Start (UTC) | Minutes | Prompts | API calls | Tokens in | Tokens out | `$:` cost |
  |---|---|---|---|---|---|---|---|---|
  | A | 39d3ee7d | 17:21 | 5.0 | 1 | 8 | 376,158 | 4,945 | not noted |
  | B | 154c65ab | 17:25 | 42.5 (until /exit) | 1 (the report shows 4: /exit adds 3 lines) | 7 | 289,988 | 6,727 | $0.36 (status line before /exit) |

  Session A finished before Session B got going, so the runs overlapped by only about 1 minute. `session_report.py` counts `/exit` and its caveat lines as prompts. Session B's transcript has one real prompt.
- **Host-side evidence, before committing:**
  - `git status --short -uall` in `netutils-lint-report`: `?? agent/reports/lint-report.md`.
  - `git status --short` and `git diff --stat` in `netutils-vlan-tests`: ` M tests/unit/test_vlan.py`, `tests/unit/test_vlan.py | 152 ++++`, 1 file changed, 152 insertions(+).
  - `agent-sandbox` itself had no changes.
- **Review findings:**
  - Session A: the linters reported zero findings (ruff "All checks passed", pylint 10.00/10, mypy "no issues found in 35 source files"). The agent then reviewed about 90 inline suppressions. Its top finding was verified in the code: `netutils/acl.py:521` raises `UnboundLocalError` when `ACLRules.match` has no rules.
  - Session B: an independent run in a separate `python:3.12-slim` container gave `57 passed, 6 xfailed`. All 4 bugs the agent reported were reproduced. The worst: `vlanlist_to_config([1,2,3], min_grouping_size=4)` gives `['1,2']`. `ruff check` passes, and `ruff format --check` with the project config passes. A first format check outside the repo gave a false alarm, because it used ruff's default line length instead of the project's 120.
  - Both agents ran shell tools outside the allowed command list. Session A ran ls, cat, grep and sed -n, which is only visible in its transcript. Session B ran cat, ls, md5sum and sed, and listed them itself. No file outside either write scope changed.
- **Merges into `agent-sandbox`:** Session A was a fast-forward (`4a67b4a..e9f1436`). Session B was an ort merge, commit `0e6063a`. There were no conflicts.
- **After the merge:** the full unit suite gave `880 passed, 4 failed, 2 skipped, 6 xfailed`. The 4 failures are the DNS tests, which are expected in the sandbox. Before: 836 passed, 4 failed, 2 skipped.
- **Results recorded** in `session_tasks.md` (0a7b268, f4b2475). Pushed `c9d8fa2..f4b2475`. Submitted 2026-11-20. Answers saved in the course notes.
- **Lessons:**
  - The command limits were only requested in the prompt, so both agents used tools outside the list. Enforce them with Claude Code permission rules in the container instead.
  - Write the empty-result case into the task, for example what to do if the linters find nothing.
  - Say how to handle bugs found while writing tests.
  - Start both sessions back to back so they really run in parallel.
  - Capture `git log --oneline main..branch` before merging, because after the merge it prints nothing.

## 2026-11-23: Module 1.3, Exercise 1. PRD, rubric and baseline for a single-agent workflow

- **Tried:** a quality system for one agent task: run the Netutils unit tests in the sandbox and write `agent/reports/test-summary.md` explaining every failure. Files: `docs/prd.md` (375db02), `docs/rubric.md` (8038fc9, 3f400ee), `docs/iteration-log.md` (f5d1f64). Two scored runs: Run 001 baseline (539d7ac) and Run 002 with one prompt change (6e9a13d). The per-run detail (prompts, raw evidence, gates, scores, measurements) is in `docs/iteration-log.md`; this entry records the decisions.
- **Decision: the task.** Chosen over linting (ruff, pylint and mypy were all clean in Module 1.2, Exercise 1, so there would be little to score), coverage estimation (judgment calls, hard to make falsifiable) and a build check (pass/fail only). The unit test run has a known, repeatable result in the sandbox (4 test_dns failures from blocked DNS). Recorded in the PRD's "Why this task" section (554e081).
- **Decision: files in `docs/`, as the exercise requires,** even though `docs/` is also Netutils' documentation site. Checked: `mkdocs build --no-directory-urls --strict` (the project's own docs check in `tasks.py`) still succeeds with the three new files, run in the agent image with `--network none`.
- **Decision: gates plus a dimension floor.** 3 binary gates (command stated, no other files changed, no commit/push/install) and 4 dimensions scored 1-4 (Count Accuracy, Failure Coverage, Cause Accuracy, Failure Classification). Pass = all gates and every dimension 3 or higher, set before Run 001. Rejected: an aggregate of 12/16 (a run with wrong counts could pass), Count Accuracy as a gate, and a "report clarity" dimension. See ADR 0003.
- **Decision: score against evidence the agent didn't write.** The transcript's raw pytest output (primary), a reviewer rerun (cross-check), and host `git status`/`git log` (gates). Added as rubric 3.6 (3f400ee) after asking how a reviewer knows the report is accurate. See ADR 0003.
- **Rubric fixes before any run:** an N/A rule for runs with no failures (3.5), and a level-4 example that was unreachable in the sandbox was rewritten. The principle used: the bar may change to fix a flaw, never to make the agent pass.
- **Evidence:**

  | Run | Prompt | Score | Cycle time (`time`) | Agent work | Review | Tool calls | Tokens in / out | Cost |
  |---|---|---|---|---|---|---|---|---|
  | 001 (e5f0edac) | v1 | 16/16 pass | 3m21.962s | ~1m22s | ~2m01s (approx.) | 19 | 506,069 / 4,357 | $0.36 |
  | 002 (3364d95b) | v2 = v1 + exact pytest command | 16/16 pass | 1m14.369s | ~1m00s | 2m36.78s | 5 | 276,243 / 3,146 | $0.29 |

  Both runs: `4 failed, 880 passed, 2 skipped, 6 xfailed` (6.64s and 5.03s), host `git status` showed only the report changed, HEAD unchanged. Cost is API-equivalent at claude-opus-5-5 rates, computed from transcript token counts.
- **Changed:** prompt v2 gives the exact test command. Hypothesis confirmed for this pair: exploration dropped (19 to 5 tool calls, 45% fewer input tokens) with no loss in score. Cost fell less (19%) because about $0.18 per run is the cache write for Claude Code's startup context.
- **Measurement problems, recorded rather than discarded:** Run 001's cycle time includes a late `/exit` (terminal window off-screen), so agent work time is the fairer comparison; Run 001's review timer was restarted once.
- **Found:** in Run 002 the agent read Run 001's leftover report before running the tests. It still reran pytest, but a leftover report could let a run copy results.
- **After the runs (554e081):** the PRD got a "Why this task" section and an "Edge cases" section (skips/xfails, errors, no failures, overwriting the report, no environment changes, read-only checks allowed). No acceptance criterion or the threshold changed. Personal Windows paths were replaced with relative ones, and `agent/tools/checkup.py` now scans the three `docs/` files (it previously missed them).
- **Lessons:**
  - A perfect baseline leaves the rubric no room to show improvement; the iteration then has to be judged on efficiency.
  - Make the terminal fit the screen before timing a run.
  - Move the previous report out of the working tree before a run.
  - One run per prompt version can't show the normal run-to-run spread.

## Open items

- Run prompt v2 of the unit test summary workflow 3 or more times to measure normal variation in tokens and time before treating Run 002 as the new baseline, and move the old report out of the working tree before each run (Module 1.3, Exercise 1 follow-up; likely part of the Module 1 lab).
- File the 4 `netutils/vlan.py` bugs as GitHub issues and add each issue number to its xfail reason in `tests/unit/test_vlan.py` (Module 1.2, Exercise 1 follow-up).
- The top 5 items in `agent/reports/lint-report.md` are candidate tasks for future agent sessions. The first is the `acl.py:521` empty-rules crash.
- Turn each session's allowed command list into Claude Code permission rules (allow and deny) in the agent container, instead of relying on the prompt.
- `session_report.py` counts `/exit` and its caveat lines as prompts. Count only real user prompts.
- Run `python agent/tools/session_report.py` after every agent session and record the numbers here. They make up the baseline that the capstone compares against. Note the `$:` cost from the Claude Code status line before exiting, because the transcript records tokens but not cost.
- Decide whether `downloads.claude.ai` should be allowed. Blocking it stops Claude Code from updating itself inside the container, which is arguably what we want, since the image should only change when it's rebuilt.
- Two tests are skipped because `napalm` can't import `pkg_resources`. This is an environment gap to look into later.
