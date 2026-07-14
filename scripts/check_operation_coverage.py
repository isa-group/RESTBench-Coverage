#!/usr/bin/env python3
import argparse
import csv
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple


REQUIRED_LEVELS = ("TCL-4", "TCL-5", "TCL-6")


@dataclass(frozen=True, order=True)
class OperationKey:
    api: str
    method: str
    path: str


@dataclass
class DatasetReport:
    operations: Set[OperationKey] = field(default_factory=set)
    suite_count: int = 0
    record_count: int = 0
    errors: List[str] = field(default_factory=list)


def canonical_operation_key(api: str, method: str, path: str) -> OperationKey:
    normalized_api = api.casefold()
    if normalized_api == "youtube-ind":
        normalized_api = "youtube"

    normalized_method = method.upper()
    normalized_path = "/" + path.strip("/")
    normalized_path = re.sub(r"\{[^/{}]+\}", "{}", normalized_path)

    if normalized_api == "languagetool" and normalized_path == "/check":
        normalized_path = "/v2/check"
    elif normalized_api == "ohsome" and normalized_path == "/elements/{}":
        normalized_path = "/v1/elements/{}"
    elif (
        normalized_api == "scout-api"
        and normalized_method == "POST"
        and normalized_path in {"/api/v1/activities", "/api/v2/activities"}
    ):
        normalized_path = "/api/activities"

    return OperationKey(normalized_api, normalized_method, normalized_path)


def load_active_operations(op_config_path: Path) -> Set[OperationKey]:
    path = op_config_path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"operation config not found: {path}")

    module_name = f"restbench_operation_config_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load operation config: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)

    ops_map = getattr(module, "OPS_MAP", None)
    if not isinstance(ops_map, dict):
        raise ValueError(f"OPS_MAP is missing or is not a dictionary: {path}")

    operations = set()
    for api, api_operations in ops_map.items():
        module_name_value = getattr(api, "module_name", None)
        if not module_name_value:
            raise ValueError("ApiConfig entry is missing module_name")
        for operation in api_operations:
            operations.add(
                canonical_operation_key(
                    module_name_value,
                    operation.http_method,
                    operation.operation_path,
                )
            )
    return operations


def inspect_dataset(dataset_root: Path) -> DatasetReport:
    report = DatasetReport()
    suites_root = dataset_root.resolve() / "Test-suites"
    if not suites_root.is_dir():
        report.errors.append(f"test suite root not found: {suites_root}")
        return report

    csv.field_size_limit(sys.maxsize)
    operation_dirs = sorted(
        path
        for api_dir in suites_root.iterdir()
        if api_dir.is_dir()
        for path in api_dir.iterdir()
        if path.is_dir()
    )

    for operation_dir in operation_dirs:
        operation_keys = set()
        for level in REQUIRED_LEVELS:
            level_dir = operation_dir / level
            if not level_dir.is_dir():
                report.errors.append(f"{operation_dir}: missing {level}")
                continue

            report.suite_count += 1
            csv_path = level_dir / "requests_responses.csv"
            jsonl_path = level_dir / "responses.jsonl"
            if not csv_path.is_file():
                report.errors.append(f"{level_dir}: missing requests_responses.csv")
                continue
            if not jsonl_path.is_file():
                report.errors.append(f"{level_dir}: missing responses.jsonl")
                continue

            rows = _read_csv(csv_path, report.errors)
            responses = _read_jsonl(jsonl_path, report.errors)
            report.record_count += len(rows)
            if not rows:
                report.errors.append(f"{csv_path}: suite is empty")
            if not responses:
                report.errors.append(f"{jsonl_path}: suite is empty")

            keys = {
                canonical_operation_key(
                    operation_dir.parent.name,
                    row.get("httpMethod", ""),
                    row.get("path", ""),
                )
                for row in rows
            }
            operation_keys.update(keys)
            if len(keys) > 1:
                report.errors.append(f"{csv_path}: multiple operations in one suite")

            csv_ids = [row.get("testCaseId", "") for row in rows]
            jsonl_ids = [str(response.get("id", "")) for response in responses]
            if len(csv_ids) != len(set(csv_ids)):
                report.errors.append(f"{csv_path}: duplicate testCaseId")
            if len(jsonl_ids) != len(set(jsonl_ids)):
                report.errors.append(f"{jsonl_path}: duplicate response id")
            if csv_ids != jsonl_ids:
                report.errors.append(f"{level_dir}: ID order mismatch")

            for row, response in zip(rows, responses):
                csv_status = str(row.get("statusCode", ""))
                jsonl_status = str(response.get("Status Code", ""))
                if csv_status != jsonl_status:
                    test_id = row.get("testCaseId", "<missing-id>")
                    report.errors.append(
                        f"{level_dir}: status mismatch for test {test_id}"
                    )

        if len(operation_keys) > 1:
            report.errors.append(
                f"{operation_dir}: TCL levels describe different operations"
            )
        report.operations.update(operation_keys)

    return report


def compare_coverage(
    active: Set[OperationKey], dataset: Set[OperationKey]
) -> Tuple[Set[OperationKey], Set[OperationKey]]:
    return active - dataset, dataset - active


def run_check(dataset_root: Path, op_config_path: Path) -> int:
    try:
        active = load_active_operations(op_config_path)
    except Exception as error:
        print(f"configuration error: {type(error).__name__}: {error}", file=sys.stderr)
        return 2

    report = inspect_dataset(dataset_root)
    missing, extra = compare_coverage(active, report.operations)
    print(
        f"active={len(active)} dataset={len(report.operations)} "
        f"missing={len(missing)} extra={len(extra)}"
    )
    print(f"suites={report.suite_count} records={report.record_count}")
    _print_operations("missing", missing)
    _print_operations("extra", extra)
    for error in report.errors:
        print(f"error: {error}", file=sys.stderr)

    return 1 if missing or report.errors else 0


def _read_csv(path: Path, errors: List[str]) -> List[dict]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as error:
        errors.append(f"{path}: cannot parse CSV ({type(error).__name__})")
        return []


def _read_jsonl(path: Path, errors: List[str]) -> List[dict]:
    responses = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    errors.append(f"{path}:{line_number}: response is not an object")
                    continue
                responses.append(value)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"{path}: cannot parse JSONL ({type(error).__name__})")
    return responses


def _print_operations(label: str, operations: Iterable[OperationKey]) -> None:
    for operation in sorted(operations):
        print(f"{label}: {operation.api} {operation.method} {operation.path}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check RESTBench operation coverage against an OPS_MAP config."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path.cwd(),
        help="RESTBench-Coverage repository root (default: current directory)",
    )
    parser.add_argument(
        "--op-config",
        type=Path,
        help="Path to httpmutator-benchmark/expScripts/op_configs.py",
    )
    args = parser.parse_args(argv)
    op_config = args.op_config
    if op_config is None:
        op_config = (
            args.dataset_root.resolve().parent
            / "httpmutator-benchmark"
            / "expScripts"
            / "op_configs.py"
        )
    return run_check(args.dataset_root, op_config)


if __name__ == "__main__":
    raise SystemExit(main())
