#!/bin/bash
# Script to provision a new user namespace with HA + Ollama

set -e

USERNAME="${1}"

if [ -z "$USERNAME" ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

NAMESPACE="ha-llm-user-${USERNAME}"

echo "=== Provisioning user: $USERNAME ==="

# Create namespace
echo "Creating namespace: $NAMESPACE"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: $NAMESPACE
  labels:
    user: "$USERNAME"
    monitoring: enabled
EOF

# Apply resource quota
echo "Applying resource quota..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: user-quota
  namespace: $NAMESPACE
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    requests.nvidia.com/gpu: "1"
    limits.cpu: "8"
    limits.memory: 16Gi
    limits.nvidia.com/gpu: "1"
    persistentvolumeclaims: "3"
    requests.storage: "100Gi"
EOF

# Deploy HA-LLM stack for user
echo "Deploying HA-LLM stack..."
helm upgrade --install "ha-llm-${USERNAME}" \
  ../helm/ha-llm-stack \
  --namespace $NAMESPACE \
  --set global.domain="${USERNAME}.yourdomain.com" \
  --wait

# Create service account and RBAC
echo "Creating service account..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: $USERNAME
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ${USERNAME}-admin
  namespace: $NAMESPACE
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
- kind: ServiceAccount
  name: $USERNAME
  namespace: $NAMESPACE
EOF

# Get access credentials
echo "Generating kubeconfig..."
./generate-kubeconfig.sh $USERNAME $NAMESPACE > "${USERNAME}-kubeconfig.yaml"

echo ""
echo "=== User provisioned successfully ==="
echo ""
echo "Namespace: $NAMESPACE"
echo "Kubeconfig: ${USERNAME}-kubeconfig.yaml"
echo ""
echo "Access URLs:"
echo "  Home Assistant: https://ha.${USERNAME}.yourdomain.com"
echo "  Ollama API: https://ollama.${USERNAME}.yourdomain.com"
