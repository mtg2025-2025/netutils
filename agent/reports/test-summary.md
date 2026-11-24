# Unit test report: `tests/unit`

Date: 2026-11-24. Python 3.12.16, pytest 9.1.1, run from `/workspace`. The project config in `pyproject.toml` adds `addopts = "-vv --doctest-modules -p no:warnings --ignore-glob='*mock*'"`.

## Command

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit -p no:cacheprovider
```

`PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` stop the run from writing `__pycache__/` or `.pytest_cache/` into the repo. They don't change which tests run. Exit status: tests failed.

## Final summary line

```
============= 4 failed, 880 passed, 2 skipped, 6 xfailed in 8.65s ==============
```

| Outcome | Count |
|---|---|
| Failed | 4 |
| Passed | 880 |
| Skipped | 2 |
| xfailed | 6 |
| Errors | 0 (none reported) |

## Failed tests

| Test ID | Cause (from traceback) | Category |
|---|---|---|
| `tests/unit/test_dns.py::test_is_fqdn_resolvable[data0]` | `dns.is_fqdn_resolvable("google.com")` returned `False`, but the test expected `True` (`AssertionError: assert False == True` at `tests/unit/test_dns.py:23`). The function catches the resolver error and returns `False`. | Environment |
| `tests/unit/test_dns.py::test_is_fqdn_resolvable[data1]` | Same as above, for `"yahoo.com"`. | Environment |
| `tests/unit/test_dns.py::test_fqdn_to_ip[data0]` | `dns.fqdn_to_ip("google.com")` raised `socket.gaierror: [Errno -3] Temporary failure in name resolution`. The error came from `socket.getaddrinfo` (`netutils/dns.py:29` → `/usr/local/lib/python3.12/socket.py:978`). | Environment |
| `tests/unit/test_dns.py::test_fqdn_to_ip[data1]` | Same `socket.gaierror`, for `"yahoo.com"`. | Environment |

### Why these are environment issues

All four tests look up real public DNS names, and this sandbox can't resolve names. `/etc/resolv.conf` points at the Docker internal resolver `127.0.0.11`. I ran `socket.getaddrinfo("google.com", 0)` on its own, outside pytest, and it raised the same `gaierror: [Errno -3] Temporary failure in name resolution`.

`netutils/dns.py` does what its docstrings say:
- `fqdn_to_ip` raises `socket.gaierror` when a name can't be resolved.
- `is_fqdn_resolvable` returns `False` when a name can't be resolved.

The tests in the same file that don't need a successful lookup passed. These are `test_is_fqdn_resolvable[data2]`, which expects `False` for `nevergonnagiveyouup.pizza`, and `test_bad_hostname`. None of the failures points to a code defect.

These tests need the network. They should pass on a machine with working DNS. They could also be mocked, or marked to skip when the machine is offline.

## Skipped and xfailed (not failures, for context)

I got these reasons from a second, read-only run of the same command with `-rsx -q` added.

- **2 skipped:** `tests/unit/test_lib_helpers_optionals.py:11` and `:18`. The reason given is "could not import 'napalm': No module named 'pkg_resources'". This is an environment issue: an optional dependency is unavailable because `setuptools`/`pkg_resources` is missing. I didn't install anything.
- **6 xfailed** in `tests/unit/test_vlan.py`. These are tests marked as expected failures for known VLAN bugs:
  - `test_to_config_out_of_range_grouping_size_one[vlan_list0]` and `[vlan_list1]`: with `min_grouping_size=1`, the function returns before the 1–4094 range check.
  - `test_to_list_below_min`: there's no lower-bound check, so VLAN 0 is accepted.
  - `test_to_list_empty_string`: an empty string raises `IndexError` instead of `ValueError`.
  - `test_to_config_short_group_not_truncated[vlan_list0-4-expected0]` and `[vlan_list1-5-expected1]`: a run of 3 or more VLANs that is shorter than `min_grouping_size` keeps only its first two VLANs.

  These are real code defects that the test suite already records. They aren't failures in this run.
