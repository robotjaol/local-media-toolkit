# Contributing

Thank you for improving Local Media Toolkit.

## Principles

Contributions should preserve four properties:

1. Local-first processing.
2. No telemetry or hidden network calls.
3. Explicit and inspectable FFmpeg commands.
4. Cross-platform behavior where practical.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
ruff check .
```

## Pull requests

Keep changes scoped. Include tests for parsers and command construction. For codec behavior, document the FFmpeg build and operating system used for validation.

Never commit private media. Synthetic test media can be generated with FFmpeg `lavfi`; see `scripts/smoke_test.py`.
