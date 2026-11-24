# Ruff lint report: all rules (`--select ALL`)

Ruff version: 0.16.8 (`/usr/local/bin/ruff`). Run from `/workspace` on 2026-11-24.

## Commands run

```
ruff check netutils --select ALL --no-cache --statistics
ruff check netutils --select ALL --no-cache --output-format concise
```

Both commands ran on the first try. Each exited with code 1, which is ruff's normal exit code when it finds problems. Nothing was written to stderr. No `--fix` or `--unsafe-fixes` was used, and no `.ruff_cache` folder was created.

## Summary

- **Total findings:** 1106 (from `Found 1106 errors.`, the same in both runs; the 1106 lines in the concise output and the sum of the statistics counts both match it)
- **Fixable:** 393 (from `[*] 393 fixable with the `--fix` option (179 hidden fixes can be enabled with the `--unsafe-fixes` option).`)

## Top 10 rules by count (from `--statistics`)

| # | Code | Name | Count |
|---|------|------|------:|
| 1 | UP006 | non-pep585-annotation | 242 |
| 2 | TRY003 | raise-vanilla-args | 95 |
| 3 | E501 | line-too-long | 85 |
| 4 | EM101 | raw-string-in-exception | 59 |
| 5 | EM102 | f-string-in-exception | 48 |
| 5 | RUF012 | mutable-class-default | 48 |
| 7 | UP045 | non-pep604-annotation-optional | 38 |
| 8 | ANN401 | any-type | 35 |
| 8 | CPY001 | missing-copyright-notice | 35 |
| 8 | EXE002 | shebang-missing-executable-file | 35 |

Ranks 8 to 10 are a three-way tie at 35. All three fit inside the top 10. The next rule, PLW2901 (redefined-loop-name), has 33, so no tied entries had to be added.

## Top 10 files by findings (counted from the concise output)

| # | File | Findings |
|---|------|---------:|
| 1 | netutils/config/parser.py | 286 |
| 2 | netutils/interface.py | 115 |
| 3 | netutils/acl.py | 80 |
| 4 | netutils/ip.py | 74 |
| 5 | netutils/password.py | 57 |
| 6 | netutils/bandwidth.py | 51 |
| 6 | netutils/_private/version.py | 51 |
| 8 | netutils/config/conversion.py | 49 |
| 8 | netutils/config/compliance.py | 49 |
| 10 | netutils/lib_mapper.py | 47 |

There is no tie at 10th place. The next file, netutils/os_version.py, has 30.

## Findings that look like real bugs (no files were edited)

1. **`netutils/config/compliance.py:371`: PLE0704 misplaced-bare-raise.** Inside `_check_configs`, the `else:` branch after `if feature["ordered"] is True: ... elif feature["ordered"] is False: ...` contains a bare `raise`. This is not inside an `except` block, so there is no active exception to re-raise. If `feature["ordered"]` is anything other than the booleans `True` or `False` (for example missing as `None`, or a truthy string like `"true"`), Python raises `RuntimeError: No active exception to reraise` instead of a useful error. The code silences this with a `# pylint: disable=misplaced-bare-raise` comment, which suggests it was noticed but never fixed. A proper fix would raise an explicit exception, such as `ValueError`, with a message about the invalid `ordered` value.

2. **`netutils/_private/version.py:36`: PLW1641 eq-without-hash (minor).** `Version` defines `__eq__` but not `__hash__`, so its instances, including `LooseVersion`, can't be hashed (they can't be used in sets or as dict keys). This code is copied from the old `distutils.version`, which behaves the same way, so it is probably known and accepted rather than a regression.

3. **`netutils/_private/version.py:343`: RET503 implicit-return (minor).** `LooseVersion._cmp` returns 0, -1 or 1 from three `if` checks and otherwise falls through to `None`. For comparable lists this can't happen, so it is a style issue rather than a live bug. It is listed here only because it was checked.

Other findings that might have pointed to bugs were checked and look correct as written:

- `B034`, `netutils/regex.py:132,158`: `re.split(pattern, string, maxsplit)` and `re.sub(pattern, repl, string, count)` pass the arguments in the right positions.
- `RUF021`, `netutils/config/parser.py:388`: the precedence of `a and b or c` matches the intent, "parent matches OR line matches".
- `ISC001`, `netutils/constants.py:417`: the implicit string concatenation is deliberate and marked with a pylint disable comment.
