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


def _otel_key(idx):
    # Secret keys are keyed by pod name <fullname>-<ordinal>; the render helper
    # uses release "test-release", so fullname is "test-release-pubsubplus".
    return "otel-config-test-release-pubsubplus-{}.yaml".format(idx)


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

    # Chart-managed OTel config Secret is rendered (keyed per pod index).
    otel_secret = _otel_secret(resources)
    assert otel_secret is not None
    assert _otel_key(0) in otel_secret["stringData"]

    # In forwarding mode the chart manages these keys in stringData.
    env_secret = _env_secret(resources)
    assert env_secret["stringData"]["INSIGHTS_AGENT_THIRD_PARTY_FORWARDING_ENABLED"] == "true"
    assert env_secret["stringData"]["INSIGHTS_AGENT_TELEMETRY_ENABLED"] == "false"
    # GOMEMLIMIT is derived from the agent memory headroom when the operator did not
    # set it: 80% of (limits.memory - requests.memory) = 80% of (512Mi - 256Mi) = 204MiB.
    assert env_secret["stringData"]["INSIGHTS_AGENT_GOMEMLIMIT"] == "204MiB"
    # The Datadog push vars remain operator-supplied via environmentVariables only.
    assert "INSIGHTS_AGENT_LOGS_ENABLED" not in env_secret["stringData"]
    assert "INSIGHTS_AGENT_ADDITIONAL_ENDPOINTS" not in env_secret["stringData"]

    # Volume + volumeMount wired to the chart-managed Secret.
    mount = next(
        m
        for m in _insights_container(resources)["volumeMounts"]
        if m["name"] == "otel-config"
    )
    assert mount["mountPath"] == "/etc/datadog-agent/otel-config.yaml"
    assert mount["subPathExpr"] == "otel-config-$(POD_NAME).yaml"
    assert mount["readOnly"] is True

    volume = next(v for v in _volumes(resources) if v["name"] == "otel-config")
    assert volume["secret"]["secretName"].endswith("-otel-config")


def test_chart_managed_keys_not_duplicated_in_data(render_helm_template, base_values):
    # Keys the chart manages in stringData must not also be emitted in the data block
    # (which would create conflicting duplicate keys). Operator-supplied custom vars
    # still pass through to data.
    values = copy.deepcopy(base_values)
    values["insights"]["environmentVariables"].update(
        {
            "INSIGHTS_AGENT_SEMP_PORT": "9999",          # chart-managed (always)
            "INSIGHTS_AGENT_THIRD_PARTY_FORWARDING_ENABLED": "false",   # chart-managed (forwarding only)
            "MY_CUSTOM_VAR": "keepme",                    # operator-supplied
        }
    )
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    sec = _env_secret(render_helm_template(values))
    data, string_data = sec["data"], sec["stringData"]

    assert base64.b64decode(data["MY_CUSTOM_VAR"]).decode() == "keepme"
    assert "INSIGHTS_AGENT_SEMP_PORT" not in data
    assert "INSIGHTS_AGENT_THIRD_PARTY_FORWARDING_ENABLED" not in data
    # They appear once, in stringData, with the chart's values (operator value ignored).
    assert string_data["INSIGHTS_AGENT_SEMP_PORT"] == "8080"
    assert string_data["INSIGHTS_AGENT_THIRD_PARTY_FORWARDING_ENABLED"] == "true"


# --------------------------------------------------------------------------- #
# Per-node otelConfig (HA)
# --------------------------------------------------------------------------- #
def test_otel_per_node_configs_keyed_by_pod_index(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev", "redundancy": True}
    values["insights"]["forwarding"] = {
        "enabled": True,
        "otelConfigPrimary": "service: {role: primary}\n",
        "otelConfigBackup": "service: {role: backup}\n",
        "otelConfigMonitor": "service: {role: monitor}\n",
    }
    sd = _otel_secret(render_helm_template(values))["stringData"]
    assert "role: primary" in sd[_otel_key(0)]
    assert "role: backup" in sd[_otel_key(1)]
    assert "role: monitor" in sd[_otel_key(2)]


def test_otel_per_node_falls_back_to_otel_config(render_helm_template, base_values):
    # backup/monitor unset -> fall back to otelConfig; primary overrides.
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev", "redundancy": True}
    values["insights"]["forwarding"] = {
        "enabled": True,
        "otelConfig": "service: {role: shared}\n",
        "otelConfigPrimary": "service: {role: primary}\n",
    }
    sd = _otel_secret(render_helm_template(values))["stringData"]
    assert "role: primary" in sd[_otel_key(0)]
    assert "role: shared" in sd[_otel_key(1)]
    assert "role: shared" in sd[_otel_key(2)]


def test_otel_non_ha_renders_only_index_0(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev"}  # redundancy defaults false
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    sd = _otel_secret(render_helm_template(values))["stringData"]
    assert _otel_key(0) in sd
    assert _otel_key(1) not in sd
    assert _otel_key(2) not in sd


def test_otel_ha_requires_backup_config_when_no_fallback(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev", "redundancy": True}
    # primary set, but no otelConfig fallback and no backup/monitor -> fail for backup.
    values["insights"]["forwarding"] = {
        "enabled": True,
        "otelConfigPrimary": "service: {}\n",
    }
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert "backup node" in str(e.value)


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

    # The chart must NOT emit its own copies into stringData (no clobbering). For
    # GOMEMLIMIT specifically, an operator-supplied value suppresses the chart's
    # computed injection so it appears only once (in data).
    string_data = env_secret.get("stringData", {})
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in string_data
    assert "INSIGHTS_AGENT_LOGS_ENABLED" not in string_data
    assert "INSIGHTS_AGENT_ADDITIONAL_ENDPOINTS" not in string_data
    assert "INSIGHTS_AGENT_LOGS_CONFIG_ADDITIONAL_ENDPOINTS" not in string_data


# --------------------------------------------------------------------------- #
# Derived INSIGHTS_AGENT_GOMEMLIMIT (forwarding mode, operator value not set)
# --------------------------------------------------------------------------- #
def test_broker_size_passed_when_limits_computed(render_helm_template, base_values):
    # With computed limits (no explicit limits.memory override), the chart passes the
    # broker scaling tier and lets the agent derive GOMEMLIMIT. solace.size "prod1k" is
    # translated to the agent's vocabulary "1k" (the "prod" prefix is stripped).
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "prod1k"}
    del values["insights"]["resources"]["limits"]
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    sd = _env_secret(render_helm_template(values))["stringData"]
    assert sd["INSIGHTS_AGENT_BROKER_SIZE"] == "1k"
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in sd


def test_operator_broker_size_passes_through_and_suppresses_auto_inject(render_helm_template, base_values):
    # An operator-supplied INSIGHTS_AGENT_BROKER_SIZE passes through the data block and
    # suppresses the chart's auto-injected tier (no duplicate key) and its GOMEMLIMIT.
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "prod10k"}
    del values["insights"]["resources"]["limits"]
    values["insights"]["environmentVariables"]["INSIGHTS_AGENT_BROKER_SIZE"] = "100k"
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    sec = _env_secret(render_helm_template(values))
    assert base64.b64decode(sec["data"]["INSIGHTS_AGENT_BROKER_SIZE"]).decode() == "100k"
    sd = sec.get("stringData", {})
    assert "INSIGHTS_AGENT_BROKER_SIZE" not in sd
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in sd


def test_gomemlimit_computed_from_explicit_limit(render_helm_template, base_values):
    # Explicit limit -> GOMEMLIMIT = 80% of (limit - requests) = 80% of (2048 - 256) = 1433MiB.
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev"}
    values["insights"]["resources"]["limits"]["memory"] = "2Gi"
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    sd = _env_secret(render_helm_template(values))["stringData"]
    assert sd["INSIGHTS_AGENT_GOMEMLIMIT"] == "1433MiB"


def test_gomemlimit_not_injected_in_standard_mode(render_helm_template, base_values):
    # Standard mode has no OTel collector, so the chart does not derive GOMEMLIMIT.
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev"}
    sd = _env_secret(render_helm_template(values))["stringData"]
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in sd


def test_gomemlimit_fails_when_explicit_limit_has_no_headroom(render_helm_template, base_values):
    # Explicit limit not above requests and no operator GOMEMLIMIT -> fail-fast.
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev"}
    values["insights"]["resources"]["limits"]["memory"] = "256Mi"  # == agent base
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert "at or below the agent base" in str(e.value)


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
# Empty API_KEY / SITE suppression (forwarding mode)
# --------------------------------------------------------------------------- #
def test_empty_api_key_site_suppressed_in_forwarding(render_helm_template, base_values):
    # The chart's empty defaults for API_KEY/SITE are merged in even when omitted; in
    # forwarding mode they are optional, so empty values must not be emitted as blank env vars.
    values = copy.deepcopy(base_values)
    values["insights"]["environmentVariables"]["INSIGHTS_AGENT_API_KEY"] = ""
    values["insights"]["environmentVariables"]["INSIGHTS_AGENT_SITE"] = ""
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    data = _env_secret(render_helm_template(values))["data"]
    assert "INSIGHTS_AGENT_API_KEY" not in data
    assert "INSIGHTS_AGENT_SITE" not in data
    # Non-empty operator vars are unaffected.
    assert "INSIGHTS_AGENT_TAGS" in data


def test_nonempty_api_key_site_passthrough_in_forwarding(render_helm_template, base_values):
    # If the operator does set them in forwarding mode, they pass through unchanged.
    values = copy.deepcopy(base_values)
    values["insights"]["environmentVariables"]["INSIGHTS_AGENT_API_KEY"] = "k"
    values["insights"]["environmentVariables"]["INSIGHTS_AGENT_SITE"] = "datadoghq.eu"
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    data = _env_secret(render_helm_template(values))["data"]
    assert base64.b64decode(data["INSIGHTS_AGENT_API_KEY"]).decode() == "k"
    assert base64.b64decode(data["INSIGHTS_AGENT_SITE"]).decode() == "datadoghq.eu"


def test_env_secret_consumed_via_envfrom(render_helm_template, base_values):
    # Suppressing optional keys is only safe because the container loads the env secret via
    # envFrom (a missing key just means the var is unset). A non-optional secretKeyRef to a
    # suppressed key would fail the pod with CreateContainerConfigError, so guard against it.
    values = copy.deepcopy(base_values)
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    c = _insights_container(render_helm_template(values))
    env_from_secrets = [
        e.get("secretRef", {}).get("name", "") for e in c.get("envFrom", [])
    ]
    assert any(n.endswith("-insights-agent-env-secrets") for n in env_from_secrets)
    for e in c.get("env", []):
        ref = e.get("valueFrom", {}).get("secretKeyRef", {})
        assert not ref.get("name", "").endswith("-insights-agent-env-secrets")


# --------------------------------------------------------------------------- #
# Backward compatibility
# --------------------------------------------------------------------------- #
def test_forwarding_disabled_is_noop(render_helm_template, base_values):
    resources = render_helm_template(base_values)  # no forwarding block at all

    assert _otel_secret(resources) is None

    env_secret = _env_secret(resources)
    assert "INSIGHTS_AGENT_THIRD_PARTY_FORWARDING_ENABLED" not in env_secret.get("stringData", {})

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


def test_computed_limit_independent_of_requests_below_it(render_helm_template, base_values):
    # The computed limit uses a fixed base (not requests); requests below it don't change it.
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "1", "memory": "1Gi"}
    values["solace"] = {"size": "prod10k"}
    container = _insights_container(render_helm_template(values))
    # computed = 256Mi + 2048Mi = 2304Mi; 200m + 1000m = 1.2 cores. Requests (1024Mi / 1 core)
    # are below those, so the limit stays at the computed value.
    assert container["resources"]["limits"]["memory"] == "2304Mi"
    assert float(container["resources"]["limits"]["cpu"]) == 1.2


def test_requests_equal_limits_is_guaranteed_qos(render_helm_template, base_values):
    # Set requests to the per-size value and leave limits unset -> requests == limits
    # (Guaranteed QoS). Limits are computed (not an explicit limits.memory override), so
    # the chart passes the tier and the agent derives GOMEMLIMIT (dev -> 409MiB).
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["solace"] = {"size": "dev"}
    values["insights"]["resources"]["requests"] = {"cpu": "700m", "memory": "768Mi"}
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    resources = render_helm_template(values)
    c = _insights_container(resources)
    assert c["resources"]["limits"]["memory"] == "768Mi"
    assert c["resources"]["limits"]["memory"] == c["resources"]["requests"]["memory"]
    assert float(c["resources"]["limits"]["cpu"]) == 0.7
    sd = _env_secret(resources)["stringData"]
    assert sd["INSIGHTS_AGENT_BROKER_SIZE"] == "dev"
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in sd


def test_computed_limit_clamps_up_to_large_request(render_helm_template, base_values):
    # A request above base + headroom raises the container limit up to the request. The
    # chart still passes the tier (a requests-driven clamp is not an explicit limits.memory
    # override), so GOMEMLIMIT is left to the agent (fixed per tier, not scaled to the clamp).
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["solace"] = {"size": "dev"}
    values["insights"]["resources"]["requests"] = {"cpu": "200m", "memory": "1Gi"}
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    resources = render_helm_template(values)
    assert _insights_container(resources)["resources"]["limits"]["memory"] == "1024Mi"
    sd = _env_secret(resources)["stringData"]
    assert sd["INSIGHTS_AGENT_BROKER_SIZE"] == "dev"
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in sd


def test_agent_limits_verbatim_when_set(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "prod10k"}  # large delta, but explicit values win
    values["insights"]["resources"]["limits"] = {"cpu": "1", "memory": "2Gi"}
    container = _insights_container(render_helm_template(values))
    assert str(container["resources"]["limits"]["cpu"]) == "1"
    assert container["resources"]["limits"]["memory"] == "2Gi"


def test_agent_limits_fractional_mi_request_not_below_request(render_helm_template, base_values):
    # Regression: a fractional-Mi request must ceil (not truncate) so the limit clamps up
    # to a value not below the request. dev computed = 768Mi; 1536.5Mi ceils to 1537Mi.
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "200m", "memory": "1536.5Mi"}
    values["solace"] = {"size": "dev"}
    container = _insights_container(render_helm_template(values))
    assert container["resources"]["limits"]["memory"] == "1537Mi"


def test_agent_limits_fractional_gi_request(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "200m", "memory": "1.5Gi"}
    values["solace"] = {"size": "prod1k"}
    container = _insights_container(render_helm_template(values))
    # prod1k computed = 256+1024 = 1280Mi; request 1.5Gi=1536Mi clamps the limit up to 1536Mi.
    assert container["resources"]["limits"]["memory"] == "1536Mi"


def test_agent_limits_rejects_non_mi_gi_memory(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "200m", "memory": "512Ki"}
    values["solace"] = {"size": "dev"}
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert "must be specified in Mi or Gi" in str(e.value)


# --------------------------------------------------------------------------- #
# Full per-size matrix: computed memory/CPU limits (chart) plus the broker scaling
# tier passed to the agent (INSIGHTS_AGENT_BROKER_SIZE = solace.size with the "prod"
# prefix stripped), with default requests (256Mi / 200m). Locks the hand-maintained
# delta maps and the tier translation for every solace.size in one place so a drift in
# any tier is caught. (The tier -> GOMEMLIMIT mapping is the agent's concern, covered by
# the agent's own unit tests.)
# --------------------------------------------------------------------------- #
SIZE_MATRIX = {
    "dev": ("768Mi", 0.7, "dev"),
    "prod1k": ("1280Mi", 0.7, "1k"),
    "prod10k": ("2304Mi", 1.2, "10k"),
    "prod100k": ("4352Mi", 2.2, "100k"),
    "prod200k": ("5888Mi", 2.2, "200k"),
}


@pytest.mark.parametrize("size,expected", list(SIZE_MATRIX.items()))
def test_computed_limits_and_broker_size_per_size(render_helm_template, base_values, size, expected):
    exp_mem, exp_cpu, exp_broker = expected
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": size}
    del values["insights"]["resources"]["limits"]  # computed
    values["insights"]["forwarding"] = {"enabled": True, "otelConfig": "service: {}\n"}
    resources = render_helm_template(values)
    container = _insights_container(resources)
    assert container["resources"]["limits"]["memory"] == exp_mem
    assert float(container["resources"]["limits"]["cpu"]) == exp_cpu
    sd = _env_secret(resources)["stringData"]
    assert sd["INSIGHTS_AGENT_BROKER_SIZE"] == exp_broker
    assert "INSIGHTS_AGENT_GOMEMLIMIT" not in sd


# --------------------------------------------------------------------------- #
# TLS: the insights SEMP connection uses the secure port/protocol.
# --------------------------------------------------------------------------- #
def test_tls_enabled_uses_https_semp_port(render_helm_template, base_values):
    values = copy.deepcopy(base_values)
    values["tls"] = {"enabled": True, "serverCertificatesSecret": "dummy-tls"}
    sd = _env_secret(render_helm_template(values))["stringData"]
    assert sd["INSIGHTS_AGENT_SEMP_PORT"] == "1943"
    assert sd["INSIGHTS_AGENT_SEMP_PROTOCOL"] == "https"


def test_tls_disabled_uses_plain_semp_port(render_helm_template, base_values):
    sd = _env_secret(render_helm_template(base_values))["stringData"]
    assert sd["INSIGHTS_AGENT_SEMP_PORT"] == "8080"
    assert sd["INSIGHTS_AGENT_SEMP_PROTOCOL"] == "http"


def test_agent_limits_fractional_millicore_cpu_not_truncated(render_helm_template, base_values):
    # A fractional-millicore request above the computed limit must ceil (not truncate) when
    # clamping. dev computed = 700m; request 1500.5m ceils to 1501m = 1.501 cores (not 1.5).
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["insights"]["resources"]["requests"] = {"cpu": "1500.5m", "memory": "256Mi"}
    values["solace"] = {"size": "dev"}
    container = _insights_container(render_helm_template(values))
    assert float(container["resources"]["limits"]["cpu"]) == 1.501


def test_agent_limits_partial_override(render_helm_template, base_values):
    # memory provided -> verbatim; cpu omitted -> computed from requests base.
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "dev"}
    values["insights"]["resources"]["limits"] = {"memory": "900Mi"}
    container = _insights_container(render_helm_template(values))
    assert container["resources"]["limits"]["memory"] == "900Mi"
    assert float(container["resources"]["limits"]["cpu"]) == 0.7  # 200m + 500m


_SYSTEM_SCALING = {
    "maxConnections": 100,
    "maxQueueMessages": 100,
    "maxSpoolUsage": 1000,
    "cpu": "2",
    "memory": "4000Mi",
}


def test_agent_limits_unknown_size_fails_when_computed(render_helm_template, base_values):
    # Under systemScaling the broker ignores solace.size (no "Invalid solace.size"),
    # so an unknown size would otherwise yield silent zero headroom; the helper fails
    # instead of computing a limit equal to the request.
    values = copy.deepcopy(base_values)
    del values["insights"]["resources"]["limits"]
    values["solace"] = {"size": "bogus", "systemScaling": dict(_SYSTEM_SCALING)}
    with pytest.raises(Exception) as e:
        render_helm_template(values)
    assert "unknown solace.size" in str(e.value)


def test_agent_limits_unknown_size_ok_with_explicit_limits(render_helm_template, base_values):
    # Explicit limits bypass the helper (and its unknown-size guard).
    values = copy.deepcopy(base_values)
    values["solace"] = {"size": "bogus", "systemScaling": dict(_SYSTEM_SCALING)}
    values["insights"]["resources"]["limits"] = {"cpu": "1", "memory": "1Gi"}
    container = _insights_container(render_helm_template(values))
    assert container["resources"]["limits"]["memory"] == "1Gi"
    assert str(container["resources"]["limits"]["cpu"]) == "1"


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
