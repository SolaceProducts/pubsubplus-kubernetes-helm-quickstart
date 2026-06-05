# Configuration of Insights

To configure Insights, edit the Insights section of the Helm values. For more ways to override default chart values,
refer
to [Customizing the Helm Chart Before Installing](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing).

Please ensure that the values are updated accordingly for each new broker deployment.

For reference, see `pubsubplus/values.yaml` from [values.yaml](values.yaml).

| Parameter                                     | Description                                                                                         | Default                                      |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------|
| `enabled`                                     | Should be set to `true` if you want Insights enabled on the broker.                                 | `false`                                      |
| `environmentVariables`                        | Environment variables for configuring the Insights Agent                                            |                                              |
| `environmentVariables.INSIGHTS_AGENT_API_KEY` | The API key for your Solace Insights subscription. Available from the Solace Cloud Console. Required in standard mode; optional when `forwarding.enabled=true`. |                                              |
| `environmentVariables.INSIGHTS_AGENT_SITE`    | The site location where broker metrics and logs will flow. Available from the Solace Cloud Console. Required in standard mode; optional when `forwarding.enabled=true`. |                                              |
| `environmentVariables.INSIGHTS_AGENT_TAGS`    | Tags for metrics and logs. Available from the Solace Cloud Console.                                 |                                              |
| `image.repository`                            | The image repository for the Insights Agent container                                               | `gcr.io/gcp-maas-prod/solace-insights-agent` |
| `image.tag`                                   | The image tag for the Insights Agent container                                                      | `latest`                                     |
| `image.pullSecretName`                        | The name of the image pull secret for the Insights Agent container                                  | `gcr-reg-secret`                             |
| `image.pullPolicy`                            | Image pull policy for the Insights Agent container (`Always`, `IfNotPresent`, `Never`). Set to `IfNotPresent`/`Never` for air-gapped clusters with pre-loaded images. | `Always`            |
| `resources.requests.cpu`                      | The minimum CPU resource required by the `insights-agent` container.                                | `200m`                                       |
| `resources.requests.memory`                   | The minimum memory resource required by the `insights-agent` container (must use `Mi`/`Gi` units).  | `256Mi`                                      |
| `resources.limits.cpu`                        | Max CPU for the `insights-agent` container. Used verbatim if set; otherwise computed as the requests CPU plus a per-`solace.size` OTel headroom. | computed       |
| `resources.limits.memory`                     | Max memory for the `insights-agent` container. Used verbatim if set; otherwise computed as the requests memory plus a per-`solace.size` OTel headroom. | computed   |
| `forwarding.enabled`                          | Set `true` to enable Insights Agent Pro (third-party forwarding via the co-resident OTel collector). | `false`                                     |
| `forwarding.otelConfig`                       | Inline `otel-config.yaml` content for all nodes. Required when `forwarding.enabled=true` unless per-node configs are set; rendered into a chart-managed Secret. | `""`        |
| `forwarding.otelConfigPrimary`                | Per-node `otel-config.yaml` for the primary node (pod-0) in an HA deployment. Falls back to `forwarding.otelConfig` when empty. | `""`                       |
| `forwarding.otelConfigBackup`                 | Per-node `otel-config.yaml` for the backup node (pod-1) in an HA deployment. Falls back to `forwarding.otelConfig` when empty. | `""`                        |
| `forwarding.otelConfigMonitor`                | Per-node `otel-config.yaml` for the monitor node (pod-2) in an HA deployment. Falls back to `forwarding.otelConfig` when empty. | `""`                       |
| `forwarding.logsConfig`                       | Inline `logs.yml` to override the agent's `/etc/datadog-agent/conf.d/solace.d/logs.yml` (rendered into a chart-managed ConfigMap, same for all nodes). Only takes effect when `forwarding.enabled=true`. | `""`        |

## Forwarding modes

The chart natively supports the Insights forwarding modes. Each is a single
`helm install -f values.yaml` — no out-of-band `kubectl create secret` or `kubectl patch`
is required, and the configuration survives `helm upgrade`.

### Standard (direct to Datadog SaaS)

The default. The agent ships metrics and logs straight to Datadog SaaS.

```yaml
insights:
  enabled: true
  environmentVariables:
    INSIGHTS_AGENT_API_KEY: "<your-api-key>"
    INSIGHTS_AGENT_SITE: "datadoghq.com"
    INSIGHTS_AGENT_TAGS: "<your-tags>"
```

### Forwarding-only (via OTel collector, no Datadog SaaS push)

Routes metrics and logs through the co-resident OpenTelemetry collector. Supply the
collector config inline with `forwarding.otelConfig` (rendered into a chart-managed Secret).

The collector's Go memory limit (`INSIGHTS_AGENT_GOMEMLIMIT`) is set automatically in
forwarding mode: the chart derives it as 80% of the agent memory headroom (the effective
memory limit minus `resources.requests.memory`), i.e. 80% of the per-`solace.size` headroom
when limits are computed, or 80% of `limits.memory - requests.memory` when limits are
explicit. To override the derived value, set `INSIGHTS_AGENT_GOMEMLIMIT` (e.g. `"410MiB"`)
under `environmentVariables`. If you set explicit `resources.limits.memory` that does not
exceed `requests.memory`, the chart cannot derive a value and fails fast — set
`INSIGHTS_AGENT_GOMEMLIMIT` explicitly or raise the limit.

> **Note on resource limits and `solace.systemScaling`:** when `resources.limits` are not
> set, the chart computes the `insights-agent` limits as the requests value plus a headroom
> selected by `solace.size`. If you scale the broker with `solace.systemScaling` (which makes
> the chart ignore `solace.size`), that headroom falls back to the `solace.size` default tier
> and will not track your actual broker size — set `insights.resources.limits` explicitly to
> size the agent for a custom-scaled broker.

```yaml
insights:
  enabled: true
  environmentVariables:
    # INSIGHTS_AGENT_API_KEY and INSIGHTS_AGENT_SITE are not required in forwarding mode.
    INSIGHTS_AGENT_TAGS: "<your-tags>"
  forwarding:
    enabled: true
    otelConfig: |
      receivers:
        datadog:
          endpoint: localhost:6000
      exporters:
        # ...your exporters...
      service:
        pipelines:
          # ...your pipelines...
```

### Forwarding + Datadog push (dual-write)

Forwards through the OTel collector and also dual-writes to Datadog SaaS. Dual-write is
not a separate chart setting — it is driven entirely by three agent env vars that you
provide under `insights.environmentVariables`; the chart passes them through verbatim.
Substitute your Datadog site for `<site>` (e.g. `datadoghq.com`) and your real API keys.

```yaml
insights:
  enabled: true
  environmentVariables:
    # INSIGHTS_AGENT_API_KEY and INSIGHTS_AGENT_SITE are not required in forwarding mode.
    INSIGHTS_AGENT_TAGS: "<your-tags>"
    # ── dual-write to Datadog SaaS (passed through to the agent verbatim) ──
    INSIGHTS_AGENT_LOGS_ENABLED: "true"
    INSIGHTS_AGENT_ADDITIONAL_ENDPOINTS: '{"https://app.datadoghq.com":["REAL_DD_KEY_1","REAL_DD_KEY_2"]}'
    INSIGHTS_AGENT_LOGS_CONFIG_ADDITIONAL_ENDPOINTS: '[{"api_key":"REAL_DD_KEY_1","host":"agent-http-intake.logs.datadoghq.com","use_compression":true,"compression_level":2},{"api_key":"REAL_DD_KEY_2","host":"agent-http-intake.logs.datadoghq.com","use_compression":true,"compression_level":2}]'
  forwarding:
    enabled: true
    otelConfig: |
      receivers:
        datadog:
          endpoint: localhost:6000
      # ...
```

### Overriding the agent log-collection config (`logs.yml`)

In forwarding mode you can replace the Datadog agent's Solace log-collection config
(`/etc/datadog-agent/conf.d/solace.d/logs.yml`). Supply it inline with `forwarding.logsConfig`
(rendered into a chart-managed ConfigMap and mounted over that single file). This only takes
effect when `forwarding.enabled=true`.

```yaml
insights:
  enabled: true
  environmentVariables:
    # INSIGHTS_AGENT_API_KEY and INSIGHTS_AGENT_SITE are not required in forwarding mode.
    INSIGHTS_AGENT_TAGS: "<your-tags>"
  forwarding:
    enabled: true
    otelConfig: |
      service: {}
    logsConfig: |
      logs:
        - type: file
          path: /jail/logs/*.log
          service: solace
          source: solace
```

### HA deployments: per-node OTel config

In an HA deployment (`solace.redundancy=true`) the broker runs three nodes — primary
(pod-0), backup (pod-1), and monitor (pod-2). If each node needs a different
`otel-config.yaml` (for example, an auto-generated config whose only per-node difference
is the `ha_role` attribute), supply one config per node:

- `forwarding.otelConfigPrimary` → pod-0
- `forwarding.otelConfigBackup` → pod-1
- `forwarding.otelConfigMonitor` → pod-2

The chart renders them into a single Secret under per-pod keys
(`otel-config-<release>-pubsubplus-<ordinal>.yaml`) and each pod mounts its own via
`subPathExpr` keyed on the pod name (`metadata.name`, available on all Kubernetes
versions). A node with an empty per-node value falls back to `forwarding.otelConfig`, so
you can also set just one or two of them. `logsConfig` is always shared across all nodes.

Because these values are whole files, load them with `--set-file` instead of pasting
(avoids indentation mistakes and keeps the generated files intact):

```bash
helm install my-release pubsubplus \
  -f values.yaml \
  --set solace.redundancy=true \
  --set insights.enabled=true \
  --set-file insights.forwarding.otelConfigPrimary=./otel-primary.yaml \
  --set-file insights.forwarding.otelConfigBackup=./otel-backup.yaml \
  --set-file insights.forwarding.otelConfigMonitor=./otel-monitor.yaml \
  --set-file insights.forwarding.logsConfig=./logs.yaml
```

Keep the stable settings (`forwarding.enabled: true`, `environmentVariables`, image, etc.)
in `values.yaml`; `--set-file` overrides the matching keys with each file's contents.
(`--set-file` also works for the single-config keys, e.g.
`--set-file insights.forwarding.otelConfig=./otel-config.yaml` in non-HA deployments.)
