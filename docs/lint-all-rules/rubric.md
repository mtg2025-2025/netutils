# Quality Rubric: All-Rules Lint Summary Workflow

Derived from the acceptance criteria in [prd.md](prd.md). Module 1 Lab, Task 2.

## 1. Gates (pass/fail, not scored)

These acceptance criteria have only two meaningful states, so they stay binary.
If any gate fails, the run fails regardless of its rubric scores.

| Gate | PRD criterion | How to check |
|------|---------------|--------------|
| G1 Command stated | 1 | The report contains the exact ruff command(s) that were run. |
| G2 No other files changed | 6 | `git status` on the host shows no change except agent/reports/lint-all-rules.md, and no `.ruff_cache` folder exists in the worktree (ruff hides its cache from Git). |
| G3 No commit, push, or install | 7 | `git log` shows no new commit; the transcript shows no `git commit`, `git push`, `pip install` or `poetry add`. |

## 2. Dimensions

### 2.1 Total Findings (PRD criterion 2)
Measures whether the total number of findings in the report matches ruff's `Found N errors.` line.
A high score requires the exact number.

### 2.2 Top 10 Rules (PRD criterion 3)
Measures whether the 10 rules with the most findings are listed with their code, name and count,
in order, matching ruff's `--statistics` output. A high score requires the right rules, all ties
for 10th, and exact counts.

### 2.3 Top 10 Files (PRD criterion 4)
Measures whether the 10 files with the most findings are listed with their counts, in order,
matching ruff's per-finding (concise) output. A high score requires the right files, all ties for
10th, and exact counts.

### 2.4 Fixable Count (PRD criterion 5)
Measures whether the number of auto-fixable findings matches ruff's `[*] N fixable` line. A high
score requires the exact number, read correctly (the unsafe fixes on the same line are a separate
number).

## 3. Scoring Guide

Levels: **1** Does not meet · **2** Partially meets · **3** Meets (target) · **4** Exceeds.
Examples use the result recorded when the task was chosen (ruff 0.16.8, 2026-11-23): 1,106 findings,
393 fixable plus 179 unsafe fixes, top rule UP006 (242), top file netutils/config/parser.py (286).
Each run is scored against its own ruff output, not against these numbers (PRD edge cases).

### 3.1 Total Findings

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | Total missing, or not the number ruff reported. | No total given, or "1,060 findings". |
| 2 | Approximate or rounded, so it can't be checked exactly. | "About 1,100 findings." |
| 3 | Exact total matching ruff's output. | "1,106 findings." |
| 4 | Exact, and quotes ruff's line as evidence. | "1,106 findings (ruff: `Found 1106 errors.`)." |

### 3.2 Top 10 Rules

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | A rule missing or wrong, a tie for 10th left out, the order wrong, or counts that don't match ruff. | Lists 9 rules, leaving out EXE002 (35); or gives UP006 as 224. |
| 2 | The right 10 rules in the right order, but counts approximate or missing. | "UP006 non-pep585-annotation (200+), TRY003 raise-vanilla-args (~100), ..." |
| 3 | The right 10 rules in the right order, each with code, name and exact count. | "UP006 non-pep585-annotation 242, TRY003 raise-vanilla-args 95, E501 line-too-long 85, ..." |
| 4 | All of level 3, plus for each rule a one-line meaning and whether the project's config enables or ignores it. | "E501 line-too-long, 85: lines longer than the limit. Ignored on purpose in pyproject.toml." |

Rules with equal counts may appear in any order among themselves (e.g. ANN401, CPY001 and EXE002,
35 each).

### 3.3 Top 10 Files

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | A file missing or wrong, a tie for 10th left out, the order wrong, or counts missing, incorrect or fabricated. | Leaves out netutils/lib_mapper.py (47); or gives parser.py as 268. |
| 2 | The right 10 files in the right order, but counts approximate. | "netutils/config/parser.py (nearly 300), netutils/interface.py (over 100), ..." |
| 3 | The right 10 files in the right order, each with its exact count. | "netutils/config/parser.py 286, netutils/interface.py 115, netutils/acl.py 80, ..." |
| 4 | All of level 3, plus each file's most common rule with its count. | "netutils/config/parser.py, 286: mostly UP006 (64)." |

Files with equal counts may appear in any order among themselves (e.g. bandwidth.py and
_private/version.py, 51 each).

### 3.4 Fixable Count

| Level | Description | Example case |
|-------|-------------|--------------|
| 1 | Missing, or not ruff's number. | No count, or "572 fixable" (adds the 179 unsafe fixes). |
| 2 | Approximate. | "About 400 can be auto-fixed." |
| 3 | Exact. | "393 fixable." |
| 4 | Exact, and shows how the number was read: quotes ruff's line, or states the unsafe fixes separately. | "393 fixable with `--fix`; another 179 need `--unsafe-fixes` and are not included." |

### 3.5 Runs Where Ruff Can't Run

If ruff fails twice (PRD decision event 2), the four dimensions have nothing to measure. Score them
**N/A** (not 1 and not 4). The run passes only if all gates pass and the report contains ruff's error
output and says it stopped. Its log entry must say it is not comparable to runs where ruff ran. If
the report gives counts anyway, score every dimension 1 (fabricated).

### 3.6 Evidence Sources

Score the agent's report against evidence the agent did not write, never against the report itself.

| Evidence | Where it is | Used for |
|----------|-------------|----------|
| ruff `--statistics` output from the run (primary) | The run's session transcript in `../agent-history` (recorded by Claude Code) | Total Findings, Top 10 Rules, Fixable Count |
| ruff concise output from the run (primary) | The same transcript | Top 10 Files (count lines per file) |
| Reviewer's own rerun (cross-check) | The same two commands, run by the reviewer in a fresh sandbox container after the agent finishes | Confirms the transcript; needed if the transcript output is cut off |
| `ruff rule <CODE>` and `pyproject.toml` | Reviewer runs `ruff rule` in the container; config in the repo | Level 4 of Top 10 Rules |
| Host Git state and the worktree folder | `git status`, `git log`, and a check for `.ruff_cache` on Windows after the run | Gates G2 and G3 |

If the transcript's output is cut off (long output can be truncated), use the reviewer's rerun for
the missing part and note that in the log.

## 4. Pass Threshold

A run **passes** only if all three gates pass **and** every scored dimension scores **3 or higher**
(dimensions scored N/A under 3.5 are left out).

Reasoning: approximate numbers aren't facts you can make decisions on. A report that is exact on
three dimensions but approximate on the fourth still can't be trusted for that fourth number, so a
high score on one dimension must not hide a low score on another. A dimension floor prevents that.

Set on 2026-11-23, before the first run of this task.

## 5. Alternatives Considered

- **Total score minimum (e.g. at least 12 of 16):** ruled out because a run could score 1 on one
  dimension (a wrong number) and still pass by scoring 4 elsewhere.
- **Combining Total Findings and Fixable Count into one dimension:** ruled out because they are
  different criteria, and a combined score of 2 would not show which number was wrong.
- **A "bug-related" flag for each file at level 4:** ruled out because whether a finding is
  bug-related is a judgment call that two reviewers would score differently. Replaced with each
  file's most common rule, which can be checked from ruff's output.
