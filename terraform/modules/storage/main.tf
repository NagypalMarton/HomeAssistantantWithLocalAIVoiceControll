variable "storage_class_name" {
  description = "Storage class name"
  type        = string
}

variable "storage_type" {
  description = "Storage type (ssd, standard)"
  type        = string
}

# Storage Class for fast SSD
resource "kubernetes_storage_class" "fast_ssd" {
  metadata {
    name = var.storage_class_name
  }
  
  storage_provisioner = "kubernetes.io/gce-pd"  # Change based on cloud provider
  reclaim_policy      = "Retain"
  volume_binding_mode = "WaitForFirstConsumer"
  
  parameters = {
    type = "pd-ssd"  # Change based on cloud provider
    replication-type = "regional-pd"
  }
}

output "storage_class_name" {
  description = "Created storage class name"
  value       = kubernetes_storage_class.fast_ssd.metadata[0].name
}
