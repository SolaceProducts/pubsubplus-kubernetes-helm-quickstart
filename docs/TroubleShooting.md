# Solace Event Router Kubernetes deployment Troubleshooting Tips

## How to determine a healthy deployment

## How to see Events

## How to see Logs

## Solace event broker troubleshooting

### General troubleshooting hints
https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/

### Pods stuck not enough resources

-> Increase K8S resources

### Pods stuck no storage

=> have a storage or use ephemeral (not for Production!)

### Pods stuck in CrashLoopBackoff or Failed

=> increase the Liveliness probe timeout and retry

### Security constraints

=> ensure adequate RBAC for your roles
=> open up network access to the k8s aAPI

