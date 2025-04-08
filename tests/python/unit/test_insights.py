import pytest


@pytest.fixture
def test_values(cleanup_test_values):
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


def test_insights_secret_created_when_enabled(render_helm_template, test_values):
    resources = render_helm_template(test_values)

    password_secret = next(
        (
            s
            for s in resources
            if s["kind"] == "Secret"
            and "insights-secrets" in s["metadata"]["name"]
            and not "env" in s["metadata"]["name"]
        ),
        None,
    )
    env_secret = next(
        (
            s
            for s in resources
            if s["kind"] == "Secret"
            and "insights-agent-env-secrets" in s["metadata"]["name"]
        ),
        None,
    )

    assert password_secret is not None
    assert env_secret is not None

    assert "username_insights_password" in password_secret["data"]

    assert "INSIGHTS_AGENT_API_KEY" in env_secret["data"]
    assert "INSIGHTS_AGENT_SITE" in env_secret["data"]
    assert "INSIGHTS_AGENT_TAGS" in env_secret["data"]


def test_insights_container_added_to_pod(render_helm_template, test_values):
    resources = render_helm_template(test_values)

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    stateful_set = stateful_sets[0]
    containers = stateful_set["spec"]["template"]["spec"]["containers"]

    insights_containers = [c for c in containers if c["name"] == "insights-agent"]
    assert len(insights_containers) == 1

    insights_container = insights_containers[0]

    assert (
        insights_container["image"]
        == f"{test_values['insights']['image']['repository']}:{test_values['insights']['image']['tag']}"
    )

    assert (
        insights_container["resources"]["requests"]["cpu"]
        == test_values["insights"]["resources"]["requests"]["cpu"]
    )
    assert (
        insights_container["resources"]["requests"]["memory"]
        == test_values["insights"]["resources"]["requests"]["memory"]
    )
    assert (
        insights_container["resources"]["limits"]["cpu"]
        == test_values["insights"]["resources"]["limits"]["cpu"]
    )
    assert (
        insights_container["resources"]["limits"]["memory"]
        == test_values["insights"]["resources"]["limits"]["memory"]
    )

    volume_mounts = insights_container["volumeMounts"]
    assert any(
        mount["name"] == "data" and mount["mountPath"] == "/jail"
        for mount in volume_mounts
    )
    assert any(
        mount["name"] == "data" and mount["mountPath"] == "/opt/datadog-agent/run"
        for mount in volume_mounts
    )


def test_insights_disabled(render_helm_template):
    disabled_values = {"insights": {"enabled": False}}
    resources = render_helm_template(disabled_values)

    insights_secrets = [
        r
        for r in resources
        if r["kind"] == "Secret" and "insights" in r["metadata"]["name"]
    ]
    assert len(insights_secrets) == 0

    stateful_sets = [r for r in resources if r["kind"] == "StatefulSet"]
    assert len(stateful_sets) > 0

    stateful_set = stateful_sets[0]
    containers = stateful_set["spec"]["template"]["spec"]["containers"]

    insights_containers = [c for c in containers if c["name"] == "insights-agent"]
    assert len(insights_containers) == 0


def test_missing_required_values(render_helm_template):
    invalid_values = {
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_SITE": "us-east",
                "INSIGHTS_AGENT_TAGS": "dev,test",
            },
        }
    }

    with pytest.raises(Exception) as e:
        render_helm_template(invalid_values)
    assert "INSIGHTS_AGENT_API_KEY must be defined" in str(e.value)

    invalid_values = {
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_API_KEY": "test-key",
                "INSIGHTS_AGENT_TAGS": "dev,test",
            },
        }
    }

    with pytest.raises(Exception) as e:
        render_helm_template(invalid_values)
    assert "INSIGHTS_AGENT_SITE must be defined" in str(e.value)

    invalid_values = {
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_API_KEY": "test-key",
                "INSIGHTS_AGENT_SITE": "us-east",
            },
        }
    }

    with pytest.raises(Exception) as e:
        render_helm_template(invalid_values)
    assert "INSIGHTS_AGENT_TAGS must be defined" in str(e.value)


def test_service_publish_not_ready_addresses(render_helm_template, test_values):
    resources = render_helm_template(test_values)

    services = [r for r in resources if r["kind"] == "Service"]
    assert len(services) > 0

    service = next(
        (s for s in services if not s["metadata"]["name"].endswith("-discovery")), None
    )
    assert service is not None
    assert service["spec"].get("publishNotReadyAddresses", False) is True

    disabled_resources = render_helm_template({"insights": {"enabled": False}})
    disabled_service = next(
        (
            s
            for s in disabled_resources
            if s["kind"] == "Service"
            and not s["metadata"]["name"].endswith("-discovery")
        ),
        None,
    )

    if disabled_service:
        assert "publishNotReadyAddresses" not in disabled_service["spec"]
