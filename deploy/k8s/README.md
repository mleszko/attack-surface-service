# Kubernetes deployment

This directory contains baseline Kubernetes manifests for the service:

- `deployment.yaml` - application deployment with liveness/readiness probes
- `service.yaml` - internal ClusterIP service
- `kustomization.yaml` - apply both resources together

## Usage

Build and publish an image to your registry, then update `deployment.yaml` image reference.

Apply:

```bash
kubectl apply -k deploy/k8s
```

Check rollout:

```bash
kubectl rollout status deployment/attack-surface-service
kubectl get pods -l app=attack-surface-service
kubectl get svc attack-surface-service
```
