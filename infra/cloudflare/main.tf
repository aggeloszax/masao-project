locals {
  chat_api_expression = "(http.host eq \"${var.api_hostname}\" and http.request.method eq \"POST\" and http.request.uri.path eq \"/api/chat\")"
  chat_rate_limit_response = jsonencode({
    detail = "Too many chat requests. Please wait before trying again."
  })
}

resource "cloudflare_ruleset" "masao_chat_edge_rate_limit" {
  zone_id     = var.cloudflare_zone_id
  name        = "Masao API edge rate limiting"
  description = "Cloudflare edge rate limiting for Masao public API traffic."
  kind        = "zone"
  phase       = "http_ratelimit"

  rules = [{
    ref         = "masao_chat_edge_rate_limit"
    description = "Rate limit POST /api/chat by client IP before FastAPI"
    expression  = local.chat_api_expression
    action      = "block"

    action_parameters = {
      response = {
        status_code  = 429
        content      = local.chat_rate_limit_response
        content_type = "application/json"
      }
    }

    ratelimit = {
      characteristics     = ["cf.colo.id", "ip.src"]
      period              = var.chat_edge_period_seconds
      requests_per_period = var.chat_edge_requests_per_period
      mitigation_timeout  = var.chat_edge_mitigation_timeout_seconds
      requests_to_origin  = true
    }
  }]
}
