# ADR 0003: Agent runs are scored with gates plus a dimension floor, against evidence the agent didn't write

- **Status:** Accepted
- **Date:** 2026-11-23
- **Context source:** Module 1.3, Exercise 1 (PRD, rubric and baseline for the unit test summary workflow).
  Files: `docs/prd.md`, `docs/rubric.md`, `docs/iteration-log.md`.

## Context

The workflow's output is a report (`agent/reports/test-summary.md`) that a reviewer should be able to trust without
rerunning pytest. Two questions came up while writing the rubric:

1. How should scores combine into pass or fail? Some acceptance criteria have only two meaningful states (did the
   agent change other files?), while others have degrees (one count wrong vs every count wrong).
2. How does a reviewer know the report is accurate, when the agent both ran the tests and wrote the report?

## Decision

1. **Gates plus a floor.** Criteria with only two states are binary gates (G1 command stated, G2 no other files
   changed, G3 no commit, push or install). The rest are dimensions scored 1-4 (Count Accuracy, Failure Coverage,
   Cause Accuracy, Failure Classification). A run passes only if every gate passes and every scored dimension is 3
   or higher. The threshold was set before the baseline run (rubric commit 8038fc9, Run 001 in 539d7ac).
2. **Independent evidence.** Score the report against the run's session transcript (raw pytest output, recorded by
   Claude Code), cross-checked by a reviewer rerun, and check the gates with host `git status` and `git log`. Never
   score the report against itself (rubric section 3.6).
3. **The bar changes only to fix a flaw.** Rubric changes are allowed to fix a gap or an error (for example the N/A
   rule for runs with no failures, rubric 3.5), never to lower the standard so a run passes.

## Alternatives considered

- **Aggregate minimum (12 of 16):** rejected. A run could score 1 on Count Accuracy and still pass by scoring 4
  elsewhere, which would accept a report with the wrong counts.
- **Count Accuracy as a gate:** rejected. "One count wrong" and "every count wrong" are different failures, and the
  score should show how close the run came.
- **A "report clarity" dimension:** rejected for now. It overlaps with the four dimensions and would be the hardest
  to score consistently.
- **Scoring from the report alone:** rejected. The agent wrote the report, so a wrong count in it would look right.
  Run 001 and Run 002 were both verified against the transcript: the summary lines (6.64s and 5.03s) differ, which
  also showed that Run 002 ran pytest itself rather than copying Run 001's report.

## Consequences

- Scoring takes longer: the reviewer has to open the transcript and check host Git state (review latency 2-2.5
  minutes per run in Module 1.3, Exercise 1).
- A perfect score on one run says nothing about stability; both runs scored 16/16, so the rubric couldn't show a
  quality gain, and improvement had to be measured as efficiency (tool calls, tokens, time, cost).
- The transcript has to be kept for every scored run (`../agent-history`, outside Git because transcripts can
  contain secrets).
- The same pattern (gates, a floor, independent evidence) is the starting point for the capstone's rubric design ADR
  and the eval harness in later modules.
