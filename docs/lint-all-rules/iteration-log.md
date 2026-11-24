# Iteration Log: All-Rules Lint Summary Workflow

Module 1 Lab, Task 2. Scored with [rubric.md](rubric.md) (each run notes the rubric commit it was scored
against) against [prd.md](prd.md). Newest run first. Entries are never deleted.

## Runs

| Run ID | Date | Agent/tool | Prompt or command | Cycle time | Rubric scores (TF/10R/10F/Fix) | Pass/Fail | Review latency | Cost (tokens in/out) | Observations |
|--------|------|------------|-------------------|------------|--------------------------------|-----------|----------------|----------------------|--------------|
| 002 | 2026-11-24 | Claude Code 2.1.327, claude-opus-5-5, ruff 0.16.8, sandbox container per worktree | Prompt v1 content (pasted inside an open Claude session, see Run 002 details) | No `time` output; agent work ~26s (transcript) | 4 / 3 / 3 / 4 | Pass | 4m41.63s | $0.29 (332,398 in / 2,661 out) | Pass with the same scores, but the agent read Run 001's committed report, re-ran ruff, verified every number, then kept the old report and changed one line, claiming it was "regenerated" (`git diff --stat`: 1 insertion, 1 deletion). The rubric can't tell a reused report from a fresh one when the output doesn't change. Next run: delete the old report first. True parallel run; no `time` output (prompt pasted inside Claude). The review sheet cut review time to 4:41. |
| 001 (baseline) | 2026-11-24 | Claude Code 2.1.327, claude-opus-5-5, ruff 0.16.8, sandbox container per worktree | Prompt v1 (see Run 001 details) | 18m15.645s (`time`, includes waiting before `/exit`); agent work ~45s (transcript) | 4 / 3 / 3 / 4 | Pass | 7m08.10s | $0.35 (443,443 in / 4,659 out) | Passed on the first run with exact numbers, and found a likely real bug (compliance.py:371) without editing. Review time includes looking up the rubric and evidence mid-review; next run: a prepared review sheet. Its agent work didn't overlap Task 1's (login delay), so this was not a true parallel run. |

Scores: TF = Total Findings, 10R = Top 10 Rules, 10F = Top 10 Files, Fix = Fixable Count.
1-4, or N/A (rubric 3.5). Pass = all gates + every scored dimension >= 3.

## Run details

<!-- One section per run, newest first: full prompt, how it was run (worktree, branch, container),
     raw evidence (ruff summary lines, time output, token counts), gates G1-G3, one-sentence note per
     score, measurements, observations, and what changed since the last run. -->

### Run 002 -- 2026-11-24 -- Repeat of v1, true parallel run with Task 1 Run 004

**Task:** Same as Run 001.

**Changes made:** None to the prompt (v1 content). Purpose: a second data point for v1 and a run that truly overlaps
Task 1 (Run 001's agent work did not overlap Task 1 Run 003 because of a login delay). Setup changes, not part of
the task: a fresh container, a login check in each container before the run, and a prepared review sheet before the
review clock started. Run 001's report was committed (`2f43350`), so it was in the worktree for this run; it was
not removed.

**Full prompt (v1):** same content as Run 001, but see the deviation below.

**How it was run:** Fresh container, same command as Run 001 (`--name lab-task2`). Login checked first (`claude`,
confirmed, `/exit`). Before the run: host `git status` clean at `2f43350`, no `.ruff_cache`.
**Deviation:** after the login check the user started `claude` again and pasted the whole
`time claude "<prompt v1>"` line into that open session, so the agent's prompt was the v1 text wrapped in
`time claude "..."`, and the shell never ran `time`. The agent ignored the wrapper and did the task.
Overlap with Task 1 Run 004 (transcripts): Task 2 20:01:53-20:02:19 UTC, Task 1 20:01:56-20:02:33 UTC.
Transcript: session `00d17eaf-df55-4f28-938e-0d5fb36cacca` in `../agent-history`. Scored against rubric commit `5697d12`.

**Raw evidence (from the transcript, not the report):**
- Total line: `Found 1106 errors.`; fixable line: `[*] 393 fixable with the --fix option (179 hidden fixes can be
  enabled with the --unsafe-fixes option).` Both commands exited 1 with empty stderr.
- Top rules and top files: identical to Run 001 (UP006 242 ... EXE002 35, 11th PLW2901 33; config/parser.py 286 ...
  lib_mapper.py 47, 11th os_version.py 30), 1,106 concise lines.
- Tool calls: 6, no Write. (1) list files, check `.ruff_cache`, ruff version; (2) **`cat agent/reports/lint-all-rules.md`
  (Run 001's report)** and `git status` (fails in the container); (3) run both commands into the container's `/tmp`;
  (4) total and per-file counts, grep for the bug-like findings; (5) read the code at those lines; (6) a Python
  one-liner that **replaced one line of the old report**, adding: "This report was regenerated from a fresh run of
  both commands; every number below was re-checked against that run's output."
- Host `git diff --stat`: `agent/reports/lint-all-rules.md | 2 +-`, 1 insertion, 1 deletion.

**Gates:**

| Gate | Result | Evidence |
|------|--------|----------|
| G1 Commands stated | Pass | Both exact commands under "Commands run" (carried over from Run 001's text, and true for this run) |
| G2 No other files changed | Pass | Host `git status --short`: only ` M agent/reports/lint-all-rules.md`; `Test-Path .ruff_cache` -> False |
| G3 No commit, push, or install | Pass | Host `git log --oneline -1`: still `2f43350`; no commit, push, install or `--fix` in the 6 tool calls |

**Rubric scores:**

| Dimension | Score | Note |
|-----------|-------|------|
| Total Findings | 4 | 1106, matches this run's `Found 1106 errors.`, and the line is quoted. |
| Top 10 Rules | 3 | All 10 with codes, names and exact counts matching this run's statistics; no meaning or pyproject status. |
| Top 10 Files | 3 | All 10 with exact counts matching this run's concise output; no most common rule per file. |
| Fixable Count | 4 | 393 with ruff's whole line quoted. |

All gates pass and every dimension >= 3. Reviewer's decision: Pass, because every number was verified against this
run's own output, which is what the rubric measures; the reuse is recorded as an observation, not a score change.

**Measurements:**
- Cycle time: no `time` output (see deviation). The transcript shows the agent worked ~26s (20:01:53 to 20:02:19 UTC).
- Review latency: 4m41.63s, with a prepared review sheet (Run 001: 7m08.10s without one).
- Cost per run: $0.29 at claude-opus-5-5 API rates (API-equivalent; not billed this way on a subscription).
  Tokens: 14 input + 21,583 cache write (1h) + 310,801 cache read = 332,398 in; 2,661 out.
  = $0.0001 + $0.1727 + $0.0622 + $0.0532 = $0.2881 (rounded per line).
- Permission prompts: none reported.

**Pass/Fail:** Pass

**Comparison with Run 001 (same prompt content):**

| Metric | Run 001 | Run 002 | Change |
|--------|---------|---------|--------|
| Scores | 4/3/3/4 | 4/3/3/4 | none |
| Read the old report? | no (none there) | yes, and reused it | new risk |
| Report lines changed vs last commit | new file | 1 insertion, 1 deletion | reused |
| Agent work time | ~45s | ~26s | -42% |
| Tool calls | 9 | 6 | -3 |
| Tokens in / out | 443,443 / 4,659 | 332,398 / 2,661 | -25% / -43% |
| Cost | $0.35 | $0.29 | -17% |
| Review latency | 7m08.10s | 4m41.63s | -34% (review sheet) |

**Observations:** Pass with the same scores, but the agent read Run 001's committed report, re-ran ruff, verified
every number, then kept the old report and changed one line, claiming it was "regenerated" (`git diff --stat`:
1 insertion, 1 deletion). The rubric can't tell a reused report from a fresh one when the output doesn't change.
Next run: delete the old report first. True parallel run; no `time` output (prompt pasted inside Claude). The review
sheet cut review time to 4:41. Fixes considered: delete the old report before each run (setup; strongest, the agent
can't read what isn't there), rename old or new reports (fair; old files stay visible and the PRD path changes), or
tell the agent in the prompt to ignore previous reports (weaker alone: an instruction, not enforcement, and a prompt
change to test on its own). Preferred: delete first, optionally plus the prompt line (defense in depth). Task 1 Run
004 tested deletion: the agent wrote a fresh report with no loss in score. The cost and time drops likely come from
reusing the old text, so they are not a fair efficiency gain.

**Changes made:** None to the prompt. For the next run: delete the old report before the run.

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

Both branches were reviewed (`git diff --stat agent-sandbox <branch>`: each changed only its own report and its own
log, no shared files) and merged into `agent-sandbox` (this repo's "main") on 2026-11-24 with `git merge --no-ff`, so
each merge has its own commit. Both merges were clean, with no conflicts.

Output of `git log --oneline` on `agent-sandbox` right after the merges. The full log is 462 lines because it includes
all of Netutils' earlier history; the first 12 lines below cover this lab and the end of Module 1.3.

```
9c8df79 (HEAD -> agent-sandbox) Merge Task 2 (all-rules lint summary, Runs 001-002) into agent-sandbox (Module 1 Lab)
3d9fba5 Merge Task 1 (unit test summary, Runs 003-004) into agent-sandbox (Module 1 Lab)
98de379 (lab/task2-lint-all-rules) docs: log Run 002, repeat of v1 in true parallel run (Module 1 Lab, Task 2)
00e6f28 (lab/task1-unit-tests) docs: log Run 004, old report removed, true parallel run (Module 1 Lab, Task 1)
2f43350 docs: log Run 001 baseline for all-rules lint (Module 1 Lab, Task 2)
0c4198a docs: log Run 003, repeat of prompt v2 in parallel worktree (Module 1 Lab, Task 1)
c454193 docs: add iteration log for all-rules lint (Module 1 Lab, Task 2)
5697d12 docs: add rubric, scoring guide, and pass threshold for all-rules lint (Module 1 Lab, Task 2)
a67249f docs: add PRD for all-rules lint summary workflow (Module 1 Lab, Task 2)
7f83cb9 (origin/agent-sandbox) checkup: log entry, ADR 0003, remove personal paths, scan docs files (Module 1.3, Exercise 1)
554e081 docs: add task justification and edge cases to PRD; fix log header (Module 1.3, Exercise 1)
6e9a13d log: run 002 exact test command -- cycle time 1m14s, cost $0.29, rubric 16/16 (Module 1.3, Exercise 1)
```

The same history as a graph (`git log --oneline --graph -12`), showing the two branches leaving `c454193` and
joining back at the merge commits:

```
*   9c8df79 (HEAD -> agent-sandbox) Merge Task 2 (all-rules lint summary, Runs 001-002) into agent-sandbox (Module 1 Lab)
|\
| * 98de379 (lab/task2-lint-all-rules) docs: log Run 002, repeat of v1 in true parallel run (Module 1 Lab, Task 2)
| * 2f43350 docs: log Run 001 baseline for all-rules lint (Module 1 Lab, Task 2)
* |   3d9fba5 Merge Task 1 (unit test summary, Runs 003-004) into agent-sandbox (Module 1 Lab)
|\ \
| |/
|/|
| * 00e6f28 (lab/task1-unit-tests) docs: log Run 004, old report removed, true parallel run (Module 1 Lab, Task 1)
| * 0c4198a docs: log Run 003, repeat of prompt v2 in parallel worktree (Module 1 Lab, Task 1)
|/
* c454193 docs: add iteration log for all-rules lint (Module 1 Lab, Task 2)
* 5697d12 docs: add rubric, scoring guide, and pass threshold for all-rules lint (Module 1 Lab, Task 2)
* a67249f docs: add PRD for all-rules lint summary workflow (Module 1 Lab, Task 2)
* 7f83cb9 (origin/agent-sandbox) checkup: log entry, ADR 0003, remove personal paths, scan docs files (Module 1.3, Exercise 1)
* 554e081 docs: add task justification and edge cases to PRD; fix log header (Module 1.3, Exercise 1)
* 6e9a13d log: run 002 exact test command -- cycle time 1m14s, cost $0.29, rubric 16/16 (Module 1.3, Exercise 1)
```

How to read it:
- `a67249f`, `5697d12`, `c454193`: Task 2's PRD, rubric and log, committed on `agent-sandbox` before any run, so
  the bar was set first. Both branches start from `c454193`.
- `0c4198a`, `00e6f28`: Task 1's Runs 003 and 004 on `lab/task1-unit-tests`.
- `2f43350`, `98de379`: Task 2's Runs 001 and 002 on `lab/task2-lint-all-rules`.
- `3d9fba5` merges Task 1 and `9c8df79` merges Task 2. These two merge commits show the parallel branches being
  merged back.
- This section itself is committed after the merges, so its own commit is not in the output above.
