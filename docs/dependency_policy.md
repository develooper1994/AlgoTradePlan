# Third-Party Dependency Policy

Add a new package only if:
- standard library is insufficient
- maintenance and security posture are acceptable
- license is compatible with repository license

Required checks:
- vulnerability scan
- license review
- changelog entry

## Allowlist (enforced by `scripts/security_check.py`)
- `pandas`
- `scikit-learn`
- `mkdocs`
- `mkdocs-material`

To add a new dependency:
1. open an issue justifying the addition (security, license, maintenance posture)
2. add the package to the allowlist in `scripts/security_check.py`
3. declare the dependency with an explicit `>=` lower bound in `pyproject.toml`
4. record the addition in the changelog
5. re-run `python scripts/security_check.py --repo-root .`
