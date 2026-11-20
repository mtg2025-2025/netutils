# Lint report: `netutils/`

Date: 2026-11-20. All checks used the project config in `pyproject.toml`. Nothing was auto-fixed.

| Tool | Version | Command | Result |
|------|---------|---------|--------|
| ruff | 0.16.8 | `ruff check netutils/` | All checks passed (0 findings) |
| pylint | 4.0.8 | `pylint netutils` | 10.00/10 (0 messages) |
| mypy | 2.3.1 | `mypy netutils` | Success: no issues found in 35 source files |

Cache directories (`RUFF_CACHE_DIR`, `MYPY_CACHE_DIR`, `PYLINTHOME`) were sent to a temporary directory, so the runs created no `.ruff_cache` or `.mypy_cache` in the repo.

## Findings by tool and severity

None of the three tools reported anything under the current config:

- **ruff**: error 0, warning 0
- **pylint**: error (E/F) 0, warning (W) 0, refactor/convention (R/C) 0
- **mypy**: error 0

## Suppressed findings

The clean result depends partly on inline suppressions. `netutils/` has about 30 `# noqa`, about 40 `# pylint: disable`, and 24 `# type: ignore` comments. Most are harmless, such as `E203` slice spacing, magic-method docstrings in `interface.py` and the E3701 lines in `nist.py`. The ones below hide real risk.

| Tool / rule | Severity | Location | What it hides |
|---|---|---|---|
| pylint `undefined-loop-variable` | warning | `netutils/acl.py:521` | `ACLRules.match` returns `str(item.deny)` after the loop. If `self.rules` is empty, `item` is never bound and the method raises `UnboundLocalError` instead of returning the default deny. |
| pylint `undefined-loop-variable` | warning | `netutils/acl.py:455` | `existing_rule` is read after the inner loop. It is unbound if `self.expanded_rules` is empty, and it is the last rule tried, not the matching one, when nothing matched. |
| pylint `inconsistent-return-statements` | refactor | `netutils/acl.py:248` | `process_dst_port` mixes `return None` with falling off the end of the function. |
| ruff `S101` (assert) | security/low | `netutils/mac.py:19`, `netutils/interface.py:369`, `netutils/config/parser.py:1202` | Runtime checks use `assert`, which is removed under `python -O`. In `mac.py` the `_valid_mac` decorator's type check then disappears. |
| ruff `S311` (non-crypto RNG) | security/low | `netutils/password.py:296`, `:448`, `:454` | `random.randint` produces salts for Cisco type 7 and Juniper `$9$`. These are reversible obfuscation schemes anyway, so the impact is small, but the choice should be stated in a comment. |
| ruff `S701` (Jinja autoescape off) | security/info | `netutils/config/clean.py:193` | `SandboxedEnvironment(autoescape=False)`. The inline comment says this is intentional because config text must not be HTML-escaped. |
| mypy bare `type: ignore` | error (suppressed) | `netutils/config/parser.py:324-343, 1008, 1409-1421, 1581`; `netutils/config/compliance.py:209, 254, 373, 473`; `netutils/ip.py:278, 343` and others | 23 of the 24 ignores have no error code, so they hide every mypy error on those lines, including new ones. Only `parser.py:428` names a code (`[arg-type]`). |

## Top 5 issues worth fixing

1. **`netutils/acl.py:521`, `ACLRules.match` with no rules.** This is a real crash: `UnboundLocalError` when `self.rules` is empty. Set a default before the loop or handle the empty case explicitly.
2. **`netutils/acl.py:455`, stale or unbound `existing_rule` in `match_details`.** The detail output can report the wrong rule, or crash when there are no expanded rules.
3. **`netutils/mac.py:19`, `assert` used for input validation in `_valid_mac`.** Under `-O` the check disappears. Use `if not isinstance(mac, str): raise TypeError(...)`. The `interface.py:369` and `parser.py:1202` asserts are only hints for mypy and matter less.
4. **Bare `# type: ignore` comments, mostly in `netutils/config/parser.py` and `netutils/config/compliance.py`.** Give each one a specific error code, or remove it where it is no longer needed. Today they can hide new type errors without anyone noticing.
5. **`netutils/acl.py:248`, inconsistent returns in `process_dst_port`.** Make every path return explicitly so the `Union[List[str], None]` contract is visible and the suppression can go.

## Config notes (no changes made)

`pyproject.toml` globally ignores ruff `D401`, `D407`, `D416` and `E501`, with the comment "Produces a lot of issues in the current codebase", and pylint disables `line-too-long`. The pylint comment says Black enforces line length, but Black is not in the dev dependencies; ruff is. If you want to tighten these, that is a config change for you to decide on. I did not make it.
