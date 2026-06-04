import base64
import copy

import pytest


@pytest.fixture
def base_values(cleanup_test_values):
    return {
        "insights": {
            "enabled": True,
            "environmentVariables": {
                "INSIGHTS_AGENT_API_KEY": "unused",
                "INSIGHTS_AGENT_SITE": "datadoghq.com",
                "INSIGHTS_AGENT_TAGS": "env:dev",
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


def _env_secret(resources):
    return next(
        (
            r
            for r in resources
            if r["kind"] == "Secret"
            and "insights-agent-env-secrets" in r["metadata"]["name"]
        ),
        None,
    )


def _otel_secret(resources):
    return next(
        (
            r
            for r in resources
            if r["kind"] == "Secret" and r["metadata"]["name"].endswith("-otel-config")
        ),
        None,
    )


def _logs_configmap(resources):
    return next(
        (
            r
            for r in resources
            if r["kind"] == "ConfigMap" and r["metadata"]["name"].endswith("-logs-config")
        ),
        None,
    )


def _insights_container(resources):
    stateful_set = next(r for r in resources if r["kind"] == "StatefulSet")
    containers = stateful_set["spec"]["template"]["spec"]["containers"]
    return next(c for c in containers if c["name"] == "insights-agent")


def _volumes(resources):
    stateful_set = next(r for r in resources if r["kind"] == "StatefulSet")
    return stateful_set["spec"]["template"]["spec"]["volumes"]


# --------------------------------------------------------------------------- #
# Forwarding-only mode
# --------------------------------------------------------------------------- #
def test_forwarding_only_renders_otel_secret_and_mount(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["insights"]["forwarding"] = {
        "enabled": True,
        "otelConfig": "service:\n  pipelines: {}\n",
    }
    resources = render_helm_template(values)

    # Chart-managed OTel config Secret is rendered.
    otel_secret = _otel_secret(resources)
    assert otel_secret is not None
    assert "otel-config.yaml" in otel_secret["stringData"]

    # Only SOLACE_CUSTOM_INSIGHTS_ENABLED is chart-managed in stringData.
    env_secret = _env_secret(resources)
    assert env_secret["stringData"]["SOLACE_CUSTOM_INSIGHTS_ENABLED"] == "true"
    # The chart no longer injects GOMEMLIMIT or the push env vars; those are
    # operator-supplied via environmentVariables only.
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in env_secret["stringData"]
    assert "INSIGHTS_AGENT_LOGS_ENABLED" not in env_secret["stringData"]
    assert "INSIGHTS_AGENT_ADDITIONAL_ENDPOINTS" not in env_secret["stringData"]

    # Volume + volumeMount wired to the chart-managed Secret.
    mount = next(
        m
        for m in _insights_container(resources)["volumeMounts"]
        if m["name"] == "otel-config"
    )
    assert mount["mountPath"] == "/etc/datadog-agent/otel-config.yaml"
    assert mount["subPath"] == "otel-config.yaml"
    assert mount["readOnly"] is True

    volume = next(v for v in _volumes(resources) if v["name"] == "otel-config")
    assert volume["secret"]["secretName"].endswith("-otel-config")


# --------------------------------------------------------------------------- #
# Forwarding-mode agent settings (GOMEMLIMIT + Datadog push) — raw env vars,
# not chart fields; passed through verbatim.
# --------------------------------------------------------------------------- #
def test_forwarding_env_vars_pass_through(render_helm_template, base_values):
    # The chart has no datadogPush or gomemLimit field; the operator supplies these
    # env vars directly under environmentVariables and the chart passes them through
    # (into the env-secret's `data` block, base64-encoded like the other env vars).
    additional = '{"https://app.datadoghq.com":["KEY1","KEY2"]}'
    logs_cfg = (
        '[{"api_key":"KEY1","host":"agent-http-intake.logs.datadoghq.com",'
        '"use_compression":true,"compression_level":2}]'
    )
    values = copy.deepcopy(base_values)
    values["insights"]["environmentVariables"].update(
        {
            "INSIGHTS_AGENT_GOMEMLIMIT": "410MiB",
            "INSIGHTS_AGENT_LOGS_ENABLED": "true",
            "INSIGHTS_AGENT_ADDITIONAL_ENDPOINTS": additional,
            "INSIGHTS_AGENT_LOGS_CONFIG_ADDITIONAL_ENDPOINTS": logs_cfg,
        }
    )
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    env_secret = _env_secret(render_helm_template(values))

    data = env_secret["data"]
    assert base64.b64decode(data["INSIGHTS_AGENT_GOMEMLIMIT"]).decode() == "410MiB"
    assert base64.b64decode(data["INSIGHTS_AGENT_LOGS_ENABLED"]).decode() == "true"
    assert base64.b64decode(data["INSIGHTS_AGENT_ADDITIONAL_ENDPOINTS"]).decode() == additional
    assert (
        base64.b64decode(data["INSIGHTS_AGENT_LOGS_CONFIG_ADDITIONAL_ENDPOINTS"]).decode()
        == logs_cfg
    )

    # The chart must NOT emit its own copies into stringData (no clobbering).
    string_data = env_secret.get("stringData", {})
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in string_data
    assert "INSIGHTS_AGENT_LOGS_ENABLED" not in string_data
    assert "INSIGHTS_AGENT_ADDITIONAL_ENDPOINTS" not in string_data
    assert "INSIGHTS_AGENT_LOGS_CONFIG_ADDITIONAL_ENDPOINTS" not in string_data


def test_forwarding_does_not_require_api_key_or_site(render_helm_template, base_values):
    # In forwarding mode INSIGHTS_AGENT_API_KEY / INSIGHTS_AGENT_SITE are optional
    # (the agent overrides/derives them); only TAGS remains required.
    values = copy.deepcopy(base_values)
    values["insights"]["environmentVariables"] = {"INSIGHTS_AGENT_TAGS": "env:dev"}
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    # Renders without error despite no API_KEY/SITE.
    assert _otel_secret(render_helm_template(values)) is not None


def test_standard_mode_still_requires_api_key(render_helm_template, base_values):
    # With forwarding disabled (standard mode), API_KEY remains required.
    values = copy.deepcopy(base_values)
    values["insights"]["environmentVariables"] = {
        "INSIGHTS_AGENT_SITE": "datadoghq.com",
        "INSIGHTS_AGENT_TAGS": "env:dev",
    }
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert "INSIGHTS_AGENT_API_KEY must be defined" in str(e.value)


# --------------------------------------------------------------------------- #
# Backward compatibility
# --------------------------------------------------------------------------- #
def test_forwarding_disabled_is_noop(render_helm_template, base_values):
    resources = render_helm_template(base_values)  # no forwarding block at all

    assert _otel_secret(resources) is None

    env_secret = _env_secret(resources)
    assert "SOLACE_CUSTOM_INSIGHTS_ENABLED" not in env_secret.get("stringData", {})

    assert all(v["name"] != "otel-config" for v in _volumes(resources))
    assert all(
        m["name"] != "otel-config"
        for m in _insights_container(resources)["volumeMounts"]
    )


# --------------------------------------------------------------------------- #
# Agent logs.yml override (ConfigMap)
# --------------------------------------------------------------------------- #
def test_logs_override_inline_renders_configmap_and_mount(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["insights"]["forwarding"] = {
        "enabled": True,
        "otelConfig": "service: {}\n",
        "logsConfig": "logs:\n  - type: file\n    path: /jail/logs/*.log\n",
    }
    resources = render_helm_template(values)

    cm = _logs_configmap(resources)
    assert cm is not None
    assert "logs.yml" in cm["data"]
    assert "/jail/logs/*.log" in cm["data"]["logs.yml"]

    mount = next(
        m
        for m in _insights_container(resources)["volumeMounts"]
        if m["name"] == "logs-config"
    )
    assert mount["mountPath"] == "/etc/datadog-agent/conf.d/solace.d/logs.yml"
    assert mount["subPath"] == "logs.yml"
    assert mount["readOnly"] is True

    volume = next(v for v in _volumes(resources) if v["name"] == "logs-config")
    assert volume["configMap"]["name"].endswith("-logs-config")


def test_logs_override_ignored_without_forwarding_block(render_helm_template, base_values):
    # No logs override and no forwarding -> no logs ConfigMap / volume.
    resources = render_helm_template(base_values)
    assert _logs_configmap(resources) is None
    assert all(v["name"] != "logs-config" for v in _volumes(resources))


def test_logs_override_requires_forwarding(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["insights"]["forwarding"] = {"logsConfig": "logs: []\n"}  # forwarding disabled
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert "only takes effect when insights.forwarding.enabled=true" in str(e.value)


# --------------------------------------------------------------------------- #
# insights-agent resource limits: computed when not set, verbatim when set.
# Computed base = requests value (else 256Mi / 200m) + per-size-class headroom.
# --------------------------------------------------------------------------- #
def test_agent_limits_computed_from_default_base(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]  # not provided -> computed
    values["solace"] = {"size": "dev"}
    container = _insights_container(render_helm_template(values))
    # requests base 256Mi/200m + dev headroom 512Mi/500m.
    assert container["resources"]["limits"]["memory"] == "768Mi"
    assert float(container["resources"]["limits"]["cpu"]) == 0.7


def test_agent_limits_computed_base_follows_requests(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "1", "memory": "1Gi"}
    values["solace"] = {"size": "prod10k"}
    container = _insights_container(render_helm_template(values))
    # base = requests (1Gi=1024Mi / 1 core) + prod10k headroom (2048Mi / 1000m).
    assert container["resources"]["limits"]["memory"] == "3072Mi"
    assert float(container["resources"]["limits"]["cpu"]) == 2.0


def test_agent_limits_verbatim_when_set(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "prod10k"}  # large delta, but explicit values win
    values["insights"]["resources"]["limits"] = {"cpu": "1", "memory": "2Gi"}
    container = _insights_container(render_helm_template(values))
    assert str(container["resources"]["limits"]["cpu"]) == "1"
    assert container["resources"]["limits"]["memory"] == "2Gi"


def test_agent_limits_fractional_mi_request_not_below_request(render_helm_template, base_values):
    # Regression: a fractional-Mi request must not parse to 0 and yield a limit
    # below the request (which k8s would reject). 1536.5Mi ceils to 1537 + 512 = 2049Mi.
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "200m", "memory": "1536.5Mi"}
    values["solace"] = {"size": "dev"}
    container = _insights_container(render_helm_template(values))
    assert container["resources"]["limits"]["memory"] == "2049Mi"


def test_agent_limits_fractional_gi_request(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "200m", "memory": "1.5Gi"}
    values["solace"] = {"size": "prod1k"}
    container = _insights_container(render_helm_template(values))
    # 1.5Gi = 1536Mi + prod1k headroom 1024Mi.
    assert container["resources"]["limits"]["memory"] == "2560Mi"


def test_agent_limits_rejects_non_mi_gi_memory(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "200m", "memory": "512Ki"}
    values["solace"] = {"size": "dev"}
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert "must be specified in Mi or Gi" in str(e.value)


def test_agent_limits_fractional_millicore_cpu_not_truncated(render_helm_template, base_values):
    # "100.5m" must not truncate to 0; ceil(100.5)=101 + dev 500m = 601m = 0.601 cores.
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "100.5m", "memory": "256Mi"}
    values["solace"] = {"size": "dev"}
    container = _insights_container(render_helm_template(values))
    assert float(container["resources"]["limits"]["cpu"]) == 0.601


def test_agent_limits_partial_override(render_helm_template, base_values):
    # memory provided -> verbatim; cpu omitted -> computed from requests base.
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev"}
    values["insights"]["resources"]["limits"] = {"memory": "900Mi"}
    container = _insights_container(render_helm_template(values))
    assert container["resources"]["limits"]["memory"] == "900Mi"
    assert float(container["resources"]["limits"]["cpu"]) == 0.7  # 200m + 500m


# --------------------------------------------------------------------------- #
# imagePullPolicy (DATAGO-134542)
# --------------------------------------------------------------------------- #
def test_insights_pull_policy_default_always(render_helm_template, base_values):
    container = _insights_container(render_helm_template(base_values))
    assert container["imagePullPolicy"] == "Always"


def test_insights_pull_policy_override(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["insights"]["image"]["pullPolicy"] = "IfNotPresent"
    container = _insights_container(render_helm_template(values))
    assert container["imagePullPolicy"] == "IfNotPresent"


# --------------------------------------------------------------------------- #
# Fail-fast validation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "forwarding_without_config",
            "forwarding": {"enabled": True},
            "expected_error": "requires insights.forwarding.otelConfig",
        },
    ],
)
def test_forwarding_fail_fast(render_helm_template, base_values, test_case):
    values = copy.deepcopy(base_values)
    values["insights"]["forwarding"] = test_case["forwarding"]
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert test_case["expected_error"] in str(e.value)
