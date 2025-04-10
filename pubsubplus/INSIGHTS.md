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
| `resources.requests.cpu`                      | The minimum CPU resource required by the `insights-agent` container.                                | `200m`                                       |
| `resources.requests.memory`                   | The minimum memory resource required by the `insights-agent` container.                             | `256Mi`                                      |
| `resources.limits.cpu`                        | The maximum CPU resource the `insights-agent` container can use.                                    | `200m`                                       |
| `resources.limits.memory`                     | The maximum memory resource the `insights-agent` container can use.                                 | `512Mi`                                      |
