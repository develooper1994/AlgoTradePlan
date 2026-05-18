# Environment and Secrets Switching

Supported environments:
- `dev`
- `paper`
- `live`

Use schema `schemas/runtime_config.schema.json` to validate runtime config payloads.
Secrets must be injected via environment variables or external secret stores; never commit them.
