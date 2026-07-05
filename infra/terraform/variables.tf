variable "project_id" {
  type    = string
  default = "sentinel-ai-hackathon"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "backend_url" {
  type        = string
  description = "Cloud Run backend URL (set after first deploy)"
  default     = "https://sentinel-backend-placeholder.a.run.app"
}

variable "alert_channels" {
  type        = list(string)
  description = "Cloud Monitoring notification channel IDs"
  default     = []
}
