# Storage and Provenance

Artifact layout (incremental scaffold):
- `artifacts/datahub/raw/`: optional raw ingress payload snapshots / future source dumps
- `artifacts/datahub/records/`: canonical normalized record batches written by `LocalArtifactStorage`
- `artifacts/datahub/manifests/`: provenance manifests captured by `ManifestProvenanceTracker`
- `artifacts/datahub/quality/`: quality summaries / future validation snapshots
- `artifacts/tutorial/`: tutorial walkthrough + tutorial/source-specific reports

Every generated artifact should include strategy id, environment, and timestamp metadata.
