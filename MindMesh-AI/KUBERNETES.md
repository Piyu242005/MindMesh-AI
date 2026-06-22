<div align="center">
  <img src="assets/logo.png" width="180">
</div>

# Kubernetes Deployment Guide

This document describes how to deploy MindMesh AI onto a Kubernetes cluster.

## Prerequisites
- A running Kubernetes cluster (e.g., Minikube, EKS, GKE, AKS)
- `kubectl` configured to interact with your cluster
- NGINX Ingress Controller installed in the cluster
- Cert-Manager installed for automatic TLS (Let's Encrypt)

## Deployment Steps

1. **Update Secrets:**
   Update `k8s/secret.yaml` with your base64 encoded API keys. Do not commit real keys to source control!

2. **Apply Manifests:**
   Deploy the entire application using Kustomize:
   ```bash
   kubectl apply -k k8s/
   ```
   Or apply directly:
   ```bash
   kubectl apply -f k8s/
   ```

## Useful Commands

### Check Pods
```bash
kubectl get pods -n mindmesh
```

### Check Services
```bash
kubectl get svc -n mindmesh
```

### Check Ingress
```bash
kubectl get ingress -n mindmesh
```

### Rolling Restart
To force a rolling restart (e.g., after updating an image or config):
```bash
kubectl rollout restart deployment/mindmesh-ai -n mindmesh
```

### View Logs
```bash
kubectl logs -l app=mindmesh-ai -n mindmesh -f
```

## Monitoring
The deployment exposes Prometheus metrics on port `8000` at `/metrics` (assuming the FastAPI app exports them). The deployment includes the standard `prometheus.io/scrape` annotations.

## Autoscaling
The deployment includes a Horizontal Pod Autoscaler (HPA) configured to scale between 2 and 10 replicas based on 70% CPU or 75% Memory utilization.
