"""End-of-exercise checkup: are the course files intact, committed, and free of secrets?

Each check targets a problem that actually happened during the course (see
agent/iteration-log.md) or a risk the capstone rubric calls out.

Usage (from the repository root):
    python agent/tools/checkup.py           # file and Git checks (a few seconds)
    python agent/tools/checkup.py --docker  # also rebuild images, rerun tests, recheck egress

Exit code 0 = no failures (warnings allowed), 1 = at least one failure.
Uses only the Python standard library.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Files and folders created for the course, as opposed to Netutils' own code.
COURSE_PATHS = ["setup.md", "Dockerfile.agent", ".gitattributes", "agent-smoke-test.md", "agent",
                "docs/prd.md", "docs/rubric.md", "docs/iteration-log.md",  # Module 1.3, Exercise 1
                "docs/lint-all-rules/prd.md", "docs/lint-all-rules/rubric.md",
                "docs/lint-all-rules/iteration-log.md"]  # Module 1 Lab
REQUIRED_FILES = [
    "Dockerfile.agent",
    "setup.md",
    "agent/docker-entrypoint.sh",
    "agent/settings.json",
    "agent/statusline.sh",
    "agent/proxy/Dockerfile",
    "agent/proxy/allowlist.txt",
    "agent/proxy/tinyproxy.conf",
    "agent/iteration-log.md",
]

# Signs of Windows 11 Notepad's Markdown mode escaping pasted Markdown (seen 2026-11-18).
MARKDOWN_DAMAGE = [
    (re.compile(r"^\\#"), r"heading escaped as \#"),
    (re.compile(r"\\\*\\\*"), r"bold escaped as \*\*"),
    (re.compile(r"^\\- "), r"list item escaped as \-"),
    (re.compile(r"&#x20;"), "HTML space entity &#x20;"),
]

SECRET_PATTERNS = [
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"), "Anthropic API key"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"), "GitHub token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r'"(accessToken|refreshToken)"\s*:'), "Claude login token"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s`\"]+"), "personal Windows path"),
]

results = []  # (status, check, detail)


def record(status, check, detail=""):
    results.append((status, check, detail))


def git(*args):
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout.strip()


def course_files():
    """All files under the course paths, skipping caches."""
    for name in COURSE_PATHS:
        path = ROOT / name
        if path.is_file():
            yield path
        elif path.is_dir():
            for file in path.rglob("*"):
                if file.is_file() and "__pycache__" not in file.parts:
                    yield file


def rel(path):
    return path.relative_to(ROOT).as_posix()


def check_required_files():
    missing = [f for f in REQUIRED_FILES if not (ROOT / f).is_file()]
    empty = [f for f in REQUIRED_FILES if (ROOT / f).is_file() and (ROOT / f).stat().st_size == 0]
    if missing:
        record("FAIL", "Required files present", "missing: " + ", ".join(missing))
    elif empty:
        record("FAIL", "Required files present", "empty: " + ", ".join(empty))
    else:
        record("PASS", "Required files present", f"{len(REQUIRED_FILES)} files")


def check_notepad_names():
    # Notepad adds .txt to new files with no extension, e.g. Dockerfile -> Dockerfile.txt.
    bad = [rel(f) for f in course_files()
           if re.search(r"(Dockerfile|\.md|\.sh|\.py|\.conf|\.json|\.yml)\.txt$", f.name, re.IGNORECASE)]
    if bad:
        record("FAIL", "No Notepad .txt misnames", ", ".join(bad))
    else:
        record("PASS", "No Notepad .txt misnames")


def check_markdown():
    problems = []
    for file in course_files():
        if file.suffix.lower() != ".md":
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            for pattern, label in MARKDOWN_DAMAGE:
                if pattern.search(line):
                    problems.append(f"{rel(file)}:{number} {label}")
                    break
        # Double-spaced files: Notepad's Markdown mode also inserted a blank line after every line.
        lines = text.splitlines()
        if len(lines) > 20 and all(not lines[i].strip() for i in range(1, min(len(lines), 41), 2)):
            problems.append(f"{rel(file)}: every other line is blank (double-spaced)")
    if problems:
        shown = problems[:8] + ([f"...and {len(problems) - 8} more"] if len(problems) > 8 else [])
        record("FAIL", "Markdown not damaged", "; ".join(shown))
    else:
        record("PASS", "Markdown not damaged")


def check_encoding():
    problems = []
    for file in course_files():
        data = file.read_bytes()
        if file.suffix in {".log"}:
            continue
        if data.startswith(b"\xef\xbb\xbf") and (file.suffix in {".sh", ".conf", ".txt"} or "Dockerfile" in file.name):
            problems.append(f"{rel(file)}: UTF-8 BOM (breaks Linux tools)")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel(file)}: not valid UTF-8")
    if problems:
        record("FAIL", "File encoding", "; ".join(problems))
    else:
        record("PASS", "File encoding")


def check_line_endings():
    # Shell scripts run inside Linux; Git must store them with LF (see .gitattributes).
    code, out = git("ls-files", "--eol", "--", "*.sh")
    bad = [line.split()[-1] for line in out.splitlines() if line and "i/lf" not in line.split()[0]]
    if code != 0:
        record("WARN", "Shell scripts stored with LF", "could not run git ls-files")
    elif bad:
        record("FAIL", "Shell scripts stored with LF", ", ".join(bad))
    else:
        record("PASS", "Shell scripts stored with LF")


def check_secrets():
    hits = []
    for file in course_files():
        if file.suffix == ".py" and file.name == "checkup.py":
            continue  # this file contains the patterns themselves
        text = file.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(line):
                    hits.append(f"{rel(file)}:{number} {label}")
    if hits:
        record("FAIL", "No secrets or personal paths", "; ".join(hits[:8]))
    else:
        record("PASS", "No secrets or personal paths")


def check_history_outside_repo():
    inside = [p for p in ("agent-history", "agent/agent-history") if (ROOT / p).exists()]
    code, out = git("ls-files", "--", "*.jsonl")
    if inside or out:
        record("FAIL", "Session transcripts kept out of the repo", ", ".join(inside + out.splitlines()))
    else:
        record("PASS", "Session transcripts kept out of the repo")


def check_git_state():
    code, out = git("status", "--porcelain")
    if code != 0:
        record("FAIL", "Git working tree", "not a Git repository?")
        return
    if out:
        changed = [line[2:].strip() for line in out.splitlines()]  # git() strips the first line's leading space
        record("WARN", "Everything committed", f"{len(changed)} uncommitted: " + ", ".join(changed[:6]))
    else:
        record("PASS", "Everything committed")
    code, out = git("rev-list", "--count", "@{u}..HEAD")
    if code != 0:
        record("WARN", "Commits pushed to GitHub", "branch has no upstream; run git push -u origin <branch>")
    elif out != "0":
        record("WARN", "Commits pushed to GitHub", f"{out} commit(s) not pushed; run git push")
    else:
        record("PASS", "Commits pushed to GitHub")


def check_iteration_log():
    code, out = git("log", "-1", "--format=%cs", "--", "agent/iteration-log.md")
    _, latest = git("log", "-1", "--format=%cs")
    if not out:
        record("WARN", "Iteration log updated", "agent/iteration-log.md has never been committed")
    elif out < latest:
        record("WARN", "Iteration log updated", f"last updated {out}, latest commit {latest}; add an entry?")
    else:
        record("PASS", "Iteration log updated", f"last updated {out}")


def run(cmd, timeout=900):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def check_docker():
    code, out = run(["docker", "build", "-q", "-f", "Dockerfile.agent", "-t", "netutils-agent", "."])
    record("PASS" if code == 0 else "FAIL", "Agent image builds", "" if code == 0 else out[-300:])
    code, out = run(["docker", "build", "-q", "-t", "egress-proxy", "agent/proxy"])
    record("PASS" if code == 0 else "FAIL", "Proxy image builds", "" if code == 0 else out[-300:])

    code, out = run(["docker", "inspect", "-f", "{{.State.Running}}", "egress-proxy"])
    if out != "true":
        record("FAIL", "Egress proxy running", "start it with: docker start egress-proxy")
        return
    record("PASS", "Egress proxy running")

    base = ["docker", "run", "--rm", "--network", "agent-net",
            "-e", "HTTPS_PROXY=http://egress-proxy:8888", "-e", "HTTP_PROXY=http://egress-proxy:8888",
            "-v", f"{ROOT}:/workspace", "--entrypoint", "bash", "netutils-agent", "-c"]
    code, out = run(base + ["curl -sS -m 10 -o /dev/null https://example.com; echo EXIT=$?"])
    blocked = "EXIT=0" not in out
    record("PASS" if blocked else "FAIL", "Egress blocked (example.com)", out.splitlines()[0] if out else "")
    code, out = run(base + ["curl -sS -m 10 -o /dev/null -w '%{http_code}' https://api.anthropic.com"])
    record("PASS" if code == 0 else "FAIL", "Anthropic API reachable", out[-80:])

    code, out = run(base + ["cd /workspace && PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider 2>&1 | tail -1"])
    summary = out.splitlines()[-1] if out else ""
    failed = re.search(r"(\d+) failed", summary)
    # The 4 DNS tests in tests/unit/test_dns.py fail by design inside the sandbox (no internet DNS).
    if failed and int(failed.group(1)) > 4:
        record("FAIL", "Unit tests (4 DNS failures expected)", summary)
    elif "passed" in summary:
        record("PASS", "Unit tests (4 DNS failures expected)", summary.strip("= "))
    else:
        record("FAIL", "Unit tests (4 DNS failures expected)", summary or "no pytest output")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--docker", action="store_true", help="also rebuild images and rerun tests and egress checks")
    args = parser.parse_args()

    check_required_files()
    check_notepad_names()
    check_markdown()
    check_encoding()
    check_line_endings()
    check_secrets()
    check_history_outside_repo()
    check_git_state()
    check_iteration_log()
    if args.docker:
        check_docker()

    width = max(len(check) for _, check, _ in results)
    for status, check, detail in results:
        print(f"[{status}] {check.ljust(width)}  {detail}".rstrip())
    fails = sum(1 for s, _, _ in results if s == "FAIL")
    warns = sum(1 for s, _, _ in results if s == "WARN")
    print(f"\n{len(results)} checks: {fails} failed, {warns} warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
