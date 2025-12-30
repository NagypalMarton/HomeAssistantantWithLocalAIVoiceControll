variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
}

variable "domain_name" {
  description = "Domain name for ingress"
  type        = string
}

# Network Policy for HA-LLM namespace
resource "kubernetes_network_policy" "ha_llm_policy" {
  metadata {
    name      = "ha-llm-network-policy"
    namespace = "ha-llm-system"
  }
  
  spec {
    pod_selector {}
    
    policy_types = ["Ingress", "Egress"]
    
    ingress {
      from {
        namespace_selector {
          match_labels = {
            name = "ingress-nginx"
          }
        }
      }
    }
    
    egress {
      to {
        pod_selector {}
      }
    }
  }
}

output "network_policy_name" {
  description = "Network policy name"
  value       = kubernetes_network_policy.ha_llm_policy.metadata[0].name
}
