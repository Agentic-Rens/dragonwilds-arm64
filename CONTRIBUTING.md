# Contributing

This is a small experimental project. Clear bug reports and honest compatibility
results are just as useful as code changes.

## Reporting a problem

Include:

- Your board model, RAM, OS, and whether you are using stock clocks.
- The repository revision and game build, if known.
- What you tried, what you expected, and what happened.
- A short, relevant log excerpt and any runtime flags you changed.

Before posting logs, remove passwords, EOS owner IDs, session tokens, addresses,
and personal paths. The game can log the join password even when the setup
helper does not print it. Do not attach `.env` files or world backups.

For performance reports, include player count and how long you tested. Reaching
`ReadyToJoin` is useful evidence, but is different from a playable session.

## Working on the code

Keep changes focused and explain why they are needed. The project deliberately
uses Jagex's launcher where possible; changes to its patch should fail clearly
if upstream structure changes.

Local checks, without Docker or a running server:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile patch-upstream.py scripts/*.py
bash -n entrypoint.sh
for script in scripts/*.sh; do sh -n "$script"; done
git diff --check
```

For runtime changes, also build and run preflight on an ARM64 Linux machine.
Use a disposable world for startup/restart tests. Never run the download or
boot-test helpers against a volume that an active server is using.

Update `VALIDATION.md` with reproducible, anonymized observations. Please avoid
turning one successful boot into a broad compatibility claim.

Contributions to the original code and documentation are made under the MIT
license in `LICENSE`. Keep third-party notices intact.
