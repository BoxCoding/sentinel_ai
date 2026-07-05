# Sentinel AI — Google Cloud infrastructure

terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
  backend "gcs" {
    bucket = "sentinel-ai-tfstate"
    prefix = "prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------- APIs ----------
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com", "cloudbuild.googleapis.com", "aiplatform.googleapis.com",
    "bigquery.googleapis.com", "storage.googleapis.com", "firestore.googleapis.com",
    "pubsub.googleapis.com", "cloudscheduler.googleapis.com", "cloudfunctions.googleapis.com",
    "alloydb.googleapis.com", "secretmanager.googleapis.com", "documentai.googleapis.com",
    "speech.googleapis.com", "texttospeech.googleapis.com", "vision.googleapis.com",
    "logging.googleapis.com", "monitoring.googleapis.com", "artifactregistry.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# ---------- Storage ----------
resource "google_storage_bucket" "data" {
  name                        = "${var.project_id}-data"
  location                    = var.region
  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "knowledge_base" {
  name                        = "${var.project_id}-knowledge-base"
  location                    = var.region
  uniform_bucket_level_access = true
  versioning { enabled = true }
}

# ---------- BigQuery ----------
resource "google_bigquery_dataset" "sentinel" {
  dataset_id = "sentinel_ai"
  location   = var.region
}

# ---------- Pub/Sub ----------
resource "google_pubsub_topic" "topics" {
  for_each = toset(["sentinel-incidents", "sentinel-alerts", "sentinel-workflows"])
  name     = each.value
}

# ---------- Firestore ----------
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# ---------- AlloyDB ----------
resource "google_alloydb_cluster" "main" {
  cluster_id = "sentinel-alloydb"
  location   = var.region
  network_config { network = "projects/${var.project_id}/global/networks/default" }
}

resource "google_alloydb_instance" "primary" {
  cluster       = google_alloydb_cluster.main.name
  instance_id   = "sentinel-primary"
  instance_type = "PRIMARY"
  machine_config { cpu_count = 2 }
}

# ---------- Vertex AI Vector Search ----------
resource "google_vertex_ai_index" "kb" {
  display_name = "sentinel-knowledge-base"
  region       = var.region
  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.knowledge_base.name}/embeddings"
    config {
      dimensions                  = 768
      approximate_neighbors_count = 50
      distance_measure_type       = "COSINE_DISTANCE"
      algorithm_config {
        tree_ah_config { leaf_node_embedding_count = 500 }
      }
    }
  }
  index_update_method = "STREAM_UPDATE"
}

resource "google_vertex_ai_index_endpoint" "kb" {
  display_name            = "sentinel-kb-endpoint"
  region                  = var.region
  public_endpoint_enabled = true
}

# ---------- Service accounts & IAM (least privilege) ----------
resource "google_service_account" "backend" {
  account_id   = "sentinel-backend"
  display_name = "Sentinel backend (Cloud Run)"
}

resource "google_project_iam_member" "backend_roles" {
  for_each = toset([
    "roles/aiplatform.user", "roles/bigquery.dataEditor", "roles/bigquery.jobUser",
    "roles/datastore.user", "roles/pubsub.publisher", "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor", "roles/logging.logWriter",
    "roles/monitoring.metricWriter", "roles/documentai.apiUser",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# ---------- Secret Manager ----------
resource "google_secret_manager_secret" "secrets" {
  for_each  = toset(["sentinel-jwt-secret", "sentinel-maps-key"])
  secret_id = each.value
  replication { auto {} }
}

# ---------- Cloud Scheduler: decision cycle every 5 minutes ----------
resource "google_cloud_scheduler_job" "decision_cycle" {
  name      = "sentinel-decision-cycle"
  schedule  = "*/5 * * * *"
  time_zone = "Etc/UTC"
  http_target {
    http_method = "POST"
    uri         = "${var.backend_url}/api/v1/agents/decision-cycle"
    oidc_token { service_account_email = google_service_account.backend.email }
  }
}

# ---------- Cloud Monitoring: alert on high risk + service errors ----------
resource "google_monitoring_alert_policy" "backend_errors" {
  display_name = "Sentinel backend 5xx rate"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run 5xx > 1%"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "300s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  notification_channels = var.alert_channels
}
