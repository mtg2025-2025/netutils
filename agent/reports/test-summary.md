# Unit test report: `tests/unit`

Date: 2026-11-23. Python 3.12.16, pytest 9.1.1, run from `/workspace` with the project config in `pyproject.toml` (`addopts = "-vv --doctest-modules -p no:warnings --ignore-glob='*mock*'"`).

## Command

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider
```

`PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` stop the run from writing `__pycache__/` or `.pytest_cache/` into the repo. They do not change which tests run or how they behave. Exit code: 1.

## Final summary line

```
============= 4 failed, 880 passed, 2 skipped, 6 xfailed in 6.64s ==============
```

| Outcome | Count |
|---|---|
| Failed | 4 |
| Passed | 880 |
| Skipped | 2 |
| xfailed | 6 |
| Errors | 0 |

## Failed tests

| Test ID | Cause (from traceback) | Category |
|---|---|---|
| `tests/unit/test_dns.py::test_is_fqdn_resolvable[data0]` | `dns.is_fqdn_resolvable("google.com")` returned `False`, expected `True` (`AssertionError: assert False == True`, `tests/unit/test_dns.py:23`). The function catches the resolver error and returns `False`. | Environment |
| `tests/unit/test_dns.py::test_is_fqdn_resolvable[data1]` | Same as above for `"yahoo.com"`. | Environment |
| `tests/unit/test_dns.py::test_fqdn_to_ip[data0]` | `dns.fqdn_to_ip("google.com")` raised `socket.gaierror: [Errno -3] Temporary failure in name resolution` from `socket.getaddrinfo` (`netutils/dns.py:29` → `/usr/local/lib/python3.12/socket.py:978`). | Environment |
| `tests/unit/test_dns.py::test_fqdn_to_ip[data1]` | Same `socket.gaierror` for `"yahoo.com"`. | Environment |

### Why these are environment issues

All four tests do real DNS lookups of public names. This sandbox cannot resolve names: it uses the container resolver `127.0.0.11`, and a separate `socket.getaddrinfo("google.com", 0)` call outside pytest raised the same `gaierror(-3, 'Temporary failure in name resolution')`. `netutils/dns.py` does what its docstring says: `fqdn_to_ip` raises `socket.gaierror` when a name can't be resolved, and `is_fqdn_resolvable` returns `False`. The negative tests in the same file (`nevergonnagiveyouup.pizza` → `False`, and `test_bad_hostname`) passed. No failure points to a code defect.

These tests depend on the network. They should pass on a machine with working DNS, or they could be mocked or marked so they are skipped when offline.

## Skipped and xfailed (not failures, listed for completeness)

- **Skipped (2):** `tests/unit/test_lib_helpers_optionals.py::test_get_napalm_getters_napalm_installed_default` and `::test_get_napalm_getters_napalm_installed_nxos_keys`. Both call `pytest.importorskip("napalm")`. In this environment `import napalm` fails with `ModuleNotFoundError: No module named 'pkg_resources'`, so the optional napalm tests are skipped. This is an environment issue (missing or broken optional dependency).
- **xfailed (6):** all in `tests/unit/test_vlan.py`. They are marked as known bugs in `netutils/vlan.py` (2× `min_grouping_size=1` skips the 1–4094 range check; VLAN 0 accepted because there is no lower-bound check; an empty string raises `IndexError` instead of `ValueError`; 2× a run of 3+ consecutive VLANs shorter than `min_grouping_size` keeps only its first two VLANs). They failed as expected. They are known code defects tracked by the test suite, not new findings from this run.

## Other notes

- Collection emitted two `PytestCollectionWarning`s for `TestMatrix` and `TestSchema` in `tests/unit/test_acl.py`. These are helper subclasses of `acl.ACLRule` with an `__init__`, not test classes. The warnings are harmless.
- No source, test, or config files were modified, and nothing was installed or committed. The only file written is this report.
