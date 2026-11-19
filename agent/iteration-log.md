# Iteration Log

This is a running record of what was tried, what happened, and what changed as a result. Each entry links a change to the evidence that caused it. Newest entries go at the bottom.

Format: **Date. What was tried.** What happened (evidence). What changed.

---

## 2026-11-18: Module 1, Exercise 1. Choosing the Target Codebase

- **Tried:** two candidates, `networktocode/netutils` and `alxgb/sip-parser`.
- **Evidence:** Netutils' last release was v1.19.2 (2026-09-23), with 32 open issues and 840 unit tests plus 117 doctests passing. sip-parser's last commit was in 2019, it had 21 commits in total, and its README says the tests are incomplete.
- **Decision:** forked Netutils to `mtg2025-2025/netutils`. The planned improvements are issues #765 (LibreNMS mappings), #27 (IP randomization helper) and #859 (consecutive Cisco banners).
- **Note:** the tests can't run natively on Windows, because `netutils/password.py` imports `crypt`, which only exists on Linux. They have to run in a Linux container.

## 2026-11-18: Module 1, Exercise 2. First container build

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

- **Tried:** checked the submission against the Exercise 2 rubric before submitting.
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

## Open items

- Run `python agent/tools/session_report.py` after every agent session and record the numbers here. They make up the baseline that the capstone compares against. Note the `$:` cost from the Claude Code status line before exiting, because the transcript records tokens but not cost.
- Decide whether `downloads.claude.ai` should be allowed. Blocking it stops Claude Code from updating itself inside the container, which is arguably what we want, since the image should only change when it's rebuilt.
- Two tests are skipped because `napalm` can't import `pkg_resources`. This is an environment gap to look into later.
