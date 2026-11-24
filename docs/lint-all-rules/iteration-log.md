# Iteration Log: All-Rules Lint Summary Workflow

Module 1 Lab, Task 2. Scored with [rubric.md](rubric.md) (each run notes the rubric commit it was scored
against) against [prd.md](prd.md). Newest run first. Entries are never deleted.

## Runs

| Run ID | Date | Agent/tool | Prompt or command | Cycle time | Rubric scores (TF/10R/10F/Fix) | Pass/Fail | Review latency | Cost (tokens in/out) | Observations |
|--------|------|------------|-------------------|------------|--------------------------------|-----------|----------------|----------------------|--------------|
| 001 (baseline) | 2026-11-24 | Claude Code 2.1.327, claude-opus-5-5, ruff 0.16.8, sandbox container per worktree | Prompt v1 (see Run 001 details) | 18m15.645s (`time`, includes waiting before `/exit`); agent work ~45s (transcript) | 4 / 3 / 3 / 4 | Pass | 7m08.10s | $0.35 (443,443 in / 4,659 out) | Passed on the first run with exact numbers, and found a likely real bug (compliance.py:371) without editing. Review time includes looking up the rubric and evidence mid-review; next run: a prepared review sheet. Its agent work didn't overlap Task 1's (login delay), so this was not a true parallel run. |

Scores: TF = Total Findings, 10R = Top 10 Rules, 10F = Top 10 Files, Fix = Fixable Count.
1-4, or N/A (rubric 3.5). Pass = all gates + every scored dimension >= 3.

## Run details

<!-- One section per run, newest first: full prompt, how it was run (worktree, branch, container),
     raw evidence (ruff summary lines, time output, token counts), gates G1-G3, one-sentence note per
     score, measurements, observations, and what changed since the last run. -->

### Run 001 -- 2026-11-24 -- Baseline

**Task:** Run ruff with every rule enabled on `netutils/` and write a summary of the findings without changing any
code (see [prd.md](prd.md)).

**Full prompt (v1):** written from the PRD's actions, acceptance criteria and decision events. No backticks or
double quotes inside, because the prompt is passed in double quotes on the command line (backticks would run as
shell commands; inner double quotes would cut the prompt short).

```
Run these two commands exactly: ruff check netutils --select ALL --no-cache --statistics and ruff check netutils --select ALL --no-cache --output-format concise. Write a report to agent/reports/lint-all-rules.md. In the report, state the exact commands you ran; the total number of findings from ruff's 'Found N errors.' line; the top 10 rules by count, each with its code, name and count from the --statistics output; the top 10 files by number of findings, each with its count, counted from the concise output; and the fixable count from ruff's '[*] N fixable' line. If rules or files are tied for 10th place, include all of the tied entries. If ruff fails, try once more; if it fails again, put the error output in the report and stop. If a finding looks like a real bug, describe it in the report but do not edit any file. Never run ruff with --fix or --unsafe-fixes. Do not create or modify any other file, including a .ruff_cache folder, and do not commit, push, or install anything.
```

**How it was run:** Worktree `netutils-task2` (next to `netutils`), branch `lab/task2-lint-all-rules`, created from
`c454193` (after the PRD, rubric and this log were committed). Windows PowerShell from that folder, egress proxy up.
Container: the setup.md command plus `--name lab-task2`, mounting this worktree as `/workspace`. Then
`time claude "<prompt v1>"`, started at the same time as Task 1's Run 003 in a second container. Fresh session, no
interventions. Before the run: host `git status` clean, no `.ruff_cache`.
Isolation evidence (inside the container): `cat .git` -> `gitdir: <Windows path>/netutils/.git/worktrees/netutils-task2`;
`ls /workspace/..` shows no other worktree. From the host, `docker inspect lab-task1 lab-task2` showed each container
with only its own worktree at `/workspace`; both share the `claude-auth` login volume and the `agent-history` folder.
Transcript: session `b5e2e452-483e-46a7-8b37-defc228e9414` in `../agent-history`. Scored against rubric commit `5697d12`.

**Raw evidence (from the transcript, not the report):**
- Total line: `Found 1106 errors.`
- Fixable line: `[*] 393 fixable with the --fix option (179 hidden fixes can be enabled with the --unsafe-fixes option).`
- Top rules (`--statistics`, all 84 rule lines in the transcript): UP006 242, TRY003 95, E501 85, EM101 59, EM102 48,
  RUF012 48, UP045 38, ANN401 35, CPY001 35, EXE002 35; 11th PLW2901 33 (no tie for 10th)
- Top files (count of concise lines per file, 1,106 lines in all): config/parser.py 286, interface.py 115, acl.py 80,
  ip.py 74, password.py 57, bandwidth.py 51, _private/version.py 51, config/conversion.py 49, config/compliance.py 49,
  lib_mapper.py 47; 11th os_version.py 30 (no tie for 10th)
- Both commands exited 1 (ruff's normal code when it finds problems), with empty stderr; ruff's output was saved to
  the session scratchpad in the container's `/tmp`, not the worktree.
- Tool calls: 9 (list files, check for `.ruff_cache`, try `git status` (fails in a worktree container), ruff
  version; run both commands; total three ways plus per-file counts; read the rest of the statistics; list the
  bug-like findings; read the code at those lines (two calls); list `agent/reports`; write the report). The one
  "failed" call ended with `ls -d .ruff_cache`, which fails because the folder doesn't exist. It did not read the
  old `lint-report.md`.

**Gates:**

| Gate | Result | Evidence |
|------|--------|----------|
| G1 Command stated | Pass | Report lists both exact commands under "Commands run" |
| G2 No other files changed | Pass | Host `git status --short`: only `?? agent/reports/lint-all-rules.md`; `Test-Path .ruff_cache` -> False |
| G3 No commit, push, or install | Pass | Host `git log --oneline -1`: still `c454193`; none of the 9 tool calls is a commit, push or install, and no `--fix` |

**Rubric scores:**

| Dimension | Score | Note |
|-----------|-------|------|
| Total Findings | 4 | 1106, exact, and quotes `Found 1106 errors.` |
| Top 10 Rules | 3 | Right rules, order, codes, names and exact counts; the three-way tie at 35 handled and PLW2901 (33) shown as 11th. No meaning per rule or pyproject status, so not 4. |
| Top 10 Files | 3 | All 10 files and counts exact, os_version.py (30) shown as 11th. No most common rule per file, so not 4. |
| Fixable Count | 4 | 393, exact, and quotes ruff's whole line, keeping the 179 unsafe fixes separate. |

All gates pass and every dimension >= 3.

**Measurements:**
- Cycle time: 18m15.645s (`real` from `time`; user 0m10.507s, sys 0m3.160s). Not the agent's working time: the session
  waited while the reviewer dealt with Task 1's login before `/exit`. The transcript shows the agent worked ~45s
  (18:11:22 to 18:12:07 UTC).
- Review latency: 7m08.10s. Includes finding the rubric and asking for the evidence and the level 4 rules during review.
- Cost per run: $0.35 at claude-opus-5-5 API rates (API-equivalent; not billed this way on a subscription).
  Tokens: 20 input + 21,142 cache write (1h) + 422,281 cache read = 443,443 in; 4,659 out. Prices per million tokens:
  input $4, 1h cache write $8, cache read $0.20, output $20.
  = $0.0001 + $0.1691 + $0.0845 + $0.0932 = $0.3469.
- Permission prompts: none reported.

**Pass/Fail:** Pass

**Observations:** Passed on the first run with exact numbers, and found a likely real bug (compliance.py:371) without
editing. Review time includes looking up the rubric and evidence mid-review; next run: a prepared review sheet. Its
agent work didn't overlap Task 1's (login delay), so this was not a true parallel run. Details: the agent checked the
total three ways (ruff's line, the sum of the statistics, the concise line count) and checked that no cache was
created. The bug: in `_check_configs`, a bare `raise` sits outside any `except` block, so an `ordered` value other
than True/False gives `RuntimeError: No active exception to reraise` instead of a useful error; a
`# pylint: disable=misplaced-bare-raise` comment suggests it was noticed but not fixed. It also checked other
bug-like findings (B034, RUF021, ISC001) and explained why they are fine. Run 002 (same prompt) is to be run in
parallel with Task 1's Run 004 to get true overlap and a second data point.

**Changes made:** None. This is the baseline run.

## Final state after merge

<!-- Lab step 9: paste the output of `git log --oneline` on agent-sandbox after both branches are
     merged, and note which commits show the two branches being merged. -->
