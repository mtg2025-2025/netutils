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

## Open items

- Run `python agent/tools/session_report.py` after every agent session and record the numbers here. They make up the baseline that the capstone compares against. Note the `$:` cost from the Claude Code status line before exiting, because the transcript records tokens but not cost.
- Decide whether `downloads.claude.ai` should be allowed. Blocking it stops Claude Code from updating itself inside the container, which is arguably what we want, since the image should only change when it's rebuilt.
- Two tests are skipped because `napalm` can't import `pkg_resources`. This is an environment gap to look into later.
