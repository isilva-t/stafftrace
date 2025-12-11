variable "project_id"  {
	description = "GCP Project ID"
	type		= string
}

variable "region" {
	description = "GCP Region"
	type		= string
	default		= "europe-west1"
}

variable "zone" {
	description	= "GCP Zone for GKE cluster"
	type		= string
	default		= "europe-west1-b"
}

variable "cluster_name" {
	description = "Name of the GKE cluster"
	type		= string
	default		= "stafftrace"
}

variable "node_count" {
	description	= "Number of nodes in the node pool"
	type		= number
	default		= 2
}

variable "machine_type" {
	description = "Machine type for GKE nodes"
	type		= string
	default		= "e2-small"
}

variable "disk_size_gb" {
	description = "disk size in GB for each node"
	type		= number
	default		= 15
}
