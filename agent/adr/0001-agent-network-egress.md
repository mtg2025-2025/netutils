# ADR 0001: Restrict the agent container's network to an allowlist proxy

- **Status:** Accepted
- **Date:** 2026-11-18
- **Context source:** Module 1.1, Exercise 2 (agent sandbox)

## Context

The coding agent (Claude Code) runs in a Docker container with only the project folder mounted. The network boundary still had to be decided. Two needs pull in opposite directions:

- **The agent needs the internet for one thing:** Claude Code sends its work to Anthropic's API (`api.anthropic.com`), and its login uses a few Anthropic and Claude domains. Netutils' own code and tests don't need the internet, apart from 4 DNS lookup tests.
- **An agent with open internet access is a data-exfiltration and download risk.** A mistaken or prompt-injected agent could send code or credentials to any server, or download and run untrusted code.

## Decision

Put the agent container on an **internal Docker network (`agent-net`) with no route to the internet**. Its only way out is a separate **tinyproxy container (`egress-proxy`)** that is connected to both `agent-net` and Docker's normal `bridge` network. The proxy:

- forwards only HTTPS (`ConnectPort 443`)
- forwards only to the domains in `agent/proxy/allowlist.txt`: `api.anthropic.com`, `platform.claude.com`, `console.anthropic.com` and `claude.ai`
- refuses everything else (`FilterDefaultDeny Yes`) and logs each request

The internal network enforces the boundary, not the `HTTPS_PROXY` setting. A program that ignores the proxy setting still can't get out.

## Alternatives considered

| Alternative | Why rejected | Evidence |
|---|---|---|
| **Docker's default bridge network** (no restriction) | Egress is unconstrained, so the agent could reach any host. | This was the first configuration, used in smoke test 1. Self-review against the Module 1.1, Exercise 2 rubric rated it "Developing: network egress is unconstrained". |
| **`--network none`** (no network at all) | Claude Code can't reach Anthropic's API, so the agent can't work. | Claude Code sends every request to `api.anthropic.com`. With no network, the container has no route to it. |
| **Host firewall rules** (Windows Firewall or iptables on the Docker host) | Rules would live outside the repository, differ between Windows, macOS and Linux, and couldn't be forked or reviewed with the code. | The capstone requires a forkable repo that a stranger can run in under 15 minutes. |
| **A full proxy such as Squid** | It would also work, but it's heavier and needs more configuration than this allowlist requires. | tinyproxy's whole configuration is 11 lines, and the image is Alpine (about 8 MB). |

## Evidence the decision works

Egress check, run inside the agent container on 2026-11-18:

```
ai-course:/workspace# curl -sS -m 10 https://example.com
curl: (56) CONNECT tunnel failed, response 403
ai-course:/workspace# curl -sS -m 10 --noproxy "*" https://example.com
curl: (6) Could not resolve host: example.com
ai-course:/workspace# curl -sS -m 10 -o /dev/null -w "%{http_code}\n" https://api.anthropic.com
404
```

- Smoke test 2 on the restricted network: Claude Code worked normally. The tests came out 836 passed, 4 failed and 2 skipped, and the only failures were the DNS tests that need the internet.
- The proxy log (`agent/logs/2026-11-18-egress-proxy.log`) shows that unprompted attempts to reach `github.com`, `registry.npmjs.org`, `downloads.claude.ai`, `mcp-proxy.anthropic.com` and a telemetry endpoint were all refused.

## Consequences

- **Good:** the agent can reach only Anthropic. Exfiltration to arbitrary servers and downloads from arbitrary sources are blocked, and every outbound request is logged, which gives an audit trail.
- **Cost:** the 4 tests in `tests/unit/test_dns.py` always fail inside the sandbox and have to be treated as known failures. Two more one-time setup commands are needed (create the network, start the proxy).
- **Cost:** Claude Code can't update itself inside the container, because `downloads.claude.ai` is blocked. Updates happen only by rebuilding the image, which keeps the environment reproducible.
- **Future:** later course modules may add MCP servers or other tools. Each one that needs network access must be added to the allowlist on purpose, with a justification, which matches the "justification-to-widen" governance requirement.

## Open risks

- **The domain allowlist doesn't inspect content.** A misled agent could still send data to an allowed domain, for example by using a different API key to reach another Anthropic account. Mitigation: review `docker logs egress-proxy` for unexpected volume or destinations, and consider alerting on it later.
- **The proxy container has internet access.** If it were compromised, the boundary would be gone. It runs no agent code and holds no credentials.
