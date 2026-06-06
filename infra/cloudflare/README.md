# Masao Cloudflare Edge Rate Limiting

This Terraform config creates a Cloudflare WAF rate limiting rule for:

```text
POST /api/chat
```

The rule blocks abusive traffic at the Cloudflare edge before it reaches FastAPI.
The backend Redis limiter remains the inner protection layer.

## Rule

```text
http.host eq var.api_hostname
http.request.method eq "POST"
http.request.uri.path eq "/api/chat"
```

Rate key:

```text
cf.colo.id + ip.src
```

Default threshold:

```text
60 requests / 60 seconds
mitigation timeout: 60 seconds
```

Cloudflare returns:

```json
{"detail":"Too many chat requests. Please wait before trying again."}
```

with status `429`.

## Required Cloudflare Access

Use a Cloudflare API token with at least:

```text
Zone WAF Write
```

The token is supplied through the standard Cloudflare provider environment variable:

```powershell
$env:CLOUDFLARE_API_TOKEN="..."
```

Do not commit tokens or `.tfvars` files containing real zone/account data.

## Apply

```powershell
cd infra/cloudflare
Copy-Item terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with the real zone id and API hostname.
terraform init
terraform plan
terraform apply
```

## Existing Cloudflare Rate Limit Rules

Cloudflare supports one zone entry point ruleset per phase (`http_ratelimit`).
If the zone already has rate limiting rules, import the existing ruleset into Terraform
and merge this rule into that resource before applying.

Do not apply this resource blindly over an existing manually managed ruleset.

## Production Notes

- Keep the backend Redis limiter enabled with `RATE_LIMIT_BACKEND=redis`.
- Keep this edge rule slightly broader than the backend device limiter because many guests can share one public IP.
- Review Cloudflare analytics after launch and tune `chat_edge_requests_per_period` if legitimate traffic is blocked.
