# Developer Guide

This document will explain how to contribute to the edit-python.pe project.

## How to Contribute

1. Make sure to find an open issue on [GitHub](https://github.com/python.pe/edit-python.pe/issues).
1. Fork the [edit-python.pe](https://github.com/python.pe/edit-python.pe) repository.
1. Clone the forked repository to your local machine.
1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
1. Install dependencies:

```bash
uv sync
```

1. Install pre-commit hook:

```bash
uv run pre-commit install
```

1. Make your changes.
1. Cover your changes with tests.
1. Run the test coverage:

```bash
uv run poe test
```

1. Run the auto-translations:

```bash
uv run poe makemessages
```

1. Commit your changes, if the pre-commit hook fails, run `uv run poe test` to
   know which test failed.
1. If the last step was your last commit on this issue, run this command:

```bash
uv run poe version:update NEW_VERSION
```

1. Push your changes to the forked repository.
1. Open a pull request on [GitHub](https://github.com/python.pe/edit-python.pe/pulls).
