import os
import pytest
import yaml
import subprocess


@pytest.fixture(scope="session")
def helm_executable():
    """Path to the Helm executable."""
    return "helm"


@pytest.fixture(scope="session")
def base_chart_dir():
    """Base directory for all helm charts."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "..",
    )


@pytest.fixture(scope="function")
def cleanup_test_values():
    """Cleanup test values file after test."""
    yield
    test_values_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_values.yaml"
    )
    if os.path.exists(test_values_file):
        os.remove(test_values_file)


@pytest.fixture
def render_helm_template(helm_executable, base_chart_dir, cleanup_test_values):
    def _render_template(values, release_name="test-release", namespace="default"):
        chart_path = os.path.join(base_chart_dir, "pubsubplus")
        values_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_values.yaml"
        )

        with open(values_file, "w") as f:
            yaml.dump(values, f)

        cmd = [
            helm_executable,
            "template",
            release_name,
            chart_path,
            "--namespace",
            namespace,
            "-f",
            str(values_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Helm template rendering failed: {result.stderr}")

        resources = []
        for doc in yaml.safe_load_all(result.stdout):
            if doc:
                resources.append(doc)

        return resources

    return _render_template
