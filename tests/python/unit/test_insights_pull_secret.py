import pytest


@pytest.fixture
def base_values(cleanup_test_values):
    """Base values fixture with insights enabled"""
    return {
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_API_KEY": "test-api-key",
                "INSIGHTS_AGENT_SITE": "us-east",
                "INSIGHTS_AGENT_TAGS": "dev,test",
            },
            "image": {
                "repository": "gcr.io/gcp-maas-prod/solace-insights-agent",
                "tag": "latest",
                "pullSecretName": "insights-pull-secret",
            },
            "resources": {
                "requests": {"cpu": "200m", "memory": "256Mi"},
                "limits": {"cpu": "200m", "memory": "512Mi"},
            },
        }
    }


def test_both_pull_secrets_defined(render_helm_template, base_values):
    """Test that both pull secrets are included when both are defined"""
    values = base_values.copy()
    values["image"] = {"pullSecretName": "main-pull-secret"}

    resources = render_helm_template(values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    pull_secrets = stateful_sets[0]["spec"]["template"]["spec"]["imagePullSecrets"]
    assert len(pull_secrets) == 2
    assert {"name": "main-pull-secret"} in pull_secrets
    assert {"name": "insights-pull-secret"} in pull_secrets


def test_only_insights_pull_secret(render_helm_template, base_values):
    """Test that only insights pull secret is included when only it is defined"""
    resources = render_helm_template(base_values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    pull_secrets = stateful_sets[0]["spec"]["template"]["spec"]["imagePullSecrets"]
    assert len(pull_secrets) == 1
    assert {"name": "insights-pull-secret"} in pull_secrets


def test_only_main_pull_secret(render_helm_template, cleanup_test_values):
    """Test that only main pull secret is included when insights pull secret is explicitly set to null"""
    values = {
        "image": {"pullSecretName": "main-pull-secret"},
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_API_KEY": "test-api-key",
                "INSIGHTS_AGENT_SITE": "us-east",
                "INSIGHTS_AGENT_TAGS": "dev,test",
            },
            "image": {
                "repository": "gcr.io/gcp-maas-prod/solace-insights-agent",
                "tag": "latest",
                "pullSecretName": None,
            },
        },
    }

    resources = render_helm_template(values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    pull_secrets = stateful_sets[0]["spec"]["template"]["spec"]["imagePullSecrets"]
    assert len(pull_secrets) == 1
    assert {"name": "main-pull-secret"} in pull_secrets


def test_no_pull_secrets(render_helm_template, cleanup_test_values):
    """Test that no pull secrets are included when neither is defined"""
    values = {
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_API_KEY": "test-api-key",
                "INSIGHTS_AGENT_SITE": "us-east",
                "INSIGHTS_AGENT_TAGS": "dev,test",
            },
            "image": {
                "repository": "gcr.io/gcp-maas-prod/solace-insights-agent",
                "tag": "latest",
                "pullSecretName": None,
            },
        }
    }

    resources = render_helm_template(values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    spec = stateful_sets[0]["spec"]["template"]["spec"]
    assert spec["imagePullSecrets"] is None


def test_insights_disabled_with_pull_secret(render_helm_template, cleanup_test_values):
    """Test that insights pull secret is not included when insights is disabled"""
    values = {
        "insights": {
            "enabled": False,
            "image": {"pullSecretName": "insights-pull-secret"},
        },
        "image": {"pullSecretName": "main-pull-secret"},
    }

    resources = render_helm_template(values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    pull_secrets = stateful_sets[0]["spec"]["template"]["spec"]["imagePullSecrets"]
    assert len(pull_secrets) == 1
    assert {"name": "main-pull-secret"} in pull_secrets
