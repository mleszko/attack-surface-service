# Deployment

This project includes two deployment-friendly options out of the box:

- Docker Compose for local/staging environments
- Kubernetes manifests for cluster deployments

## Docker Compose

From repository root:

```bash
docker compose up --build
```

Default settings in `docker-compose.yml`:

- `ENV_PATH=tests/cloud.json`
- `LOG_FORMAT=json`
- published port `8000 -> 80`
- healthcheck calls `GET /healthz`

Stop:

```bash
docker compose down
```

## Kubernetes

Baseline manifests are in `deploy/k8s`:

- `deployment.yaml`
- `service.yaml`
- `kustomization.yaml`

Apply:

```bash
kubectl apply -k deploy/k8s
```

The deployment includes:

- liveness probe: `GET /healthz`
- readiness probe: `GET /readyz`
- configurable environment variables (`ENV_PATH`, `LOG_FORMAT`)

Update the image reference in `deploy/k8s/deployment.yaml` before applying in real environments.
