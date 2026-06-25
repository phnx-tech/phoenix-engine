# Phoenix Engine Test Suite

This directory contains the automated test suite for Phoenix Engine. All tests
use mocked external dependencies; no live network calls are made.

## Organization

```
tests/
├── conftest.py           # Global fixtures, factories, and pytest config
├── README.md             # This file
├── fixtures/             # Static HTML fixtures and test data
├── unit/                 # Unit tests (isolated, fast)
├── integration/          # Integration tests (component interactions)
├── plugins/              # Plugin interface and loader tests
└── e2e/                  # End-to-end tests (CLI workflows)
```

## Test markers

| Marker | Description | Example command |
|--------|-------------|-----------------|
| `unit` | Fast, isolated unit tests | `pytest -m unit` |
| `integration` | Component integration tests | `pytest -m integration` |
| `e2e` | Full CLI/workflow tests | `pytest -m e2e` |
| `slow` | Tests that take longer than a few seconds | `pytest -m slow` |

## Running the tests

Activate the virtual environment first:

```bash
source .venv/bin/activate
```

Run the full suite:

```bash
pytest tests/
```

Run only unit tests:

```bash
pytest -m unit tests/unit/
```

Run integration tests:

```bash
pytest -m integration tests/integration/
```

> Note: marker-filtered runs still measure coverage over the whole `phoenix`
> package, so they may report lower coverage than the full suite. Use
> `pytest tests/` for authoritative coverage results.

Run with coverage (source path):

```bash
pytest --cov=src/phoenix --cov-report=term-missing tests/
```

## Fixtures and factories

Shared fixtures and `factory-boy` + `Faker` factories are defined in
`tests/conftest.py`. Available factory fixtures:

- `unified_output_factory` / `unified_output`
- `collection_result_factory` / `collection_result`
- `error_record_factory` / `error_record`
- `diagnostics_factory` / `diagnostics`

Additional shared fixtures include `mock_httpx_client`,
`mock_browser_context`, `sample_config`, and `event_loop_policy`.

## Adding tests

1. Place unit tests in `tests/unit/` and integration tests in
   `tests/integration/`.
2. Name files following the `test_*.py` convention.
3. Use the `unit`, `integration`, `e2e`, or `slow` markers as appropriate.
4. Use the shared fixtures from `tests/conftest.py` instead of building test
   data manually.
5. Mock all HTTP and browser interactions; never hit live sites from tests.
