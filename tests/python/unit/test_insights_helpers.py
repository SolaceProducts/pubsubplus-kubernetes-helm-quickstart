import pytest


@pytest.fixture
def base_values(cleanup_test_values):
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
            },
            "resources": {
                "requests": {"cpu": "200m", "memory": "256Mi"},
                "limits": {"cpu": "200m", "memory": "512Mi"},
            },
        }
    }


def test_insights_semp_port_with_tls(render_helm_template, base_values):
    tls_values = base_values.copy()
    tls_values.update(
        {"tls": {"enabled": True, "serverCertificatesSecret": "test-cert"}}
    )
    resources = render_helm_template(tls_values)

    env_secret = next(
        (
            r
            for r in resources
            if r["kind"] == "Secret"
            and "insights-agent-env-secrets" in r["metadata"]["name"]
        ),
        None,
    )
    assert env_secret is not None

    assert env_secret["stringData"]["INSIGHTS_AGENT_SEMP_PORT"] == "1943"
    assert env_secret["stringData"]["INSIGHTS_AGENT_SEMP_PROTOCOL"] == "https"


def test_insights_semp_port_without_tls(render_helm_template, base_values):
    resources = render_helm_template(base_values)

    env_secret = next(
        (
            r
            for r in resources
            if r["kind"] == "Secret"
            and "insights-agent-env-secrets" in r["metadata"]["name"]
        ),
        None,
    )
    assert env_secret is not None

    assert env_secret["stringData"]["INSIGHTS_AGENT_SEMP_PORT"] == "8080"
    assert env_secret["stringData"]["INSIGHTS_AGENT_SEMP_PROTOCOL"] == "http"


def test_insights_password_generation(render_helm_template, base_values):
    resources = render_helm_template(base_values)

    password_secret = next(
        (
            r
            for r in resources
            if r["kind"] == "Secret"
            and "insights-secrets" in r["metadata"]["name"]
            and not "env" in r["metadata"]["name"]
        ),
        None,
    )

    assert password_secret is not None
    assert "username_insights_password" in password_secret["data"]

    assert password_secret["data"]["username_insights_password"] != ""

    env_secret = next(
        (
            r
            for r in resources
            if r["kind"] == "Secret"
            and "insights-agent-env-secrets" in r["metadata"]["name"]
        ),
        None,
    )
    assert env_secret is not None
    assert "INSIGHTS_AGENT_SEMP_PASSWORD" in env_secret["stringData"]


def test_missing_image_configuration(render_helm_template):
    incomplete_values = {
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_API_KEY": "test-api-key",
                "INSIGHTS_AGENT_SITE": "us-east",
                "INSIGHTS_AGENT_TAGS": "dev,test",
            },
            "resources": {
                "requests": {"cpu": "200m", "memory": "256Mi"},
                "limits": {"cpu": "200m", "memory": "512Mi"},
            },
        }
    }

    resources = render_helm_template(incomplete_values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    stateful_set = stateful_sets[0]
    containers = stateful_set["spec"]["template"]["spec"]["containers"]

    insights_containers = [c for c in containers if c["name"] == "insights-agent"]
    assert len(insights_containers) == 1

    assert "image" in insights_containers[0]


def test_missing_resources_configuration(render_helm_template):
    incomplete_values = {
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
            },
        }
    }

    resources = render_helm_template(incomplete_values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    stateful_set = stateful_sets[0]
    containers = stateful_set["spec"]["template"]["spec"]["containers"]

    insights_containers = [c for c in containers if c["name"] == "insights-agent"]
    assert len(insights_containers) == 1

    assert "resources" in insights_containers[0]


def test_solace_config_map_insights_integration(render_helm_template, base_values):
    resources = render_helm_template(base_values)

    config_maps = [r for r in resources if r["kind"] == "ConfigMap"]
    assert len(config_maps) > 0

    insights_config_found = False
    for config_map in config_maps:
        for key, value in config_map["data"].items():
            if "username_insights_passwordfilepath" in value:
                insights_config_found = True
                break

    assert insights_config_found


def test_solace_config_map_without_insights(render_helm_template):
    disabled_values = {"insights": {"enabled": False}}
    resources = render_helm_template(disabled_values)

    config_maps = [r for r in resources if r["kind"] == "ConfigMap"]
    assert len(config_maps) > 0

    insights_config_found = False
    for config_map in config_maps:
        for key, value in config_map["data"].items():
            if "username_insights_passwordfilepath" in value:
                insights_config_found = True
                break

    assert not insights_config_found
