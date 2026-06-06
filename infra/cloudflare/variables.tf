variable "cloudflare_zone_id" {
  description = "Cloudflare zone id that fronts the production API hostname."
  type        = string
}

variable "api_hostname" {
  description = "Public hostname that receives Masao API traffic, for example api.masao.example.com."
  type        = string

  validation {
    condition     = length(trimspace(var.api_hostname)) > 0
    error_message = "api_hostname must not be empty."
  }
}

variable "chat_edge_requests_per_period" {
  description = "Maximum POST /api/chat requests per edge key during the period."
  type        = number
  default     = 60

  validation {
    condition     = var.chat_edge_requests_per_period > 0
    error_message = "chat_edge_requests_per_period must be greater than zero."
  }
}

variable "chat_edge_period_seconds" {
  description = "Cloudflare edge rate-limit counting period in seconds."
  type        = number
  default     = 60

  validation {
    condition     = var.chat_edge_period_seconds > 0
    error_message = "chat_edge_period_seconds must be greater than zero."
  }
}

variable "chat_edge_mitigation_timeout_seconds" {
  description = "How long Cloudflare should block a key after it exceeds the chat edge limit."
  type        = number
  default     = 60

  validation {
    condition     = var.chat_edge_mitigation_timeout_seconds > 0
    error_message = "chat_edge_mitigation_timeout_seconds must be greater than zero."
  }
}
