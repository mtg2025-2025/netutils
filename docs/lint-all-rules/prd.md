# PRD: All-Rules Lint Summary Workflow

Module 1 Lab, Task 2.

## Workflow description
This workflow runs ruff with every rule enabled on the netutils/ package inside the agent
sandbox and writes a summary of the findings, without changing any code.

## Trigger
A developer starts a sandbox container with the documented command in setup.md (egress
proxy running), mounting the Task 2 worktree as /workspace, and runs
`time claude "<task prompt>"` from /workspace. The trigger is manual; there is no
automated hook.

## Decision events
1. If ruff runs, the agent reports the total, the top 10 rules, the top 10 files and the
   fixable count from its output.
2. If ruff fails or crashes, the agent tries once more. If it fails again, the agent
   reports the error output and stops. It does not install anything or change the
   environment.
3. If rules or files are tied for 10th place, the agent includes all of the tied entries.
4. If a finding looks like a real bug, the agent describes it in the report but does not
   edit any file.
5. The agent never runs ruff with `--fix` or `--unsafe-fixes`. It reports the fixable
   count only.

## Actions
1. Run `ruff check netutils --select ALL --no-cache --statistics` and capture the
   per-rule counts, the total and the fixable count.
2. Run `ruff check netutils --select ALL --no-cache --output-format concise` and count
   the findings per file.
3. Pick the top 10 rules and the top 10 files by count, including any ties for 10th.
4. Write the report to agent/reports/lint-all-rules.md with the exact commands, the
   total, both top-10 lists with counts, and the fixable count.

## Acceptance criteria
1. (Gate) The report states the exact ruff command(s) that were run.
2. The total number of findings in the report matches ruff's `Found N errors.` line
   exactly.
3. The top 10 rules by count are listed, each with its code, name and count, all
   matching ruff's `--statistics` output. Ties for 10th place are all included.
4. The top 10 files by number of findings are listed, each with its count, all matching
   ruff's per-finding (concise) output. Ties for 10th place are all included.
5. The fixable count in the report matches ruff's `[*] N fixable` line.
6. (Gate) No file other than agent/reports/lint-all-rules.md was created or changed
   (checked with `git status`, plus a check that no `.ruff_cache` folder exists, because
   ruff hides its cache from Git). Running `--fix` or `--unsafe-fixes` fails this gate.
7. (Gate) The agent did not commit, push, or install anything.

## Why this task
Chosen over three alternatives:
- Normal lint (ruff, pylint and mypy with the project's own settings): 0 findings in
  Module 1.2, Exercise 1, so there is nothing to score.
- Normal type check (mypy): 0 errors, the same problem.
- Strict type check (`mypy --strict`): 2 errors, too few to rank or to tell good runs from
  weak ones.

All-rules lint had 1,106 findings across about 84 rules when the task was chosen
(2026-11-23), enough to rank a top 10 of rules and of files, and every count can be
checked exactly against ruff's own output.

## Edge cases
- Scoring source: counts are judged against the ruff output from the same run, not
  against the 1,106 recorded when the task was chosen. Code or ruff version changes can
  change the numbers.
- `EXE002` (file is executable): Git stores these files as not executable (mode 100644,
  checked with `git ls-files -s`), so the flag comes from how the Windows folder appears
  inside Docker, not from the code. The agent may note this; it is not required.
- Hidden cache: a `.ruff_cache` folder counts as a created file under criterion 6, even
  though `git status` does not show it.
- Overwriting an existing agent/reports/lint-all-rules.md is allowed; it is still the one
  permitted change (criterion 6).
- Read-only commands that support the report (e.g. reading a file to describe a possible
  bug) are allowed.
