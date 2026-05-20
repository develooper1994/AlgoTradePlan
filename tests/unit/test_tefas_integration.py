from __future__ import annotations

import json
import os
import stat
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.generate_data_coverage_doc import generate as generate_data_coverage_doc
from src.algotradeplan.data import DataHub
from src.algotradeplan.data.normalize import normalize_dataset
from src.algotradeplan.research import PreflightChecker


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _write_fake_tefas_cli(path: Path) -> None:
    script = textwrap.dedent(
        """\
        #!/usr/bin/env python3
        import json
        import sys

        args = sys.argv[1:]
        op = ""
        if "--operation" in args:
            op = args[args.index("--operation") + 1]
        elif "query-operation" in args and len(args) >= 2:
            op = args[1]
        payloads = {
            "fonFiyatBilgiGetir": {"resultList": [{"fonKodu": "AFT", "fonUnvan": "AFT Fonu", "tarih": "2026-05-19", "fiyat": "12.34", "dovizCinsi": "TRY"}]},
            "fonBilgiGetir": {"resultList": [{"fonKodu": "AFT", "fonUnvan": "AFT Fonu", "isin_kodu": "TRYAFT000001", "kategori": "Hisse Senedi Fonu"}]},
            "fonProfilDtyGetir": {"resultList": [{"fonKodu": "AFT", "fon_risk_degeri": 6, "yatirimci_sayisi": 1200, "fon_toplam_deger_tl": 1234567}]},
            "fonDetayGetir": {"resultList": [{"fonKodu": "AFT", "kap_bilgi_adresi": "https://kap.org/AFT", "platform_islem_goruyor": True}]},
            "fonGetiriBazliBilgiGetir": {"resultList": [{"fonKodu": "AFT", "getiri_1a": 1.1, "getiri_3a": 3.3, "getiri_6a": 6.6, "getiri_1y": 12.1}]},
            "fonTurDnmGetiriGetir": {"resultList": [{"fonKodu": "AFT", "getiri_3y": 45.0, "getiri_5y": 80.0}]},
            "dagilimSiraliGetirT": {"resultList": [{"fonKodu": "AFT", "varlikTuru": "Hisse Senedi", "oran": 70.5}]}
        }
        print(json.dumps(payloads.get(op, {"resultList": []})))
        """
    )
    path.write_text(script, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class TefasIntegrationTest(unittest.TestCase):
    def test_tefas_capability_exists(self) -> None:
        hub = DataHub()
        summary = hub.source_summary("tefas_public")
        self.assertEqual(summary["implementation_status"], "partial")
        self.assertEqual(summary["dataset_statuses"]["fund_nav"], "partial")
        self.assertEqual(summary["dataset_statuses"]["fund_profile"], "partial")

    def test_tefas_missing_dependency_reports_graceful_issue(self) -> None:
        with patch.dict(os.environ, {"TEFAS_CLI_BIN": "", "TEFAS_FFI_LIB": ""}, clear=False):
            hub = DataHub()
            result = hub.ingest(
                source="tefas_public",
                symbol="AFT",
                datasets=["fund_nav", "fund_profile"],
                allow_partial=True,
                store=False,
            )
        reasons = {issue["reason"] for issue in result.source_issues}
        self.assertIn("optional_dependency_missing:tefas-cli", reasons)
        self.assertEqual(result.dataset_coverage["fund_nav"], 0)
        self.assertEqual(result.dataset_coverage["fund_profile"], 0)

    def test_tefas_fake_cli_ingest_and_normalize(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cli_path = Path(tmp_dir) / "fake_tefas_cli.py"
            _write_fake_tefas_cli(cli_path)
            with patch.dict(os.environ, {"TEFAS_CLI_BIN": str(cli_path), "TEFAS_FFI_LIB": ""}, clear=False):
                hub = DataHub()
                result = hub.ingest(
                    source="tefas_public",
                    symbol="AFT",
                    datasets=["fund_nav", "fund_profile", "fund_return", "fund_allocation"],
                    allow_partial=True,
                    store=False,
                )
        self.assertGreater(result.dataset_coverage["fund_nav"], 0)
        self.assertGreater(result.dataset_coverage["fund_profile"], 0)
        self.assertGreater(result.dataset_coverage["fund_return"], 0)
        self.assertGreater(result.dataset_coverage["fund_allocation"], 0)
        self.assertEqual(result.normalized["fund_nav"][0]["fund_code"], "AFT")
        self.assertIn("risk_value", result.normalized["fund_profile"][0])
        self.assertIn("return_1m_pct", result.normalized["fund_return"][0])
        self.assertIn("asset_type", result.normalized["fund_allocation"][0])

    def test_tefas_normalization_with_fixtures(self) -> None:
        nav_payload = json.loads((FIXTURES_DIR / "tefas_fund_nav.json").read_text(encoding="utf-8"))
        profile_payload = json.loads((FIXTURES_DIR / "tefas_fund_profile.json").read_text(encoding="utf-8"))
        return_payload = json.loads((FIXTURES_DIR / "tefas_fund_return.json").read_text(encoding="utf-8"))
        allocation_payload = json.loads((FIXTURES_DIR / "tefas_fund_allocation.json").read_text(encoding="utf-8"))

        nav = normalize_dataset("fund_nav", "tefas_public", "AFT", nav_payload)
        profile = normalize_dataset("fund_profile", "tefas_public", "AFT", profile_payload)
        returns = normalize_dataset("fund_return", "tefas_public", "AFT", return_payload)
        allocation = normalize_dataset("fund_allocation", "tefas_public", "AFT", allocation_payload)

        self.assertEqual(nav[0]["fund_code"], "AFT")
        self.assertEqual(profile[0]["isin"], "TRYAFT000001")
        self.assertEqual(returns[0]["return_1m_pct"], 2.1)
        self.assertEqual(allocation[0]["asset_type"], "Hisse Senedi")

    def test_recommend_and_preflight_for_tefas(self) -> None:
        hub = DataHub()
        recommendations = hub.recommend_sources("tefas_fund_screener", allow_api_key=False)
        self.assertEqual(recommendations[0]["source"], "tefas_public")
        with patch.dict(os.environ, {"TEFAS_CLI_BIN": "", "TEFAS_FFI_LIB": ""}, clear=False):
            preflight = PreflightChecker(hub).check(
                source="tefas_public",
                symbol="AFT",
                datasets=["fund_nav", "fund_profile"],
                strategy="fund_momentum",
                allow_api_key=False,
            )
        self.assertFalse(preflight.can_run)
        self.assertIn("optional_dependency_missing:tefas-cli", preflight.blocking_issues)
        self.assertIn("Build tefas-cli and set TEFAS_CLI_BIN or TEFAS_FFI_LIB.", preflight.suggestions)

    def test_coverage_doc_includes_tefas_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            coverage_path = Path(tmp_dir) / "coverage.md"
            recommendations_path = Path(tmp_dir) / "source_recommendations.md"
            content = generate_data_coverage_doc(
                coverage_path,
                source_recommendations_path=recommendations_path,
            )
        self.assertIn("tefas_public", content)
        self.assertIn("Fund NAV", content)


if __name__ == "__main__":
    unittest.main()
