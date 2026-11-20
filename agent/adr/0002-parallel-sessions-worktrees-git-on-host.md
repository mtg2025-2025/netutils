# ADR 0002: Parallel agent sessions use one worktree and one sandboxed container each, with Git on the host

- **Status:** Accepted
- **Date:** 2026-11-20
- **Context source:** Module 1.2, Exercise 1 (two parallel agent sessions). The Git problem was first found in the Module 1.2 lesson practice on 2026-11-19.

## Context

Running two agent sessions at once on the same repository needs each session to have its own files and branch. Otherwise one session's edits can overwrite the other's, and the two results can't be reviewed or merged separately. Git worktrees give each session its own folder on its own branch, and each folder is mounted into its own agent container at `/workspace`.

Two questions came up while setting this up:

1. **Which container command to use.** The exercise's example command is `docker run -it --rm -v "${PWD}:/workspace" -v "claude-auth:/claude-auth" your-agent-image:latest`. It has no network settings, so a container started that way can reach the whole internet, which would drop the egress boundary from ADR 0001.
2. **Where Git runs.** In a worktree, `.git` is not a folder. It's a one-line file pointing at the main repository by its host path, for example `gitdir: C:/Users/JEREMY/Projects/netutils/.git/worktrees/netutils-vlan-tests`. That Windows path doesn't exist inside the Linux container, so every Git command there fails. Seen in the lesson practice: `fatal: not a git repository: /workspace/C:/Users/JEREMY/Projects/LaunchCodeAgenticEngineer/.git/worktrees/repo-agent-b`.

## Decision

- **Each session gets one worktree and one container, started with the full sandbox command from `setup.md`:**

      docker run -it --rm --network agent-net -e HTTPS_PROXY=http://egress-proxy:8888 -e HTTP_PROXY=http://egress-proxy:8888 -v claude-auth:/claude-auth -v "${PWD}:/workspace" -v "${PWD}/../agent-history:/root/.claude/projects" netutils-agent

  It's run from inside each worktree folder, so `${PWD}` mounts only that worktree. Both containers share the `claude-auth` login volume and the `agent-history` transcript folder, both outside the repository. Each transcript is a separate file named by its session ID, so the two sessions' metrics stay distinct.
- **Agents don't run Git.** Each session's prompt and the scope contract (`session_tasks.md`) say so. The orchestrator reviews, commits, merges and pushes from the Windows host, where the worktree paths are valid.

## Alternatives considered

- **The exercise's basic `docker run` command.** Rejected. It drops the network boundary: no `--network agent-net` and no proxy, so the agents would have unrestricted internet access.
- **Git inside the container, using relative worktree paths plus a mount of the main `.git`.** Git 2.48 and later can write relative paths (`git worktree add --relative-paths`), and mounting the main repository's `.git` into each container would make them resolve. Rejected. Every worktree shares that one `.git` database, which holds all branches, refs and objects. Mounting it writable into both containers would let either agent change the other session's branch, or the main branch, which undoes the isolation the worktrees provide. It would also let an agent commit work before anyone has reviewed it.
- **Mounting the whole repository folder into both containers.** Rejected. That is the shared-directory setup this design exists to avoid.

## Consequences

- **Good:**
  - Each session can write only to its own worktree.
  - Each session keeps the Module 1.1 network allowlist.
  - Nothing reaches a branch without a human review on the host, because only the orchestrator commits.
  - In Module 1.2, Exercise 1, both sessions' changes stayed in their own worktrees (one file each), and both branches merged without conflicts.
- **Costs:**
  - The agents can't use Git history (`git log`, `git blame`) while they work.
  - The orchestrator has to commit each session's work by hand.
  - `git diff` doesn't show a session's new untracked files until they're staged (`git add -N`) or committed.
- **Not covered by this decision:** the per-session command lists are only requested in the prompt, not enforced. In Module 1.2, Exercise 1, both agents ran read-only shell tools outside their lists. Enforcing the lists with Claude Code permission rules in the container is an open item in the iteration log.
