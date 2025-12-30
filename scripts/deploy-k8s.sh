#!/bin/bash
# Kubernetes deployment script

set -e

ENVIRONMENT="${1:-dev}"
NAMESPACE="ha-llm-system"

echo "=== Deploying HA-LLM Stack to $ENVIRONMENT ==="

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "Error: Helm is not installed"
    exit 1
fi

# Check cluster connection
echo "Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✓ Connected to cluster"

# Create namespace
echo "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply resource quotas
echo "Applying resource quotas..."
kubectl apply -f ../kubernetes/namespaces/resourcequota.yaml

# Install NVIDIA GPU operator (if not already installed)
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "Checking for GPU operator..."
    if ! kubectl get pods -n gpu-operator &> /dev/null; then
        echo "Installing NVIDIA GPU Operator..."
        helm repo add nvidia https://nvidia.github.io/gpu-operator
        helm repo update
        helm install gpu-operator nvidia/gpu-operator \
          --namespace gpu-operator \
          --create-namespace \
          --wait
    fi
fi

# Deploy with Helm
echo "Deploying with Helm..."
helm upgrade --install ha-llm-stack \
  ../helm/ha-llm-stack \
  --namespace $NAMESPACE \
  --values ../helm/ha-llm-stack/values-${ENVIRONMENT}.yaml \
  --wait \
  --timeout 10m

# Check deployment status
echo "Checking deployment status..."
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ha-llm-stack -n $NAMESPACE --timeout=300s

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "To check logs:"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=home-assistant"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=ollama"
echo ""
echo "To access services:"
echo "  kubectl port-forward -n $NAMESPACE svc/home-assistant 8123:8123"
echo "  kubectl port-forward -n $NAMESPACE svc/ollama 11434:11434"
