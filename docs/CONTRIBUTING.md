# Contributing

Run the project test suite before submitting a change:

```bash
PYTHONPATH=src python -m pytest -q
```

Keep documentation aligned with `cli.parse_args()` and the implemented modules.
Do not document a high-level library API: the CLI is the supported interface.