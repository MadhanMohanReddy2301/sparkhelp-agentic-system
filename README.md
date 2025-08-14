# Project Setup and Development Guide

This document provides instructions on how to set up the development environment for this project, run tests, and build distributable packages.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8+
- `pip` (Python package installer)
- `venv` (for creating virtual environments)

## Setup Instructions

1.  **Clone the repository (if you haven't already):**

    ```bash
    git clone <your-repository-url>
    cd AgenticAI-Base-Code
    ```

2.  **Create and activate a virtual environment:**

    It is highly recommended to work within a virtual environment to manage project dependencies.

    *   On macOS and Linux:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

    *   On Windows:
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```

3.  **Install dependencies:**

    Install the project in editable mode along with its testing dependencies.

    ```bash
    pip install -e .[test]
    ```

## Running Tests

This project uses `pytest` for running tests. To execute the entire test suite, run the following command from the project root:

```bash
pytest
```

## Building the Project

To create a source distribution (`sdist`) and a wheel, you can use the `build` package.

1.  **Install `build` (if you haven't already):**
    ```bash
    pip install build
    ```

2.  **Build the packages:**
    ```bash
    python -m build
    ```

The distributable files will be created in the `dist/` directory.
