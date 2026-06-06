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
set: a fixed agent base (256Mi) plus a per-broker-size-class headroom (MiB) for the
co-resident OTel collector. The base is fixed (not the requests value) so the limit is a
stable per-size value — this lets operators run Guaranteed QoS by setting requests equal to
this value and leaving limits unset. If requests.memory exceeds base + headroom, the limit
is raised to the request so the manifest stays valid (limit >= request).
*/}}
{{- define "insights.agentLimitMemory" -}}
{{- $deltas := dict "dev" 512 "prod1k" 1024 "prod10k" 2048 "prod100k" 4096 "prod200k" 5632 -}}
{{- if not (hasKey $deltas .Values.solace.size) -}}
{{- fail (printf "insights: cannot compute the agent memory limit for unknown solace.size %q; set insights.resources.limits.memory explicitly" .Values.solace.size) -}}
{{- end -}}
{{- $computed := add 256 (int (get $deltas .Values.solace.size)) -}}
{{- $requests := .Values.insights.resources.requests | default dict -}}
{{- $req := $requests.memory | default "256Mi" | toString -}}
{{- $reqMi := 0.0 -}}
{{- if hasSuffix "Gi" $req -}}{{- $reqMi = mulf (trimSuffix "Gi" $req | float64) 1024.0 -}}
{{- else if hasSuffix "Mi" $req -}}{{- $reqMi = trimSuffix "Mi" $req | float64 -}}
{{- else -}}{{- fail (printf "insights.resources.requests.memory must be specified in Mi or Gi, got %q" $req) -}}{{- end -}}
{{- printf "%dMi" (max (ceil $reqMi | int) $computed) -}}
{{- end -}}

{{/*
Computed insights-agent CPU limit (in cores), used when insights.resources.limits.cpu is
not set: a fixed agent base (200m) plus a per-broker-size-class headroom (millicores) for
the co-resident OTel collector. The base is fixed (not the requests value); if requests.cpu
exceeds base + headroom, the limit is raised to the request (limit >= request).
*/}}
{{- define "insights.agentLimitCpu" -}}
{{- $deltas := dict "dev" 500 "prod1k" 500 "prod10k" 1000 "prod100k" 2000 "prod200k" 2000 -}}
{{- if not (hasKey $deltas .Values.solace.size) -}}
{{- fail (printf "insights: cannot compute the agent cpu limit for unknown solace.size %q; set insights.resources.limits.cpu explicitly" .Values.solace.size) -}}
{{- end -}}
{{- $computed := add 200 (int (get $deltas .Values.solace.size)) -}}
{{- $requests := .Values.insights.resources.requests | default dict -}}
{{- $req := $requests.cpu | default "200m" | toString -}}
{{- $reqM := 0.0 -}}
{{- if hasSuffix "m" $req -}}{{- $reqM = trimSuffix "m" $req | float64 -}}
{{- else -}}{{- $reqM = mulf ($req | float64) 1000.0 -}}{{- end -}}
{{- divf (max (ceil $reqM | int) $computed) 1000 -}}
{{- end -}}

{{/*
Parse a Kubernetes memory quantity (Mi or Gi) to an integer number of MiB.
Usage: include "insights.memToMi" (dict "v" "512Mi")
*/}}
{{- define "insights.memToMi" -}}
{{- $s := .v | toString -}}
{{- if hasSuffix "Gi" $s -}}{{- mulf (trimSuffix "Gi" $s | float64) 1024.0 | int -}}
{{- else if hasSuffix "Mi" $s -}}{{- trimSuffix "Mi" $s | float64 | int -}}
{{- else -}}{{- fail (printf "insights memory values must be specified in Mi or Gi, got %q" $s) -}}{{- end -}}
{{- end -}}

{{/*
INSIGHTS_AGENT_GOMEMLIMIT for the co-resident OTel collector (forwarding mode only),
used when the operator has not set it explicitly. 80% of the memory headroom allotted to
the collector: the effective agent memory limit minus the fixed agent base (256Mi). The
effective limit is insights.resources.limits.memory when set, otherwise the computed limit
(base + per-solace.size headroom), so this reduces to 80% of that headroom. It is measured
from the fixed base (not requests) so setting requests == limits does not zero the headroom.
Fails if the effective limit is at or below the base.
*/}}
{{- define "insights.agentGomemLimit" -}}
{{- $limits := .Values.insights.resources.limits | default dict -}}
{{- $effLimit := "" -}}
{{- if $limits.memory -}}{{- $effLimit = $limits.memory -}}{{- else -}}{{- $effLimit = (include "insights.agentLimitMemory" .) -}}{{- end -}}
{{- $limMi := int (include "insights.memToMi" (dict "v" $effLimit)) -}}
{{- $headroom := sub $limMi 256 -}}
{{- if le $headroom 0 -}}
{{- fail "insights: cannot derive INSIGHTS_AGENT_GOMEMLIMIT because insights.resources.limits.memory is at or below the agent base (256Mi); set INSIGHTS_AGENT_GOMEMLIMIT explicitly or raise the limit" -}}
{{- end -}}
{{- printf "%dMiB" (div (mul $headroom 80) 100) -}}
{{- end -}}
