# Iteration Log: Unit Test Summary Workflow

Module 1.3, Exercise 1. Scored with [rubric.md](rubric.md) (commit 8038fc9) against [prd.md](prd.md).
Newest run first. Entries are never deleted.

## Runs

| Run ID | Date | Agent/tool | Prompt or command | Cycle time | Rubric scores (CA/FC/Cause/Class) | Pass/Fail | Review latency | Cost (tokens in/out) | Observations |
|--------|------|------------|-------------------|------------|-----------------------------------|-----------|----------------|----------------------|--------------|
| 002 | 2026-11-23 | Claude Code 2.1.327, claude-opus-5-5, sandbox container (setup.md command) | Prompt v2 = v1 + exact pytest command (see Run 002 details) | 1m14.369s (`time`); agent work ~1m00s (transcript) | 4 / 4 / 4 / 4 = 16/16 | Pass | 2m36.78s | $0.29 (276,243 in / 3,146 out) | Same score with 45% fewer input tokens and 5 tool calls instead of 19. The agent read Run 001's leftover report before running the tests. |
| 001 (baseline) | 2026-11-23 | Claude Code 2.1.327, claude-opus-5-5, sandbox container (setup.md command) | Prompt v1 (see Run 001 details) | 3m21.962s (`time`); agent work ~1m22s (transcript) | 4 / 4 / 4 / 4 = 16/16 | Pass | ~2m01s (approximate) | $0.36 (506,069 in / 4,357 out) | Perfect score: the rubric may leave no room to show improvement. Cost is high for one test run because the agent explored first. |

Scores: CA = Count Accuracy, FC = Failure Coverage, Cause = Cause Accuracy,
Class = Failure Classification. 1-4, or N/A (rubric 3.5). Pass = all gates + every scored dimension >= 3.

## Run details

<!-- One section per run, newest first: full prompt, gates G1-G3, one-sentence note per score,
     raw evidence (pytest summary line, time output, token counts), and what changed since the last run. -->

### Run 002 -- 2026-11-23 -- One change: exact test command in the prompt

**Task:** Same as Run 001.

**Changes made:** One change to the prompt: it now gives the exact test command. The rest of the prompt is word for
word the same as v1. Reason: in Run 001 the agent explored first (read `pyproject.toml` and an old lint report) to work
out the command. Hypothesis: giving the command cuts that exploration, lowering tokens and time with no loss in score.
Not a change to the task: the terminal window was resized to fit the screen so `/exit` could be typed straight away
(Run 001's cycle time included a late `/exit`).

**Full prompt (v2):**

```
Run this project's unit tests with exactly this command: PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider, and write a report to agent/reports/test-summary.md. In the report, state the exact command you ran, the counts from pytest's final summary line, every failed or errored test by its full test ID, the cause of each failure from its traceback, and whether each failure is an environment issue or a possible code defect. Do not modify any other files, and do not commit, push, or install anything.
```

**How it was run:** Same as Run 001: Windows PowerShell from `C:\Users\JEREMY\Projects\netutils`, egress proxy up
(`docker ps`), working tree clean at `539d7ac`, fresh container from the setup.md command, then `time claude "<prompt v2>"`.
Fresh session, no interventions. Transcript: session `3364d95b-8f1a-424f-aa85-dfdf6d834e0c` in `../agent-history`.
Report: `agent/reports/test-summary.md` (overwrites Run 001's copy; committed with this entry). Scored against rubric
commit `3f400ee`.

**Raw evidence (from the transcript, not the report):**
- pytest summary line: `4 failed, 880 passed, 2 skipped, 6 xfailed in 5.03s`, exit code 1 (Run 001 took 6.64s, so
  this is a fresh run, not numbers copied from the old report)
- Failed: `tests/unit/test_dns.py::test_is_fqdn_resolvable[data0]`, `[data1]`, `tests/unit/test_dns.py::test_fqdn_to_ip[data0]`, `[data1]`
- Errors in the tracebacks: `AssertionError: assert False == True` (test_is_fqdn_resolvable) and
  `socket.gaierror: [Errno -3] Temporary failure in name resolution` (test_fqdn_to_ip)
- Tool calls: 5 (run pytest; read the old report, `netutils/dns.py` and `git status`; a separate DNS lookup plus
  versions; write the report; `git status`), compared with 19 in Run 001

**Gates:**

| Gate | Result | Evidence |
|------|--------|----------|
| G1 Command stated | Pass | Report states `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider` |
| G2 No other files changed | Pass | Host `git status -s` after the run: only ` M agent/reports/test-summary.md` |
| G3 No commit, push, or install | Pass | HEAD still `539d7ac`; none of the 5 tool calls is an install, commit or push |

**Rubric scores:**

| Dimension | Score | Note |
|-----------|-------|------|
| Count Accuracy | 4 | Every count matches the raw summary line, and the report quotes that line and the exit code. |
| Failure Coverage | 4 | The same 4 full test IDs as the raw output, none missing or invented, and data0/data1 mapped to google.com/yahoo.com. |
| Cause Accuracy | 4 | Each failure has its actual error (assertion vs `socket.gaierror`) with file and line. |
| Failure Classification | 4 | All 4 labeled environment, backed by a separate lookup that failed the same way and the passing negative tests; says they should pass with working DNS. |
| **Total** | **16/16** | Pass threshold: all gates pass and every dimension >= 3 |

**Measurements:**
- Cycle time: 1m14.369s (`real` from `time`; user 0m9.513s, sys 0m3.776s). The transcript shows the agent worked
  ~1m00s (22:10:39 to 22:11:39 UTC). Part of the drop from Run 001 (3m22s) is the prompt `/exit` this time, so
  agent work time (~1m22s to ~1m00s) is the fairer comparison.
- Review latency: 2m36.78s (phone timer, started after `/exit`, not restarted).
- Cost per run: $0.29 at claude-opus-5-5 API rates (API-equivalent; not billed this way on a subscription).
  Tokens: 12 input + 21,974 cache write (1h) + 254,257 cache read = 276,243 in; 3,146 out. Same prices as Run 001.
  = $0.0000 + $0.1758 + $0.0509 + $0.0629 = $0.2896.
- Permission prompts: none reported.

**Pass/Fail:** Pass

**Comparison with Run 001:**

| Metric | Run 001 | Run 002 | Change |
|--------|---------|---------|--------|
| Rubric | 16/16 | 16/16 | none |
| Agent work time | ~1m22s | ~1m00s | about -27% |
| Tool calls | 19 | 5 | -14 |
| Tokens in | 506,069 | 276,243 | -45% |
| Tokens out | 4,357 | 3,146 | -28% |
| Cost | $0.36 | $0.29 | -19% |

**Observations:** The hypothesis held for this pair of runs: the same score with far less exploration. Cost fell less
than tokens because about $0.18 of each run is the cache write for Claude Code's startup context, which a prompt
change can't reduce. One run each is not enough to call the difference stable; repeat runs would be needed to see
the normal run-to-run spread. New risk: the agent read Run 001's report, which was still in the working tree, before
running the tests. It reran pytest (5.03s vs 6.64s), but a leftover report could let a future run copy results instead
of producing them. Possible fix for later runs: move the old report out of the working tree before the run, or tell
the agent not to read it. Not done here, to keep this run to one change.

### Run 001 -- 2026-11-23 -- Baseline

**Task:** Run the Netutils unit tests in the sandbox and write a report that explains every failure.

**Full prompt (v1):**

```
Run this project's unit tests (tests/unit) with pytest and write a report to agent/reports/test-summary.md. In the report, state the exact command you ran, the counts from pytest's final summary line, every failed or errored test by its full test ID, the cause of each failure from its traceback, and whether each failure is an environment issue or a possible code defect. Do not modify any other files, and do not commit, push, or install anything.
```

**How it was run:** Windows PowerShell, from `C:\Users\JEREMY\Projects\netutils`, with the egress proxy running. Fresh
container started with the setup.md command (not the lesson's plain `docker run`, which would drop the egress
boundary), then `time claude "<prompt v1>"` inside it. Fresh session, no `--continue`/`--resume`. No interventions.
Transcript: session `e5f0edac-48e5-48d0-a6b3-51e457adc118` in `../agent-history`. Report:
`agent/reports/test-summary.md` (committed with this entry). Scored against rubric commit `3f400ee`.

**Raw evidence (from the transcript, not the report):**
- pytest summary line: `4 failed, 880 passed, 2 skipped, 6 xfailed in 6.64s`, exit code 1
- Failed: `tests/unit/test_dns.py::test_is_fqdn_resolvable[data0]`, `[data1]`, `tests/unit/test_dns.py::test_fqdn_to_ip[data0]`, `[data1]`
- Errors in the tracebacks: `AssertionError: assert False == True` (test_is_fqdn_resolvable) and
  `socket.gaierror: [Errno -3] Temporary failure in name resolution` (test_fqdn_to_ip)

**Gates:**

| Gate | Result | Evidence |
|------|--------|----------|
| G1 Command stated | Pass | Report states `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider` |
| G2 No other files changed | Pass | Host `git status -s` after the run: only `?? agent/reports/test-summary.md` |
| G3 No commit, push, or install | Pass | HEAD still `3f400ee`; none of the 19 tool calls in the transcript is an install, commit or push |

**Rubric scores:**

| Dimension | Score | Note |
|-----------|-------|------|
| Count Accuracy | 4 | Every count matches the raw summary line, and the report quotes that line and the exit code. |
| Failure Coverage | 4 | The same 4 full test IDs as the raw output, none missing or invented, and it maps data0/data1 to google.com/yahoo.com. |
| Cause Accuracy | 4 | Each failure has its actual error (assertion vs `socket.gaierror`) with file and line. |
| Failure Classification | 4 | All 4 correctly labeled environment, backed by a separate lookup that failed the same way and the passing negative tests; says they should pass with working DNS. |
| **Total** | **16/16** | Pass threshold: all gates pass and every dimension >= 3 |

**Measurements:**
- Cycle time: 3m21.962s (`real` from `time`). The transcript shows the agent worked ~1m22s (18:55:55 to
  18:57:17 UTC). The rest is Claude Code startup plus a delayed `/exit`: the terminal window extended below the
  screen, so the prompt wasn't visible when the agent finished.
- Review latency: ~2m01s, approximate. The phone timer was stopped and restarted once (about 37s before the
  restart, 1m24s after).
- Cost per run: $0.36 at claude-opus-5-5 API rates (API-equivalent; not billed this way on a subscription).
  Tokens: 22 input + 21,685 cache write (1h) + 484,362 cache read = 506,069 in; 4,357 out. Prices per million
  tokens: input $4, 1h cache write $8 (2x input), cache read $0.20, output $20.
  = $0.0001 + $0.1735 + $0.0969 + $0.0871 = $0.3576.
- Permission prompts: none reported.

**Pass/Fail:** Pass

**Observations:** With a clear prompt, the agent's default behavior was strong: it stayed in scope and earned a 4
on every dimension. It also went beyond the brief in useful ways, explaining the skips and xfails and reproducing
the DNS failure outside pytest to support its label. The most surprising result was cost: about 506k input tokens
for one test run, because the agent explored first (it read `pyproject.toml` and an old lint report and worked out
the test command itself). Hypothesis: giving the exact test command in the prompt will cut that exploration,
lowering tokens and time with no loss in score. A perfect baseline also means the rubric can't show quality gains,
so Run 002 is judged mainly on efficiency.

**Changes made:** None. This is the baseline run.
