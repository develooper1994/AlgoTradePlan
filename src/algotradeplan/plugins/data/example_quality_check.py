"""Example quality gate for normalized data records."""

from __future__ import annotations

from src.algotradeplan.plugins.data.contracts import DataRecord, QualityReport


class RequiredFieldsQualityPlugin:
    plugin_id = "required_fields_quality"

    def validate(self, records: list[DataRecord]) -> QualityReport:
        checks = ["records_present", "required_fields"]
        issues: list[str] = []

        if not records:
            issues.append("No records fetched for request.")

        for index, record in enumerate(records):
            if not record.key:
                issues.append(f"Record {index} missing key.")
            if not record.observed_at:
                issues.append(f"Record {index} missing observed_at.")
            if not record.domain or not record.source or not record.asset_type:
                issues.append(f"Record {index} missing domain/source/asset_type metadata.")

        return QualityReport(passed=not issues, checks=checks, issues=issues)
