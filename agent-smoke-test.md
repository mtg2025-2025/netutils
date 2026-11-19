# Unit Test Smoke Test — netutils

- **Date:** 2026-11-19
- **Branch:** agent-sandbox
- **Python:** 3.12.16
- **Command:**
  ```
  PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider \
    -o addopts="--doctest-modules -p no:warnings --ignore-glob=*mock*"
  ```
  This uses the project's configured `addopts` from `pyproject.toml`, minus `-vv`. The cache provider and bytecode writing were disabled so the run wouldn't write any files into the repo.

## Result: FAIL (environment-related)

| Outcome | Count |
|---------|-------|
| Passed  | 836   |
| Failed  | 4     |
| Errors  | 0     |
| Skipped | 2     |

Run time: about 4.2 s. Exit code: 1.

## Failed tests

All 4 failures are in `tests/unit/test_dns.py`. They need live DNS resolution, and this sandbox has none. For example, `getent hosts google.com` returns exit code 2.

| Test | Error |
|------|-------|
| `test_is_fqdn_resolvable[data0]` (google.com) | `assert False == True` |
| `test_is_fqdn_resolvable[data1]` (yahoo.com) | `assert False == True` |
| `test_fqdn_to_ip[data0]` (google.com) | `socket.gaierror: [Errno -3] Temporary failure in name resolution` |
| `test_fqdn_to_ip[data1]` (yahoo.com) | `socket.gaierror: [Errno -3] Temporary failure in name resolution` |

These are failures caused by the network, not by the code. The DNS tests that expect resolution to fail (`nevergonnagiveyouup.pizza`, `test_bad_hostname`) pass. These tests should pass on a host that has working DNS.

Note: an earlier run on the same day recorded 840 passed and 0 failed, so DNS was available then. The difference comes from the sandbox's network access, not from any code change.

## Skipped tests

Both skips are in `tests/unit/test_lib_helpers_optionals.py` (lines 11 and 18):

> could not import 'napalm': No module named 'pkg_resources'

`napalm` is an optional dependency. It is installed, but it fails to import because `pkg_resources` (from setuptools) isn't in the environment. This is a gap in the environment. Nothing was installed to fix it, as instructed.

## Collection warnings (harmless)

pytest warned that it couldn't collect the helper classes `TestMatrix`, `TestSchema`, `TestSchema2` and `TestAddrGroups` in `tests/unit/test_acl.py`. They subclass `acl.ACLRule` and have `__init__` constructors. They are test fixtures, not test cases.

## Notes

- Only `tests/unit` was run. `tests/integration` was not run.
- Working tree before the run: only the untracked files `Dockerfile.agent`, `agent-smoke-test.md`, `agent/` and `setup.md`. No tracked files were modified. This file is the only one written.
