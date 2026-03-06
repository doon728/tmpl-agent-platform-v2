# Tool Gateway Contract (v1)

## Endpoint
POST /tools/invoke
Content-Type: application/json

## Request Body (v1)
{
  "contract_version": "v1",
  "tool_name": "<string>",
  "input": { "<tool specific json>" },
  "tenant_id": "<string|null>",
  "user_id": "<string|null>",
  "correlation_id": "<string|null>"
}

## Response Body (v1)
### Success
{
  "contract_version": "v1",
  "ok": true,
  "output": { "<tool specific json>" },
  "error": null
}

### Failure
{
  "contract_version": "v1",
  "ok": false,
  "output": null,
  "error": {
    "code": "<string>",
    "message": "<string>",
    "details": { }
  }
}
