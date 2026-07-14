import csv
import contextlib
import io
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_operation_coverage import (  # noqa: E402
    canonical_operation_key,
    compare_coverage,
    inspect_dataset,
    load_active_operations,
    run_check,
)


CSV_FIELDS = [
    "testCaseId",
    "operationId",
    "path",
    "httpMethod",
    "queryParameters",
    "headerParameters",
    "pathParameters",
    "formParameters",
    "bodyParameter",
    "statusCode",
    "responseHeaders",
    "responseBody",
]


class CoverageCheckerTest(unittest.TestCase):
    def test_normalizes_api_prefixes_trailing_slashes_and_path_parameters(self):
        self.assertEqual(
            canonical_operation_key("youtube-ind", "GET", "/youtube/v3/videos/"),
            canonical_operation_key("youtube", "get", "/youtube/v3/videos"),
        )
        self.assertEqual(
            canonical_operation_key("languagetool", "POST", "/check"),
            canonical_operation_key("languagetool", "POST", "/v2/check"),
        )
        self.assertEqual(
            canonical_operation_key("ohsome", "GET", "/elements/{aggregation}"),
            canonical_operation_key("ohsome", "GET", "/v1/elements/{kind}"),
        )

    def test_scout_post_v1_and_v2_are_equivalent_but_puts_are_distinct(self):
        self.assertEqual(
            canonical_operation_key("scout-api", "POST", "/api/v1/activities"),
            canonical_operation_key("scout-api", "POST", "/api/v2/activities"),
        )
        self.assertNotEqual(
            canonical_operation_key("scout-api", "PUT", "/api/v1/activities/{id}"),
            canonical_operation_key("scout-api", "PUT", "/api/v2/activities/{id}"),
        )

    def test_loads_only_operations_present_in_ops_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "op_configs.py"
            config.write_text(
                textwrap.dedent(
                    """
                    class Api:
                        def __init__(self, module_name): self.module_name = module_name
                    class Op:
                        def __init__(self, method, path):
                            self.http_method = method
                            self.operation_path = path
                    OPS_MAP = {Api("example"): [Op("GET", "/items/{itemId}")]}
                    """
                ),
                encoding="utf-8",
            )

            operations = load_active_operations(config)

        self.assertEqual(
            operations,
            {canonical_operation_key("example", "GET", "/items/{id}")},
        )

    def test_inspects_complete_suites_and_accepts_large_csv_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_operation(root, response_body="x" * 140_000)

            report = inspect_dataset(root)

        self.assertEqual(report.suite_count, 3)
        self.assertEqual(report.record_count, 3)
        self.assertEqual(len(report.operations), 1)
        self.assertEqual(report.errors, [])

    def test_reports_missing_tcl_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_operation(root, levels=("TCL-4", "TCL-5"))

            report = inspect_dataset(root)

        self.assertTrue(any("TCL-6" in error for error in report.errors))

    def test_reports_id_and_status_mismatches_without_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_operation(root, jsonl_id="different-id", jsonl_status=500)

            report = inspect_dataset(root)

        joined = "\n".join(report.errors)
        self.assertIn("ID order mismatch", joined)
        self.assertIn("status mismatch", joined)
        self.assertNotIn("secret-response-body", joined)

    def test_compare_coverage_allows_extra_dataset_operations(self):
        required = {canonical_operation_key("example", "GET", "/required")}
        dataset = required | {canonical_operation_key("example", "GET", "/extra")}

        missing, extra = compare_coverage(required, dataset)

        self.assertEqual(missing, set())
        self.assertEqual(extra, dataset - required)

    def test_run_check_returns_one_for_missing_operation_and_two_for_bad_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_operation(root)
            config = root / "op_configs.py"
            config.write_text(
                textwrap.dedent(
                    """
                    class Api:
                        def __init__(self, module_name): self.module_name = module_name
                    class Op:
                        def __init__(self, method, path):
                            self.http_method = method
                            self.operation_path = path
                    OPS_MAP = {Api("example"): [Op("GET", "/missing")]}
                    """
                ),
                encoding="utf-8",
            )

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                self.assertEqual(run_check(root, config), 1)
                self.assertEqual(run_check(root, root / "absent.py"), 2)

    def _write_operation(
        self,
        root,
        *,
        levels=("TCL-4", "TCL-5", "TCL-6"),
        response_body="secret-response-body",
        jsonl_id="case-1",
        jsonl_status=200,
    ):
        row = {
            "testCaseId": "case-1",
            "operationId": "getItems",
            "path": "/items/{itemId}",
            "httpMethod": "GET",
            "queryParameters": "",
            "headerParameters": "",
            "pathParameters": "itemId=1",
            "formParameters": "",
            "bodyParameter": "",
            "statusCode": "200",
            "responseHeaders": "content-type=application/json",
            "responseBody": response_body,
        }
        for level in levels:
            suite = root / "Test-suites" / "example" / "getItems" / level
            suite.mkdir(parents=True)
            with (suite / "requests_responses.csv").open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerow(row)
            (suite / "responses.jsonl").write_text(
                json.dumps(
                    {
                        "id": jsonl_id,
                        "Status Code": jsonl_status,
                        "Body": response_body,
                        "Headers": {"content-type": "application/json"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    unittest.main()
