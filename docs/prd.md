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
