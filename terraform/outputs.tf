output "cluster_name" {
  description = "Kubernetes cluster name"
  value       = var.cluster_name
}

output "ingress_nginx_ip" {
  description = "Ingress NGINX LoadBalancer IP"
  value       = helm_release.ingress_nginx.status
}

output "ha_llm_namespace" {
  description = "HA-LLM system namespace"
  value       = kubernetes_namespace.ha_llm_system.metadata[0].name
}

output "gpu_node_count" {
  description = "Number of GPU nodes"
  value       = var.gpu_node_count
}

output "home_assistant_url" {
  description = "Home Assistant URL"
  value       = "https://ha.${var.domain_name}"
}

output "ollama_url" {
  description = "Ollama API URL"
  value       = "https://ollama.${var.domain_name}"
}
