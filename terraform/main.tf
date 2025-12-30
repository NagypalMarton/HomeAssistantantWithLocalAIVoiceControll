terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# GPU Node Pool
module "gpu_nodes" {
  source = "./modules/gpu-nodes"
  
  cluster_name     = var.cluster_name
  node_count       = var.gpu_node_count
  node_machine_type = var.gpu_node_machine_type
  gpu_type         = var.gpu_type
  gpu_count        = var.gpu_count_per_node
}

# Storage provisioning
module "storage" {
  source = "./modules/storage"
  
  storage_class_name = var.storage_class_name
  storage_type       = var.storage_type
}

# Networking
module "networking" {
  source = "./modules/networking"
  
  cluster_name = var.cluster_name
  domain_name  = var.domain_name
}

# NVIDIA Device Plugin
resource "helm_release" "nvidia_device_plugin" {
  name       = "nvidia-device-plugin"
  repository = "https://nvidia.github.io/k8s-device-plugin"
  chart      = "nvidia-device-plugin"
  namespace  = "kube-system"
  
  set {
    name  = "nodeSelector.nvidia\\.com/gpu"
    value = "true"
  }
}

# Ingress NGINX Controller
resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  namespace  = "ingress-nginx"
  create_namespace = true
  
  set {
    name  = "controller.service.type"
    value = "LoadBalancer"
  }
}

# Cert Manager
resource "helm_release" "cert_manager" {
  name       = "cert-manager"
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  namespace  = "cert-manager"
  create_namespace = true
  
  set {
    name  = "installCRDs"
    value = "true"
  }
}

# HA-LLM Stack Namespace
resource "kubernetes_namespace" "ha_llm_system" {
  metadata {
    name = "ha-llm-system"
    labels = {
      name       = "ha-llm-system"
      monitoring = "enabled"
    }
  }
}

# Deploy HA-LLM Stack
resource "helm_release" "ha_llm_stack" {
  name       = "ha-llm-stack"
  chart      = "../helm/ha-llm-stack"
  namespace  = kubernetes_namespace.ha_llm_system.metadata[0].name
  
  values = [
    file("${path.module}/values-${var.environment}.yaml")
  ]
  
  depends_on = [
    helm_release.nvidia_device_plugin,
    helm_release.ingress_nginx,
    helm_release.cert_manager
  ]
}
