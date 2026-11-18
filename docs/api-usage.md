# Orbit API usage

The Orbit REST API base URL is **https://api.orbit.example/v1**. Send requests over HTTPS with a personal access token in the `Authorization: Bearer` header. Create or revoke tokens at **Profile → Developer tokens**. Tokens are shown only once and should be stored as secrets.

To list projects, call `GET /projects`. To create an issue, call `POST /projects/{project_id}/issues` with a JSON body containing `title` (required, up to 200 characters) and optional `description` and `assignee_id`. A successful create returns HTTP 201 and the new issue object.

Example:

```http
GET /v1/projects HTTP/1.1
Host: api.orbit.example
Authorization: Bearer YOUR_TOKEN
```

The API allows 120 requests per minute per token. Responses include `X-RateLimit-Remaining`; when limited, the API returns HTTP 429 and a `Retry-After` header in seconds. List endpoints return up to 50 items per page and support `?page=2`.

Timestamps use ISO 8601 UTC. Common errors are 401 for an invalid token, 403 for insufficient project access, 404 for a missing resource, and 422 for invalid request fields. API version `v1` is supported through at least December 2027; breaking changes receive a new version.
