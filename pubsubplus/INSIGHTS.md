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
| `environmentVariables.INSIGHTS_AGENT_API_KEY` | The API key for your Solace Insights subscription. Available from the Solace Cloud Console.         |                                              |
| `environmentVariables.INSIGHTS_AGENT_SITE`    | The site location where broker metrics and logs will flow. Available from the Solace Cloud Console. |                                              |
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
| `forwarding.otelConfig`                       | Inline `otel-config.yaml` content. Required when `forwarding.enabled=true`; rendered into a chart-managed Secret. | `""`                        |
| `forwarding.logsConfig`                       | Inline `logs.yml` to override the agent's `/etc/datadog-agent/conf.d/solace.d/logs.yml` (rendered into a chart-managed ConfigMap). Only takes effect when `forwarding.enabled=true`. | `""`        |

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
To tune the collector's memory, set `INSIGHTS_AGENT_GOMEMLIMIT` (e.g. `"410MiB"`) under
`environmentVariables` — it is passed through and honored only in forwarding mode.

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
    INSIGHTS_AGENT_API_KEY: "unused"
    INSIGHTS_AGENT_SITE: "datadoghq.com"
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
    INSIGHTS_AGENT_API_KEY: "unused"
    INSIGHTS_AGENT_SITE: "datadoghq.com"
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
    INSIGHTS_AGENT_API_KEY: "unused"
    INSIGHTS_AGENT_SITE: "datadoghq.com"
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
