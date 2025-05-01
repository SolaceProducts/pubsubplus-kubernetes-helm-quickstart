# PubSub+ Kubernetes Helm Chart Tests

This directory contains tests for the PubSub+ Kubernetes Helm quickstart charts.

## Helm Template Tests

The `python/` directory contains unit tests that validate the Helm templates without requiring an actual Kubernetes cluster. These tests focus on verifying that the templates render correctly with various configurations.

### Prerequisites

- Python 3.13
- Helm v3

### Installation

```bash
cd tests/python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Tests

From the `tests/python` directory:

```bash
pytest
```
