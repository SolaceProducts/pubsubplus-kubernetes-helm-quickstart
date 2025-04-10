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
