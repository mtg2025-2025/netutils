# PRD: Unit Test Summary Workflow

## Workflow description
This workflow runs the Netutils unit test suite inside the agent sandbox and writes
a report that explains every failure.

## Trigger
A developer starts the sandbox container with the documented command in setup.md
(egress proxy running) and runs `time claude "<task prompt>"` from /workspace, the
repo root. The trigger is manual; there is no automated hook.

## Decision events
1. If the test command finishes, the agent reports the counts from pytest's final
   summary line.
2. If any tests fail or error, the agent reads each traceback and labels the failure
   either "environment" (e.g. network blocked by the sandbox) or "possible code defect".
3. If the test command can't run at all (e.g. import error, missing package), the
   agent reports the error output and stops. It does not install anything or change
   the environment.
4. If a failure looks like a code defect, the agent describes it but does not edit
   any source or test file.

## Actions
1. Run the unit tests with the sandbox's standard command (setup.md).
2. Capture pytest's final summary line.
3. List every failed or errored test by its test ID.
4. For each failure, state the cause shown in its traceback and label it.
5. Write the report to agent/reports/test-summary.md.

## Acceptance criteria
1. The report states the exact test command that was run.
2. The pass/fail/skip/xfail counts in the report match pytest's summary line exactly.
3. Every failed or errored test from the run appears in the report by its test ID.
4. Each listed failure has a cause that matches its traceback.
5. Each failure's label (environment vs possible code defect) agrees with the
   traceback evidence.
6. (Gate) No file other than agent/reports/test-summary.md was created or changed
   (checked with `git status`).
7. (Gate) The agent did not commit, push, or install anything.

## Why this task
Chosen over three alternatives (added 2026-11-23 after Run 002; records the reasoning
and edge cases; no acceptance criterion or the pass threshold changed):
- Lint and summarize: in Module 1.2, Exercise 1, ruff, pylint and mypy all came back
  clean on netutils/ (0 findings, agent/reports/lint-report.md). A clean result gives
  the rubric almost nothing to score, so runs couldn't be told apart.
- Estimate test coverage: "estimate" and "weak area" are judgment calls, which makes
  falsifiable acceptance criteria hard to write.
- Build check: pass or fail only, too thin for three to six rubric dimensions.
The unit test run gives a known, repeatable result in the sandbox (4 test_dns failures
from blocked DNS, seen in Module 1.2, Exercise 1), with counts, IDs, causes and labels
that can each be checked against raw pytest output.

## Edge cases
- Skipped and xfailed tests are not failures: they must be counted (criterion 2) but
  need no ID, cause or label. Listing them is allowed.
- Errors (e.g. collection or setup errors) are treated like failures for criteria 3-5.
- No failures: criteria 3-5 don't apply (rubric 3.5).
- Overwriting an existing agent/reports/test-summary.md is allowed; it is still the
  one permitted change (criterion 6).
- Changing the environment to make tests pass (DNS, proxy, config) is not allowed,
  same as installing.
- Read-only checks that support a label (e.g. a separate DNS lookup) are allowed.
