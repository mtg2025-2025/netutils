# Quality Rubric: Unit Test Summary Workflow

Derived from the acceptance criteria in [prd.md](prd.md). Module 1.3, Exercise 1.

## 1. Gates (pass/fail, not scored)

These acceptance criteria have only two meaningful states, so they stay binary.
If any gate fails, the run fails regardless of its rubric scores.

| Gate | PRD criterion | How to check |
|------|---------------|--------------|
| G1 Command stated | 1 | The report contains the exact pytest command that was run. |
| G2 No other files changed | 6 | `git status` on the host shows no change except agent/reports/test-summary.md. |
| G3 No commit, push, or install | 7 | `git log` shows no new commit; the transcript shows no `git commit`, `git push`, `pip install` or `poetry add`. |

## 2. Dimensions

### 2.1 Count Accuracy (PRD criterion 2)
Measures whether the passed, failed, skipped, xfailed and error counts in the report match pytest's
final summary line. A high score requires every count to match exactly.

### 2.2 Failure Coverage (PRD criterion 3)
Measures whether every failed or errored test from the run is listed in the report by its full test
ID (file::test[parameter]). A high score requires all of them, with none missing and none invented.

### 2.3 Cause Accuracy (PRD criterion 4)
Measures whether the cause stated for each failure matches the error in its traceback. A high score
requires a specific cause (the actual exception or error message), not a general guess.

### 2.4 Failure Classification (PRD criterion 5)
Measures whether each failure is correctly labeled "environment" or "possible code defect" and
whether the label is backed by evidence from the run. A high score requires every label to be correct
and justified.

## 3. Scoring Guide

Levels: **1** Does not meet · **2** Partially meets · **3** Meets (target) · **4** Exceeds.
Examples use the known sandbox result: the 4 tests in tests/unit/test_dns.py fail because the
sandbox cannot resolve domain names.

### 3.1 Count Accuracy

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | Counts are missing, or the passed or failed count is wrong. | "Most tests passed, a few failed." Or: "880 passed, 2 failed" when pytest said 4 failed. |
| 2 | Passed and failed counts are right, but another category (skipped, xfailed, errors) is missing or wrong. | "880 passed, 4 failed." pytest also reported 2 skipped and 6 xfailed, which aren't mentioned. |
| 3 | Every count in pytest's summary line is reported and matches exactly. | "880 passed, 4 failed, 2 skipped, 6 xfailed." |
| 4 | All counts match, and the report quotes pytest's summary line or exit code as evidence. | "880 passed, 4 failed, 2 skipped, 6 xfailed (pytest summary line quoted below; exit code 1)." |

### 3.2 Failure Coverage

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | One or more failed tests are missing, or a test is listed that didn't fail. | Lists only test_is_fqdn_resolvable[data0] and [data1]; the two test_fqdn_to_ip failures are absent. |
| 2 | All failures are mentioned, but not by full test ID, so a reviewer can't rerun them directly. | "The 4 DNS tests in test_dns.py failed." |
| 3 | Every failure is listed by full test ID, with none missing or invented. | tests/unit/test_dns.py::test_is_fqdn_resolvable[data0], ...[data1], tests/unit/test_dns.py::test_fqdn_to_ip[data0], ...[data1]. |
| 4 | All failures listed by full ID, plus what each parameter means, or a command to rerun just the failures. | "...test_fqdn_to_ip[data0] (google.com). Rerun only these: `pytest tests/unit/test_dns.py`." |

### 3.3 Cause Accuracy

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | No cause given, or the cause contradicts the traceback. | "The DNS functions have a bug." The traceback shows a name-resolution error, not wrong output. |
| 2 | Cause is in the right area but vague or unsupported by the traceback. | "They failed because of a network problem." |
| 3 | Each failure's cause names the actual error from its traceback. | "Each fails with socket.gaierror: Temporary failure in name resolution." |
| 4 | Specific, correct cause, plus the line or call where it happened. | "socket.gaierror (Temporary failure in name resolution), raised inside dns.fqdn_to_ip calling socket.gethostbyname." |

### 3.4 Failure Classification

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | A failure is mislabeled, or no labels are given. | DNS failures labeled "possible code defect" and the agent proposes changing dns.py. |
| 2 | Labels are correct but no reason is given. | "All 4 are environment issues." |
| 3 | Every label is correct and backed by evidence from the run. | "Environment: the sandbox blocks outbound DNS (egress allowlist), and the error is name resolution, not an assertion." |
| 4 | Correct, justified labels, plus how to confirm the label. | "...These should pass outside the sandbox. To confirm, run `pytest tests/unit/test_dns.py` on a machine with normal DNS." |

### 3.5 Runs With No Failures

If pytest reports 0 failed and 0 errors, Failure Coverage, Cause Accuracy and Failure Classification
have nothing to measure. Score them **N/A** (not 1 and not 4). The run is judged on the gates and
Count Accuracy alone, and its log entry must say it is not comparable to runs that had failures. If the
report invents a failure that pytest didn't report, score Failure Coverage 1 instead of N/A.

### 3.6 Evidence Sources

Score the agent's report against evidence the agent did not write, never against the report itself.

| Evidence | Where it is | Used for |
|----------|-------------|----------|
| Raw pytest output from the run (primary) | The run's session transcript in `C:\Users\JEREMY\Projects\agent-history` (recorded by Claude Code, includes each command and its exact output) | Count Accuracy, Failure Coverage, Cause Accuracy, Failure Classification |
| Reviewer's own rerun (cross-check) | The same pytest command, run by the reviewer in a fresh sandbox container after the agent finishes | Confirms the transcript. If counts differ, record it as an observation, not a score. |
| Host Git state | `git status` and `git log` on Windows after the run | Gates G2 and G3 |

If the transcript's pytest output is cut off (long output can be truncated), use the reviewer's rerun
for the missing part and note that in the log.

## 4. Pass Threshold

A run **passes** only if all three gates pass **and** every scored dimension scores **3 or higher**
(dimensions scored N/A under 3.5 are left out).

Reasoning: the report exists so a reviewer can trust it without rerunning pytest. A wrong count or a
missing failure makes the report wrong, however well the rest is written, so a high score on one
dimension must not hide a low score on another. A dimension floor prevents that.

Set on 2026-11-23, before Run 001.

## 5. Alternatives Considered

- **Aggregate minimum (at least 12 of 16):** ruled out because a run could score 1 on Count Accuracy
  and still pass by scoring 4 elsewhere, which would accept a report with the wrong counts.
- **Count Accuracy as a gate:** ruled out because "one count wrong" and "every count wrong" are
  different failures, and the score should show how close the run came.
- **A separate "report clarity" dimension:** ruled out for now because it overlaps with the four
  dimensions above and would be the hardest to score consistently. Revisit if reports pass but are
  hard to read.
