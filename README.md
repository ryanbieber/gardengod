# GardenGod

This is AI SLOP but I want to plan my garden and this seems like a nice way to do it.

## Overview

GardenGod is designed to help manage garden data efficiently. It leverages modern Python tooling and libraries to ensure performance and type safety.

## Features

- **High-Performance Data Handling:** Utilizes `polars` for fast data manipulation.
- **Modern Tooling:** Managed with `uv` for fast, reliable dependency management.
- **Strict Typing:** Fully typed codebase compliant with strict `mypy` standards.
- **Robust Error Handling:** Adheres to a "fail hard and fast" philosophy to ensure data integrity.

## Prerequisites

- Python 3.10+
- `uv` package manager

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/carnufex/gardengod.git
    cd gardengod
    ```

2.  **Set up the environment:**

    ```bash
    uv venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    uv sync
    ```

3.  **Install pre-commit hooks:**

    ```bash
    uv run pre-commit install
    ```

## Usage

Run the application using `uv`:

```bash
uv run python -m gardengod.main
```

## Development

### Running Tests

We use `pytest` for testing. Ensure all tests pass before submitting changes.

```bash
uv run pytest
```

### Linting and Formatting

Code quality is enforced using `ruff`.

```bash
uv run pre-commit run --all-files
```

## Project Structure

- `gardengod/`: Main application source code.
- `tests/`: Unit and functional tests.
- `pyproject.toml`: Project configuration and dependencies.

## License

[MIT License](LICENSE)