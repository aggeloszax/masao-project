output "chat_edge_rate_limit_rule_ref" {
  description = "Stable ref for the Masao chat edge rate limiting rule."
  value       = "masao_chat_edge_rate_limit"
}

output "chat_edge_rate_limit_expression" {
  description = "Cloudflare filter expression applied to the chat endpoint."
  value       = local.chat_api_expression
}
