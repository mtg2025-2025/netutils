# Agent Sandbox Setup

This file explains how to run a coding agent (Claude Code) safely against this repository inside a Docker container. It is the baseline setup for the LaunchCode Agentic Engineer course and will be updated as the course goes on.

## Build the images

```
docker build -f Dockerfile.agent -t netutils-agent .
docker build -t egress-proxy agent/proxy
```

- `Dockerfile.agent` is the agent's container recipe. It's adapted from the course's `module_1/Dockerfile`, and it's kept separate from the project's own `Dockerfile`, which Netutils' CI uses.
- The agent image includes Python 3.12, Poetry 2.1.3, Netutils' dependencies and dev tools (pytest, ruff, pylint, mypy), Git and Claude Code.
- Removed from the course image: the course's general Python packages, OpenCode and ngrok. The agent doesn't need them.
- `agent/proxy/` builds a small allowlist proxy (Alpine Linux and tinyproxy). It's the agent's only way out to the internet.

## One-time network setup

```
docker network create --internal agent-net
docker run -d --name egress-proxy --network agent-net --restart unless-stopped egress-proxy
docker network connect bridge egress-proxy
```

- `agent-net` is an internal Docker network with no route to the internet.
- `egress-proxy` sits on both `agent-net` (inside) and Docker's default `bridge` network (outside), like a firewall with an inside and an outside interface. It forwards only HTTPS traffic to the domains in `agent/proxy/allowlist.txt` and refuses everything else (`FilterDefaultDeny Yes`).
- Allowed domains: `api.anthropic.com` (where Claude Code sends its work), plus `platform.claude.com`, `console.anthropic.com` and `claude.ai` (for logging in and keeping the login active).
- `--restart unless-stopped` starts the proxy again automatically after a reboot.

## Run the container

Run this from the root of your clone of the repository. `${PWD}` is the current folder.

PowerShell:

```
docker run -it --rm --network agent-net -e HTTPS_PROXY=http://egress-proxy:8888 -e HTTP_PROXY=http://egress-proxy:8888 -v claude-auth:/claude-auth -v "${PWD}:/workspace" -v "${PWD}/../agent-history:/root/.claude/projects" netutils-agent
```

macOS, Linux or Git Bash:

```
docker run -it --rm --network agent-net -e HTTPS_PROXY=http://egress-proxy:8888 -e HTTP_PROXY=http://egress-proxy:8888 -v claude-auth:/claude-auth -v "$(pwd):/workspace" -v "$(pwd)/../agent-history:/root/.claude/projects" netutils-agent
```

Then start the agent inside the container with `claude`. On the first run, Claude Code asks you to log in once. The login is saved in the `claude-auth` volume for later runs.

- **Mounted path:** only this project folder, mounted at `/workspace`. The rest of the computer (home folder, Desktop, Downloads, SSH keys, cloud credentials) is not mounted.
- **Network mode:** `agent-net` only, an internal network with no internet route. The `HTTPS_PROXY` and `HTTP_PROXY` settings point programs at the proxy, but the internal network is what enforces the boundary: a program that ignores the proxy settings has no route out. The `--noproxy` test below confirmed this for `curl`.
- **Session history:** `../agent-history` (a folder next to the repository, not inside it) is mounted at `/root/.claude/projects`, where Claude Code saves each session's transcript and token usage. It survives after the container exits, so each run's usage can be reported with `python agent/tools/session_report.py`. It's kept out of the repository because transcripts include everything the agent read. Create the folder once before the first run: `mkdir ../agent-history`.
- **Login storage:** `claude-auth` is a Docker named volume that saves the Claude Code login between runs. It's stored outside the project folder, so by default the login isn't part of anything committed to Git. The agent can still read the credential inside the container (see Remaining risks), so it could copy it into the project if it were misled. Reviewing changes before committing is the check for that.
- **No ports opened:** the course command opens port 8501 for web apps. Netutils has no web app, so no ports are published.
- **`--rm`:** the container is deleted when you exit. Only changes inside `/workspace` are kept.

## Boundary checks

These were run inside the container on 2026-11-18:

| Check | Command | Result |
|---|---|---|
| Project is visible | `ls` in `/workspace` | All Netutils files listed |
| Windows drive is hidden | `ls /mnt/c` | `No such file or directory` |
| No personal credentials | `ls -a /root` | Only image-built files (`.bashrc`, `.claude`, `.config`, caches). No `.ssh`, no cloud credentials. |
| `/workspace` persists | Wrote `/workspace/persist-test.txt`, exited | File was present on Windows afterward (then deleted) |
| `/tmp` is temporary | Wrote `/tmp/temp-test.txt`, exited | Gone with the container |

## Network egress check

Run inside the agent container on 2026-11-18. The container is on `agent-net`, an internal Docker network with no internet route. Its only way out is the `egress-proxy` container, which allows only Anthropic's domains.

```
ai-course:/workspace# curl -sS -m 10 https://example.com
curl: (56) CONNECT tunnel failed, response 403
ai-course:/workspace# curl -sS -m 10 --noproxy "*" https://example.com
curl: (6) Could not resolve host: example.com
ai-course:/workspace# curl -sS -m 10 -o /dev/null -w "%{http_code}\n" https://api.anthropic.com
404
ai-course:/workspace#
```

Result: in these tests, a site not on the allowlist (`example.com`) was refused by the proxy (403), bypassing the proxy failed because the network has no route out, and Anthropic's API was reachable (404 means the server answered). These checks confirm the cases tested. They don't prove that every other destination is unreachable. The design is what should block the rest: the internal network has no route out, and the proxy refuses any domain not on the allowlist (`FilterDefaultDeny Yes`). The proxy log from the smoke tests adds supporting evidence: it shows real requests to GitHub, npm and other sites being refused.

## Smoke test

Run on the restricted network on 2026-11-18.

**Prompt given to Claude Code inside the container:**

```
Run this project's unit tests with pytest and summarize the results. Write the summary to /workspace/agent-smoke-test.md. Do not modify any other files, and do not commit, push, or install anything.
```

**Agent output:** the agent's final reply in the terminal:

```
The unit tests ran with 836 passed, 4 failed and 2 skipped, out of 842 (exit code 1). All 4 failures are because this sandbox can't look up domain names, not because of the code. I wrote the summary to /workspace/agent-smoke-test.md.

- Failures: all four are in tests/unit/test_dns.py: test_is_fqdn_resolvable and test_fqdn_to_ip, each run for google.com and yahoo.com. They need to look up real domain names, and here the lookup fails ("Temporary failure in name resolution"). They should pass on a machine with working DNS.
- Skips: two tests in tests/unit/test_lib_helpers_optionals.py are skipped. They need the optional napalm package, which is installed but fails to load because pkg_resources is missing. I left that alone since you said not to install anything.
- Warnings: pytest couldn't collect four helper classes in tests/unit/test_acl.py. That's harmless.

agent-smoke-test.md already held a summary from an earlier run today, and I replaced it. That run reported 840 passed and 0 failed, so DNS probably worked then.

I ran only tests/unit, not tests/integration. I set the run so pytest wrote no cache or bytecode files, and git status confirms no other file changed. Nothing was committed or pushed.
```

The full summary the agent wrote is in `agent-smoke-test.md`, which is on the Windows side of the mount. Its results table:

```
| Outcome | Count |
|---------|-------|
| Passed  | 836   |
| Failed  | 4     |
| Errors  | 0     |
| Skipped | 2     |
```

**Exact test command the agent ran** (recorded in `agent-smoke-test.md`):

```
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider \
  -o addopts="--doctest-modules -p no:warnings --ignore-glob=*mock*"
```

This is the project's own pytest configuration from `pyproject.toml` without `-vv`. Turning off the cache and bytecode files keeps pytest from writing anything into the repository. (`agent-smoke-test.md` is dated 2026-11-19 because the container's clock uses UTC. On Windows it was the evening of 2026-11-18.)

**Verified afterward on Windows:** `git status` showed only the new, untracked files (`Dockerfile.agent`, `agent/`, `agent-smoke-test.md`, `setup.md`). No project files were modified, and nothing was committed or pushed. The `git status` output wasn't saved at the time. The record that can be checked now is below.

The summary file is on the Windows side of the mount, written during the session:

```
PS> Get-Item agent-smoke-test.md

Mode   LastWriteTime         Length Name
----   -------------         ------ ----
-a---- 11/18/2026 7:55:18 PM   2600 agent-smoke-test.md
```

The commit that added the sandbox work contains only new files. None of Netutils' existing source or test files appear, and nothing was deleted:

```
PS> git show --stat 5023f60

 .gitattributes             |   2 +
 Dockerfile.agent           |  55 ++++++++++++++
 agent-smoke-test.md        |  54 ++++++++++++++
 agent/docker-entrypoint.sh |  34 +++++++++
 agent/proxy/Dockerfile     |   5 ++
 agent/proxy/allowlist.txt  |   4 +
 agent/proxy/tinyproxy.conf |  11 +++
 agent/settings.json        |   7 ++
 agent/statusline.sh        | 127 ++++++++++++++++++++++++++++++++
 setup.md                   | 178 +++++++++++++++++++++++++++++++++++++++++++++
 10 files changed, 477 insertions(+)
```

For future smoke tests, `git status` and `dir` are run on Windows right after the session, and their output is pasted here as is.

**Expected failures:** the 4 failing tests in `tests/unit/test_dns.py` look up google.com and yahoo.com. The sandbox has no DNS access to the internet, so they fail. That's a sign the network boundary is working, not a code problem. On the earlier unrestricted network, the same suite was 840 passed, 0 failed.

**Issue found and fixed:** in an earlier run, Git inside the container showed about 610 files as modified. They weren't real changes. Windows Git checks files out with Windows line endings, and Git inside the Linux container counted every line as changed. `Dockerfile.agent` now sets `git config --global core.autocrlf true`, and in this run Git inside the container showed no modified files.

## Security decisions

These answers reflect the first version of this setup.

### Why mount only this folder?

The agent's work (editing code, adding tests, running pytest and the linters, and making commits) only needs what's inside the Netutils project folder: the code, tests, `pyproject.toml`, `poetry.lock` and the Git history. Netutils is a self-contained library with no local services and no credentials, so nothing outside the folder is needed. Mounting only this folder means a mistake or a misled agent has no direct way to read or change anything else on my computer (short of escaping the container, see Remaining risks), such as my home folder, Desktop, Downloads, SSH keys or cloud credentials. Without this boundary, an agent that was tricked by malicious text could read my SSH keys and use them to get into other systems. The course repo isn't mounted either, because the files I needed from it were copied into the project. My GitHub login also stays out of the container: the agent can commit locally, and I review the work and push to GitHub myself.

### What is ephemeral?

Everything in the container outside the two mounts (`/workspace` and the `claude-auth` login volume) is ephemeral. The container runs with `--rm`, so it's deleted on exit, along with `/tmp`, scratch files, temporary downloads, shell history and anything installed during the session. I verified this by writing a file to `/tmp`, exiting, and confirming it was gone. Every session starts fresh from the same image, so a bad install or scratch file doesn't carry into the next session. The exception is anything written to the persistent folders, `/workspace` or `agent-history`, which is why changes there are reviewed.

### What persists?

Three things persist. The first is the project folder, mounted at `/workspace`. The agent's code changes, new tests, output files and Git commits are written straight to my real Netutils folder on Windows, so they survive after the container exits and I can review them. I verified this by writing a test file to `/workspace` and finding it on Windows after exiting.

The second is the `claude-auth` Docker volume, which holds only the Claude Code login so I don't have to log in every session. It's kept separate from the project folder, so by default the login isn't committed to Git. The agent can still read it, though, so separate storage lowers the risk without removing it.

Session history is also kept, in the `agent-history` folder next to the repository. Claude Code writes each session's transcript and token usage there, so cost and effort can be measured for every run. It's a deliberate widening of what persists, recorded in the iteration log. The trade-off is that the agent can write to that one extra folder, and transcripts contain whatever the agent read, so the folder stays out of Git.

The third is the Docker image itself, with its tools and dependencies. It's reused for every session, but nothing the agent does inside a container changes the image: each container writes to a temporary layer that's discarded on exit. The image only changes when I edit `Dockerfile.agent` and rebuild it.

The network setup also persists: the `agent-net` network and the `egress-proxy` container stay in place between sessions. The agent can't change them, because the proxy's allowlist is built into its image, outside the agent's container.

### Dependencies in the image

The image starts from `python:3.12-slim`, because Netutils supports Python 3.10–3.14 and 3.12 matches the course image. On top of that I included:

- Linux tools. Each one is kept for a specific reason. The base image, `python:3.12-slim`, has none of `ps`, `vi`, `vim` or `nano` (checked with `command -v` on 2026-11-19):

| Tool | Why the agent environment needs it |
|---|---|
| `git` | The agent reads the project's history (`git log`, `git diff`), checks its own changes with `git status`, and makes local commits for me to review. |
| `curl` | Downloads the Poetry installer at build time, and runs the egress checks (blocked and allowed requests) in this document. |
| `ca-certificates` | Lets HTTPS connections verify certificates: Claude Code's calls to `api.anthropic.com` through the proxy, and `curl` at build time. |
| `bash` | Runs the image's entrypoint script and the status line script, and is the shell Claude Code uses to run commands such as pytest. |
| `procps` | Provides `ps`. Claude Code itself runs `ps -o ppid= -p <pid>`, `ps -o command= -p <pid>` and `ps -o lstart= -p <pid>` to track and clean up the processes it starts, such as a pytest run that has to be stopped. I found these commands in the Claude Code program installed in the image (version 2.1.327). Without `procps`, the slim image has no `ps`. |
| `nano` | Claude Code opens a text editor for longer input, such as editing a prompt in an editor (Ctrl+G) or editing its memory file. When `EDITOR` isn't set, it looks for `code`, then `vi`, then `nano`. The slim image has none of them, so without `nano` those features would have no editor. It also lets me read or fix a file by hand inside the container. |
| `nodejs`, `npm` | Install and run Claude Code, which is distributed through npm. |

- Poetry 2.1.3, the package manager Netutils uses, pinned to the same version as the project's own Dockerfile.
- Netutils' own dependencies, development tools and optional extras, installed with `poetry install --with dev --all-extras` from the project's `poetry.lock`. That gives the agent pytest and coverage for testing, ruff, pylint, mypy and yamllint (the same checks the project's CI runs), and the libraries the tests need.
- Claude Code, the coding agent, with the course's settings and status line.

I removed the course's general Python packages (Streamlit, Flask, the Slack and Google libraries and so on), OpenCode and ngrok. Netutils doesn't use them. ngrok in particular opens tunnels from the internet into the container, which an agent sandbox shouldn't allow.

The separate proxy image contains only Alpine Linux and tinyproxy.

### What the smoke test showed

- The image had everything this task needed. Claude Code started and logged in through the proxy, and pytest ran the full unit suite: 836 passed, 4 failed, 2 skipped. Later tasks may need more, and anything added will be justified the same way.
- The network boundary held for this run. The only failures were the 4 DNS tests that need to look up google.com and yahoo.com. On the earlier unrestricted network, the same tests passed, so the difference comes from the boundary. Together with the egress check, this is consistent with the agent reaching Anthropic's API and being refused elsewhere. It confirms the cases tested, not every possible destination.
- The agent could work using only the mounted folder. It found the project, its test settings and its Git history in `/workspace` without needing anything outside it.
- Its output persisted. `agent-smoke-test.md` appeared in my Netutils folder on Windows after the container exited.
- It stayed within its limits. `git status` on Windows afterward showed only new files, with no project files modified and nothing committed or pushed. The commit record above (`git show --stat 5023f60`: only new files, no deletions) is the evidence that can still be checked.

The first run also surfaced a real problem: Git inside the container saw about 610 files as changed because of Windows line endings. I fixed that in the Dockerfile before letting any agent make commits.

### Remaining risks

- **Data can still be sent to allowed domains.** Outbound traffic is limited to Anthropic's domains, but the proxy only checks the domain name, not what's sent. Everything the agent reads goes to Anthropic's API as part of its normal work, which is acceptable for a public open-source project but wouldn't be for private code. A misled agent could also use its own API key to send data to a different Anthropic account. Without the allowlist, the same agent could send my code or credentials to any server on the internet. A next step is to log and review the proxy's traffic (`docker logs egress-proxy`) for unexpected destinations.
- **The agent has full control of the project folder.** It can edit or delete any file in `/workspace`, including the `.git` history. The rest of my computer is protected, and GitHub is protected because the agent has no credentials to push. Even so, I need to review changes (`git status`, `git diff`) before I commit or push anything.
- **The agent runs as root inside the container.** If it escaped the container through a Docker vulnerability, it would have more power than a limited user would. Running as a non-root user is a possible later improvement.
- **The Claude login is inside the container.** The agent's session can read its own credential in `/root/.claude` and the `claude-auth` volume. It's limited to my Claude account, but it's still a credential inside the sandbox.
- **Prompt injection.** Text the agent reads, such as GitHub issues, code comments or test data, could contain instructions that try to make it act against my intent. The mount, the missing push credentials and the network allowlist all limit what such instructions could do.
- **Build-time supply chain.** Building the image downloads Claude Code (latest version, not pinned) and Poetry's installer from the internet. A compromised download would end up in the image. Netutils' Python packages are pinned by `poetry.lock`, which reduces this risk for them.
- **DNS tests can't pass in the sandbox.** The 4 tests in `tests/unit/test_dns.py` always fail here. Agents and reviewers need to know these 4 failures are expected, so they don't hide a real failure in the same file.

These risks are based on the current environment and are subject to change based on remaining requirements throughout this course.
