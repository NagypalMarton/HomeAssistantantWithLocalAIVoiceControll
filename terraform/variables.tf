variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
  default     = "ha-llm-cluster"
}

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "gpu_node_count" {
  description = "Number of GPU nodes"
  type        = number
  default     = 2
}

variable "gpu_node_machine_type" {
  description = "Machine type for GPU nodes"
  type        = string
  default     = "n1-standard-8"
}

variable "gpu_type" {
  description = "GPU type (nvidia-tesla-t4, nvidia-tesla-v100, etc.)"
  type        = string
  default     = "nvidia-tesla-t4"
}

variable "gpu_count_per_node" {
  description = "Number of GPUs per node"
  type        = number
  default     = 1
}

variable "storage_class_name" {
  description = "Storage class name"
  type        = string
  default     = "fast-ssd"
}

variable "storage_type" {
  description = "Storage type (ssd, standard)"
  type        = string
  default     = "ssd"
}

variable "domain_name" {
  description = "Domain name for ingress"
  type        = string
  default     = "yourdomain.com"
}

variable "region" {
  description = "Cloud region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Cloud zone"
  type        = string
  default     = "us-central1-a"
}
