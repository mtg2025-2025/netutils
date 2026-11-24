# Unit Test Summary

**Date:** 2026-11-24
**Environment:** Python 3.12.16, pytest 9.1.1, Linux; working directory `/workspace`

## Command

```
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider
```

## Result

Final summary line from pytest:

```
============= 4 failed, 880 passed, 2 skipped, 6 xfailed in 5.49s ==============
```

| Outcome | Count |
|---|---|
| Failed | 4 |
| Passed | 880 |
| Skipped | 2 |
| xfailed | 6 |
| Errors | 0 |

## Failed tests

All four failures are in `tests/unit/test_dns.py`. All of them need live DNS resolution of public hostnames.

| # | Test ID | Cause (from traceback) | Classification |
|---|---|---|---|
| 1 | `tests/unit/test_dns.py::test_is_fqdn_resolvable[data0]` | `AssertionError: assert False == True`. `dns.is_fqdn_resolvable('google.com')` returned `False` because the name could not be resolved. | Environment issue |
| 2 | `tests/unit/test_dns.py::test_is_fqdn_resolvable[data1]` | `AssertionError: assert False == True`. `dns.is_fqdn_resolvable('yahoo.com')` returned `False` because the name could not be resolved. | Environment issue |
| 3 | `tests/unit/test_dns.py::test_fqdn_to_ip[data0]` | `socket.gaierror: [Errno -3] Temporary failure in name resolution`, raised from `socket.getaddrinfo('google.com', 0)` at `netutils/dns.py:29` (`fqdn_to_ip`). | Environment issue |
| 4 | `tests/unit/test_dns.py::test_fqdn_to_ip[data1]` | `socket.gaierror: [Errno -3] Temporary failure in name resolution`, raised from `socket.getaddrinfo('yahoo.com', 0)` at `netutils/dns.py:29` (`fqdn_to_ip`). | Environment issue |

### Why these are environment issues, not code defects

- `fqdn_to_ip` is a thin wrapper around `socket.getaddrinfo`, and `is_fqdn_resolvable` returns `False` when `socket.gaierror` is raised. Both behave as documented. The docstrings say a valid FQDN may not resolve "such as a network error from your machine to the DNS server".
- A separate check in the same environment showed `socket.getaddrinfo('localhost', 0)` working (it returned `::1`). `socket.getaddrinfo('google.com', 0)` failed with the same `[Errno -3] Temporary failure in name resolution`. `/etc/resolv.conf` points to `127.0.0.11`, the Docker embedded resolver, so external DNS is not reachable from this sandbox.
- These tests depend on outside network access. They should pass on a host where DNS works. One possible improvement is to mark them as network tests or mock `socket.getaddrinfo`, but that is a test-design choice, not a library bug.

## Skipped tests (not failures, for reference)

- `tests/unit/test_lib_helpers_optionals.py::test_get_napalm_getters_napalm_installed_default`
- `tests/unit/test_lib_helpers_optionals.py::test_get_napalm_getters_napalm_installed_nxos_keys`

Both skip through `pytest.importorskip("napalm")`, because the optional `napalm` package is not installed. This is an environment condition.

## Expected failures (xfail, for reference)

There were 6 xfailed tests in `tests/unit/test_vlan.py`. Each is marked as a known bug, so none counts as a failure:

- `test_to_config_out_of_range_grouping_size_one[vlan_list0]`, `[vlan_list1]`: invalid VLAN IDs are accepted when grouping size is 1.
- `test_to_list_below_min`: there is no lower-bound check, so VLAN 0 is accepted.
- `test_to_list_empty_string`: an empty string raises `IndexError` instead of `ValueError`.
- `test_to_config_short_group_not_truncated[vlan_list0-4-expected0]`, `[vlan_list1-5-expected1]`: a short group keeps only its first two VLANs.

These are code defects already known to the project, and the tests track them as xfail. They are not new regressions.

## Other notes

- Collection showed `PytestCollectionWarning`s for helper classes in `tests/unit/test_acl.py` (`TestMatrix`, `TestSchema`, `TestSchema2`, `TestAddrGroups`). They have `__init__` constructors, so pytest does not collect them. These warnings are harmless.
- No files other than this report were modified. Nothing was installed, committed or pushed.
