{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "solace.name" -}}
  {{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{/*
Create a default fully qualified app name.
We truncate at 53 chars because some Kubernetes name fields are limited (by the DNS naming spec).
*/}}
{{- define "solace.fullname" -}}
  {{- if .Values.fullnameOverride -}}
    {{- .Values.fullnameOverride | trunc 53 | trimSuffix "-" -}}
  {{- else -}}
    {{- $name := default .Chart.Name .Values.nameOverride -}}
    {{- printf "%s-%s" .Release.Name $name | trunc 53 | trimSuffix "-" -}}
  {{- end -}}
{{- end -}}
{{/*
Return the name of the service account to use
*/}}
{{- define "solace.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default ( cat (include "solace.fullname" .) "-sa"  | nospace )  .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Determine the service type based on redundancy
*/}}
{{- define "solace.serviceType" -}}
{{- $serviceType := "enterprise-standalone" -}}
{{- if .Values.solace.redundancy -}}
  {{- $serviceType = "enterprise" -}}
{{- end -}}
{{- $serviceType -}}
{{- end -}}

{{/*
Computed insights-agent memory limit, used when insights.resources.limits.memory is not
set: base + per-broker-size-class headroom (MiB) for the co-resident OTel collector.
Base = insights.resources.requests.memory when set, otherwise 256Mi.
*/}}
{{- define "insights.agentLimitMemory" -}}
{{- $deltas := dict "dev" 512 "prod1k" 1024 "prod10k" 2048 "prod100k" 4096 "prod200k" 5632 -}}
{{- if not (hasKey $deltas .Values.solace.size) -}}
{{- fail (printf "insights: cannot compute the agent memory limit for unknown solace.size %q; set insights.resources.limits.memory explicitly" .Values.solace.size) -}}
{{- end -}}
{{- $delta := int (get $deltas .Values.solace.size) -}}
{{- $requests := .Values.insights.resources.requests | default dict -}}
{{- $base := $requests.memory | default "256Mi" | toString -}}
{{- $baseMi := 0.0 -}}
{{- if hasSuffix "Gi" $base -}}{{- $baseMi = mulf (trimSuffix "Gi" $base | float64) 1024.0 -}}
{{- else if hasSuffix "Mi" $base -}}{{- $baseMi = trimSuffix "Mi" $base | float64 -}}
{{- else -}}{{- fail (printf "insights.resources.requests.memory must be specified in Mi or Gi, got %q" $base) -}}{{- end -}}
{{- printf "%dMi" (add (ceil $baseMi | int) $delta) -}}
{{- end -}}

{{/*
Computed insights-agent CPU limit (in cores), used when insights.resources.limits.cpu is
not set: base + per-broker-size-class headroom (millicores) for the co-resident OTel
collector. Base = insights.resources.requests.cpu when set, otherwise 200m.
*/}}
{{- define "insights.agentLimitCpu" -}}
{{- $deltas := dict "dev" 500 "prod1k" 500 "prod10k" 1000 "prod100k" 2000 "prod200k" 2000 -}}
{{- if not (hasKey $deltas .Values.solace.size) -}}
{{- fail (printf "insights: cannot compute the agent cpu limit for unknown solace.size %q; set insights.resources.limits.cpu explicitly" .Values.solace.size) -}}
{{- end -}}
{{- $delta := int (get $deltas .Values.solace.size) -}}
{{- $requests := .Values.insights.resources.requests | default dict -}}
{{- $base := $requests.cpu | default "200m" | toString -}}
{{- $baseM := 0.0 -}}
{{- if hasSuffix "m" $base -}}{{- $baseM = trimSuffix "m" $base | float64 -}}
{{- else -}}{{- $baseM = mulf ($base | float64) 1000.0 -}}{{- end -}}
{{- divf (add (ceil $baseM | int) $delta) 1000 -}}
{{- end -}}
