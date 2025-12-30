# Setup Guide

Complete installation and configuration guide for the Home Assistant + Ollama LLM stack.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Kubernetes Setup](#kubernetes-setup)
4. [GPU Configuration](#gpu-configuration)
5. [Monitoring Setup](#monitoring-setup)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements

**Local Development:**
- CPU: 4+ cores
- RAM: 16GB minimum, 32GB recommended
- Storage: 100GB+ free space
- GPU: NVIDIA GPU (optional for dev, required for prod)

**Production:**
- Kubernetes cluster with 3+ nodes
- GPU nodes: NVIDIA Tesla T4, V100, A100, or better
- Storage: NFS or block storage for PersistentVolumes
- Network: Load balancer support

### Software Requirements

```bash
# Docker
docker --version  # 24.0+
docker-compose --version  # 2.20+

# Kubernetes tools
kubectl version --client  # 1.28+
helm version  # 3.13+

# Terraform
terraform version  # 1.5+

# NVIDIA drivers (for GPU support)
nvidia-smi
```

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd HomeAssistantantWithLocalAIVoiceControll
```

### 2. Environment Configuration

Create `.env` file in the project root:

```bash
# Zabbix
ZABBIX_DB_PASSWORD=secure_password_here

# Home Assistant
HA_EXTERNAL_URL=http://localhost:8123
```

### 3. Run Setup Script

```bash
chmod +x scripts/setup-local.sh
./scripts/setup-local.sh
```

This script will:
- Check prerequisites
- Create necessary directories
- Start Docker containers
- Pull Ollama models
- Configure services

### 4. Verify Installation

```bash
# Check running containers
docker ps

# Test Home Assistant
curl http://localhost:8123/api/

# Test Ollama
curl http://localhost:11434/api/tags

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### 5. Access Services

- **Home Assistant**: http://localhost:8123
  - Initial setup wizard will guide you
  
- **Zabbix**: http://localhost:8080
  - Username: `Admin`
  - Password: `zabbix`
  
- **Ollama API**: http://localhost:11434

## Kubernetes Setup

### 1. Prepare Cluster

Ensure your cluster has:
- Storage class configured
- Ingress controller installed
- GPU operator (for production)

### 2. Configure kubectl

```bash
export KUBECONFIG=~/.kube/config
kubectl cluster-info
```

### 3. Install Prerequisites

```bash
# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

### 4. Deploy with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="environments/dev/terraform.tfvars"

# Apply (development)
terraform apply -var-file="environments/dev/terraform.tfvars"

# Apply (production)
terraform apply -var-file="environments/prod/terraform.tfvars"
```

### 5. Deploy with Helm

```bash
# Development
helm install ha-llm-stack ./helm/ha-llm-stack \
  --namespace ha-llm-system \
  --create-namespace \
  --values ./helm/ha-llm-stack/values-dev.yaml

# Production
helm install ha-llm-stack ./helm/ha-llm-stack \
  --namespace ha-llm-system \
  --create-namespace \
  --values ./helm/ha-llm-stack/values-prod.yaml
```

Or use the deployment script:

```bash
./scripts/deploy-k8s.sh dev    # or prod
```

## GPU Configuration

### 1. Install NVIDIA Drivers on Nodes

```bash
# On each GPU node
sudo apt-get update
sudo apt-get install -y nvidia-driver-535
sudo reboot
```

### 2. Install NVIDIA Container Toolkit

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 3. Install NVIDIA Device Plugin

```bash
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

Or with Helm:

```bash
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm install nvdp nvdp/nvidia-device-plugin \
  --namespace kube-system \
  --set nodeSelector."nvidia\.com/gpu"=true
```

### 4. Verify GPU Availability

```bash
kubectl get nodes -o json | jq '.items[].status.capacity'
```

Look for `nvidia.com/gpu` in the output.

## Monitoring Setup

### 1. Deploy Zabbix

```bash
cd monitoring/zabbix
docker-compose up -d
```

### 2. Configure Zabbix

1. Access Zabbix web interface: http://localhost:8080
2. Login with Admin/zabbix
3. Import template: Configuration → Templates → Import
4. Upload `monitoring/zabbix/templates/ha-llm-template.json`
5. Add hosts and link templates

### 3. Configure External Scripts

```bash
# Make scripts executable
chmod +x monitoring/zabbix/scripts/*.sh

# Copy to Zabbix container
docker cp monitoring/zabbix/scripts/ zabbix-server:/usr/lib/zabbix/externalscripts/
```

### 4. Setup Alerts

Configure notification settings in Zabbix:
- Administration → Media types
- Setup email, Slack, or other integrations
- Configure user notifications

## Troubleshooting

### Docker Issues

```bash
# Check container logs
docker-compose -f docker/docker-compose.yml logs -f [service-name]

# Restart services
docker-compose -f docker/docker-compose.yml restart

# Clean up and restart
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

### Kubernetes Issues

```bash
# Check pod status
kubectl get pods -n ha-llm-system

# View pod logs
kubectl logs -n ha-llm-system [pod-name]

# Describe pod for events
kubectl describe pod -n ha-llm-system [pod-name]

# Check resource usage
kubectl top nodes
kubectl top pods -n ha-llm-system
```

### GPU Issues

```bash
# Check GPU availability on host
nvidia-smi

# Check GPU device plugin
kubectl get pods -n kube-system | grep nvidia

# Check GPU allocation
kubectl describe node [node-name] | grep -A 10 "Allocated resources"
```

### Ollama Issues

```bash
# Test Ollama API
curl http://localhost:11434/api/tags

# Pull models manually
docker exec ollama ollama pull llama3:8b

# Check Ollama logs
docker logs ollama
# or
kubectl logs -n ha-llm-system -l app.kubernetes.io/component=ollama
```

### Home Assistant Issues

```bash
# Check Home Assistant logs
docker logs homeassistant
# or
kubectl logs -n ha-llm-system -l app.kubernetes.io/component=home-assistant

# Access configuration
docker exec -it homeassistant /bin/bash
cat /config/configuration.yaml
```

## Next Steps

- [Deployment Guide](DEPLOYMENT.md) - Production deployment strategies
- [User Guide](USER_GUIDE.md) - Managing multi-user environments
- [Architecture](ARCHITECTURE.md) - Understanding system components
