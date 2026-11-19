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
- **Network mode:** `agent-net` only, an internal network with no internet route. The `HTTPS_PROXY` and `HTTP_PROXY` settings point programs at the proxy, but the internal network is what enforces the boundary: even a program that ignores the proxy settings can't get out.
- **Session history:** `../agent-history` (a folder next to the repository, not inside it) is mounted at `/root/.claude/projects`, where Claude Code saves each session's transcript and token usage. It survives after the container exits, so each run's usage can be reported with `python agent/tools/session_report.py`. It's kept out of the repository because transcripts include everything the agent read. Create the folder once before the first run: `mkdir ../agent-history`.
- **Login storage:** `claude-auth` is a Docker named volume that saves the Claude Code login between runs. It stays outside the project folder, so the login can never be committed to Git.
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

Result: a site not on the allowlist is refused by the proxy (403), bypassing the proxy fails because the network has no route out, and Anthropic's API is reachable (404 means the server answered).

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

**Verified afterward on Windows:** `git status` showed only the new, untracked files (`Dockerfile.agent`, `agent/`, `agent-smoke-test.md`, `setup.md`). No project files were modified, and nothing was committed or pushed.

**Expected failures:** the 4 failing tests in `tests/unit/test_dns.py` look up google.com and yahoo.com. The sandbox has no DNS access to the internet, so they fail. That's a sign the network boundary is working, not a code problem. On the earlier unrestricted network, the same suite was 840 passed, 0 failed.

**Issue found and fixed:** in an earlier run, Git inside the container showed about 610 files as modified. They weren't real changes. Windows Git checks files out with Windows line endings, and Git inside the Linux container counted every line as changed. `Dockerfile.agent` now sets `git config --global core.autocrlf true`, and in this run Git inside the container showed no modified files.

## Security decisions

These answers reflect the first version of this setup.

### Why mount only this folder?

The agent's work (editing code, adding tests, running pytest and the linters, and making commits) only needs what's inside the Netutils project folder: the code, tests, `pyproject.toml`, `poetry.lock` and the Git history. Netutils is a self-contained library with no local services and no credentials, so nothing outside the folder is needed. Mounting only this folder means a mistake or a misled agent can't read or change anything else on my computer, such as my home folder, Desktop, Downloads, SSH keys or cloud credentials. Without this boundary, an agent that was tricked by malicious text could read my SSH keys and use them to get into other systems. The course repo isn't mounted either, because the files I needed from it were copied into the project. My GitHub login also stays out of the container: the agent can commit locally, and I review the work and push to GitHub myself.

### What is ephemeral?

Everything in the container outside the two mounts (`/workspace` and the `claude-auth` login volume) is ephemeral. The container runs with `--rm`, so it's deleted on exit, along with `/tmp`, scratch files, temporary downloads, shell history and anything installed during the session. I verified this by writing a file to `/tmp`, exiting, and confirming it was gone. Every session starts fresh from the same image, so a mistake or a bad install in one session can't carry into the next.

### What persists?

Three things persist. The first is the project folder, mounted at `/workspace`. The agent's code changes, new tests, output files and Git commits are written straight to my real Netutils folder on Windows, so they survive after the container exits and I can review them. I verified this by writing a test file to `/workspace` and finding it on Windows after exiting.

The second is the `claude-auth` Docker volume, which holds only the Claude Code login so I don't have to log in every session. It's kept separate from the project folder, so the login can never be committed to Git.

Session history is also kept, in the `agent-history` folder next to the repository. Claude Code writes each session's transcript and token usage there, so cost and effort can be measured for every run. It's a deliberate widening of what persists, recorded in the iteration log. The trade-off is that the agent can write to that one extra folder, and transcripts contain whatever the agent read, so the folder stays out of Git.

The third is the Docker image itself, with its tools and dependencies. It's reused for every session, but the agent can't change it: each container writes to a temporary layer that's discarded on exit. The image only changes when I edit `Dockerfile.agent` and rebuild it.

The network setup also persists: the `agent-net` network and the `egress-proxy` container stay in place between sessions. The agent can't change them, because the proxy's allowlist is built into its image, outside the agent's container.

### Dependencies in the image

The image starts from `python:3.12-slim`, because Netutils supports Python 3.10–3.14 and 3.12 matches the course image. On top of that I included:

- Linux tools from the course image: git (so the agent can inspect history and commit), curl, bash, ca-certificates, nano and procps, plus Node.js and npm, which Claude Code needs.
- Poetry 2.1.3, the package manager Netutils uses, pinned to the same version as the project's own Dockerfile.
- Netutils' own dependencies, development tools and optional extras, installed with `poetry install --with dev --all-extras` from the project's `poetry.lock`. That gives the agent pytest and coverage for testing, ruff, pylint, mypy and yamllint (the same checks the project's CI runs), and the libraries the tests need.
- Claude Code, the coding agent, with the course's settings and status line.

I removed the course's general Python packages (Streamlit, Flask, the Slack and Google libraries and so on), OpenCode and ngrok. Netutils doesn't use them. ngrok in particular opens tunnels from the internet into the container, which an agent sandbox shouldn't allow.

The separate proxy image contains only Alpine Linux and tinyproxy.

### What the smoke test proved

- The image has everything the agent needs. Claude Code started and logged in through the proxy, and pytest ran the full suite: 836 passed, 4 failed, 2 skipped.
- The network boundary holds. The only failures were the 4 DNS tests that need to look up google.com and yahoo.com. On the earlier unrestricted network, the same tests passed, so the difference comes from the boundary. Together with the egress check, this shows the agent can reach Anthropic's API and nothing else.
- The agent could work using only the mounted folder. It found the project, its test settings and its Git history in `/workspace` with no access to anything else.
- Its output persisted. `agent-smoke-test.md` appeared in my Netutils folder on Windows after the container exited.
- It stayed within its limits. `git status` on Windows afterward showed only new files, with no project files modified and nothing committed or pushed.

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
