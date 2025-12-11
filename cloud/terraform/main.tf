terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}


# GKE cluster
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone

  # we can't create a cluster with no nod pool defined
  # but we wanto to only use separately managed node pools.
  # so, we create the smallest possible default node pool
  # and immediately delete it
  remove_default_node_pool = true
  initial_node_count       = 1

  # disable deletion protecion for easier testing
  deletion_protection = false
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "default-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  node_config {
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb

    # Google recommends custom service accounts 
    # that have cloud-platform scope and permissions 
    # granted via IAM Roles.
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    labels = {
      environment = "production"
      managed_by  = "terraform"
    }

    tags = ["gke-node", "stafftrace"]
  }
}

resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "Github actions ci/cd"
  description  = "service account for github actions to deploy to gke"
}


# IAM role - container developer
resource "google_project_iam_member" "container_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# IAM role - storage admin for gcr
resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# IAM role - artifact registry writer
resource "google_project_iam_member" "artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

