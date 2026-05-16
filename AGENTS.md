# AGENTS.md

Rules for future Codex sessions working on Angis:

- Keep Angis offline and local. Do not add cloud AI API dependencies for parsing.
- Do not use `eval()` or `exec()` for language execution.
- Do not add shell execution features to Angis programs.
- Keep phrase support centralized in `angis/intents.py`.
- New phrase patterns should be covered by parser tests and interpreter tests when they affect runtime behavior.
- Preserve helpful, safe error messages. Do not leak host paths unless the user explicitly provides them.
- Keep the CLI contract working: `python -m angis run examples/hello.angis`.
- Keep the IDE limited to `.angis` files and validate paths before reading or writing.
- Prefer simple standard-library Python unless a dependency is clearly justified.
- Run `python -m pytest` before reporting completion.
