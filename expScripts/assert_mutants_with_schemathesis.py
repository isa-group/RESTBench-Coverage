#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import json
import orjson
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

import requests
import schemathesis as st
from schemathesis.checks import CHECKS, load_all_checks
from schemathesis.core.failures import FailureGroup
from schemathesis.core.transport import Response as StResponse

from run_evomaster import _resolve_operation_config, SCRIPT_DIR
import os
from concurrent.futures import ProcessPoolExecutor, as_completed


# =============================================================================
# Configuration
# =============================================================================
MAX_WORKERS: int = max(1, (os.cpu_count() or 2) - 1)

MUTANTS_ROOT: Path = SCRIPT_DIR / "schemathesis-unique-reports"

SHARDED_APIS: Set[str] = {"Deutschebahn", "FDIC"}
POLL_SECONDS: int = 30

ORIGINAL_ID_FIELD = "id"
MUTANT_ORIGINAL_ID_FIELD = "_hm_original_id"
CHECKS_FIELD = "Checks"

STATUS_FIELD = "Status Code"
HEADERS_FIELD = "Headers"
BODY_FIELD = "Body"

DESIRED_CHECK_NAMES: Set[str] = {
    "not_a_server_error",
    "status_code_conformance",
    "response_headers_conformance",
    "response_schema_conformance",
    "content_type_conformance",
}

ASSERT_SHARED_COUNT: bool = True

# Global CSV output
SUMMARY_CSV: Path = MUTANTS_ROOT / "schemathesis_mutant_validation_summary.csv"

# After processing each shard:
#   "delete"  -> unlink
#   "archive" -> move to shared/processed/
#   "mark"    -> rename to *.done (kept in shared/)
SHARD_POST_ACTION: str = "archive"  # {"delete","archive","mark"}
ARCHIVE_SUBDIR_NAME: str = "processed"

# =============================================================================
# Data structures
# =============================================================================

@dataclass
class MutantStats:
    total: int = 0
    survived: int = 0
    killed: int = 0
    invalid: int = 0


def kill_rate(killed: int, survived: int) -> float:
    denom = killed + survived
    return (killed / denom) if denom > 0 else 0.0


# =============================================================================
# CSV helpers
# =============================================================================

CSV_HEADER = [
    "api",
    "operation",
    "mode",
    "http_method",
    "operation_path",
    "total",
    "survived",
    "killed",
    "invalid",
    "kill_rate",
    # shared-only (blank for plain)
    "expected_total",
    "processed_total",
]


def ensure_summary_csv_header(path: Path) -> None:
    """
    Create CSV with header if it doesn't exist or is empty.
    """
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)


def append_summary_row(
    path: Path,
    api: str,
    operation: str,
    mode: str,
    http_method: str,
    operation_path: str,
    stats: MutantStats,
    expected_total: Optional[int] = None,
    processed_total: Optional[int] = None,
) -> None:
    ensure_summary_csv_header(path)
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                api,
                operation,
                mode,
                http_method,
                operation_path,
                stats.total,
                stats.survived,
                stats.killed,
                stats.invalid,
                kill_rate(stats.killed, stats.survived),
                "" if expected_total is None else expected_total,
                "" if processed_total is None else processed_total,
            ]
        )


# =============================================================================
# Checks loading
# =============================================================================

load_all_checks()
ALL_CHECKS_BY_NAME: Dict[str, Callable[..., Any]] = {
    fn.__name__: fn for fn in CHECKS.get_all()
}

for name in sorted(DESIRED_CHECK_NAMES):
    if name not in ALL_CHECKS_BY_NAME:
        print(f"[WARN] Desired check not found in Schemathesis: {name}")


def resolve_effective_check_names(raw_checks: Any) -> List[str]:
    if raw_checks is None or not isinstance(raw_checks, list):
        raise RuntimeError("Original row missing valid Checks list")

    row_names = {str(x) for x in raw_checks}
    effective = sorted(row_names & DESIRED_CHECK_NAMES)
    effective = [n for n in effective if n in ALL_CHECKS_BY_NAME]

    if not effective:
        raise RuntimeError(
            f"Original has no executable checks after intersection: {raw_checks}"
        )
    return effective


def load_original_checks(inputs_jsonl: Path) -> Dict[str, List[str]]:
    original_checks: Dict[str, List[str]] = {}
    with inputs_jsonl.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON in originals at line {line_no}: {inputs_jsonl}"
                ) from exc

            if ORIGINAL_ID_FIELD not in row:
                raise RuntimeError(
                    f"Missing `{ORIGINAL_ID_FIELD}` in originals at line {line_no}"
                )

            oid = str(row[ORIGINAL_ID_FIELD])
            original_checks[oid] = resolve_effective_check_names(row.get(CHECKS_FIELD))

    return original_checks


# =============================================================================
# Schemathesis helpers
# =============================================================================

def build_schemathesis_response(row: Dict[str, Any], http_method: str) -> StResponse:
    if STATUS_FIELD not in row:
        raise KeyError(f"Missing `{STATUS_FIELD}`")

    status_code = int(row[STATUS_FIELD])
    headers_raw = row.get(HEADERS_FIELD) or {}
    body = row.get(BODY_FIELD)

    headers: Dict[str, list[str]] = {}
    if isinstance(headers_raw, dict):
        for k, v in headers_raw.items():
            key = str(k).lower()
            headers[key] = [str(x) for x in v] if isinstance(v, list) else [str(v)]

    if body is None:
        content_bytes = b""
    elif isinstance(body, (dict, list)):
        content_bytes = json.dumps(body).encode("utf-8")
    else:
        content_bytes = str(body).encode("utf-8")

    dummy_request = requests.Request(http_method, "http://localhost:8080").prepare()

    return StResponse(
        status_code=status_code,
        headers=headers,
        content=content_bytes,
        encoding="utf-8",
        elapsed=0.0,
        http_version="1.1",
        message="",
        request=dummy_request,
        verify=True,
    )


def build_operation_case(api_name: str, op_name: str) -> Tuple[str, st.Case, str]:
    op_conf = _resolve_operation_config(api_name, op_name)
    http_method = op_conf.http_method.upper()
    operation_path = op_conf.operation_path

    # Special-case path fix
    if operation_path == "/v3/shopping/hotel-offers":
        operation_path = "/shopping/hotel-offers"
    elif operation_path == "/api/v1/activities":
        operation_path = "/v1/activities"

    schema = st.openapi.from_path(op_conf.resolved_oas())
    operation = schema[operation_path][http_method]
    case = operation.Case(path_parameters={"id": 1, "aggregation": "test"})

    return http_method, case, operation_path

# =============================================================================
# Worker cache (per process)
# =============================================================================

_WORKER_CASE_CACHE: Dict[Tuple[str, str], st.Case] = {}

def get_cached_case(api_name: str, op_name: str) -> st.Case:
    key = (api_name, op_name)
    case = _WORKER_CASE_CACHE.get(key)
    if case is not None:
        return case
    _, case, _ = build_operation_case(api_name, op_name)
    _WORKER_CASE_CACHE[key] = case
    return case


# =============================================================================
# Shared shard reading
# =============================================================================

def iter_zst_jsonl_rows(path: Path) -> Iterator[Dict[str, Any]]:
    try:
        import zstandard as zstd
    except Exception as exc:
        raise RuntimeError("zstandard required: pip install zstandard") from exc

    dctx = zstd.ZstdDecompressor()
    with path.open("rb") as fh, dctx.stream_reader(fh) as reader:
        import io
        text = io.TextIOWrapper(reader, encoding="utf-8")
        for line in text:
            line = line.strip()
            if not line:
                continue
            try:
                yield orjson.loads(line)
            except orjson.JSONDecodeError:
                yield {"__invalid_json__": True}


# =============================================================================
# Validation logic
# =============================================================================

def validate_row(
    row: Dict[str, Any],
    case: st.Case,
    http_method: str,
    original_checks: Dict[str, List[str]],
) -> str:
    if row.get("__invalid_json__"):
        return "invalid"

    original_id = row.get(MUTANT_ORIGINAL_ID_FIELD)
    if original_id is None:
        return "invalid"

    checks = original_checks.get(str(original_id))
    if not checks:
        return "invalid"

    try:
        response = build_schemathesis_response(row, http_method)
    except Exception:
        return "invalid"

    schema_check = ALL_CHECKS_BY_NAME.get("response_schema_conformance")
    non_schema_checks = [
        ALL_CHECKS_BY_NAME[n]
        for n in checks
        if n != "response_schema_conformance"
    ]

    try:
        if non_schema_checks:
            case.validate_response(response, checks=non_schema_checks)
    except FailureGroup:
        return "killed"

    if "response_schema_conformance" in checks and schema_check is not None:
        try:
            case.validate_response(response, checks=[schema_check])
        except FailureGroup as e:
            return "killed"

    return "survived"


def process_mutants_jsonl(
    mutants_jsonl: Path,
    case: st.Case,
    http_method: str,
    original_checks: Dict[str, List[str]],
) -> MutantStats:
    stats = MutantStats()
    print(f"[INFO] Processing {mutants_jsonl}")
    with mutants_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats.total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                stats.invalid += 1
                continue

            outcome = validate_row(row, case, http_method, original_checks)
            if outcome == "survived":
                stats.survived += 1
            elif outcome == "killed":
                stats.killed += 1
            else:
                stats.invalid += 1
    return stats

def finalize_shard(shard: Path, shared_dir: Path) -> None:
    """
    Finalize a shard after it has been processed.

    If the shard was claimed, it is named like:
        mutants-00001.jsonl.zst.inprogress
    We first restore it back to:
        mutants-00001.jsonl.zst
    and then apply SHARD_POST_ACTION.

    This keeps the archive/mark directory clean and stable across reruns.
    """
    # Step 1) normalize name: strip ".inprogress" suffix if present
    normalized = shard
    suffix = ".inprogress"
    if shard.name.endswith(suffix):
        normalized = shard.with_name(shard.name[: -len(suffix)])
        try:
            shard.rename(normalized)  # same filesystem => atomic rename
        except FileNotFoundError:
            # Already moved/renamed by something else; treat as no-op
            return

    # Step 2) apply post-action on normalized path
    if SHARD_POST_ACTION == "delete":
        normalized.unlink(missing_ok=True)
        return

    if SHARD_POST_ACTION == "archive":
        dst_dir = shared_dir / ARCHIVE_SUBDIR_NAME
        dst_dir.mkdir(parents=True, exist_ok=True)
        normalized.rename(dst_dir / normalized.name)  # atomic move within FS
        return

    if SHARD_POST_ACTION == "mark":
        normalized.rename(normalized.with_name(normalized.name + ".done"))
        return

    raise ValueError(f"Unknown SHARD_POST_ACTION={SHARD_POST_ACTION}")


def claim_shard(shard: Path) -> Optional[Path]:
    """
    Atomically claim a shard by renaming it to *.inprogress.
    If another process already claimed it, rename will fail.
    """
    claimed = shard.with_name(shard.name + ".inprogress")
    try:
        shard.rename(claimed)
        return claimed
    except Exception:
        return None

def process_one_shard_worker(
    shard_path: str,
    api_name: str,
    op_name: str,
    http_method: str,
    original_checks: Dict[str, List[str]],
) -> Tuple[MutantStats, int]:
    """
    Process exactly one shard (.jsonl.zst.inprogress) in a worker process.
    Returns (stats, processed_lines).
    """
    shard = Path(shard_path)
    stats = MutantStats()
    processed_lines = 0
    print(f"[WORKER pid={os.getpid()}] processing {shard.name}")

    # Build a fresh case inside the worker (do NOT share schemathesis objects)
    case = get_cached_case(api_name, op_name)

    for row in iter_zst_jsonl_rows(shard):
        processed_lines += 1
        stats.total += 1

        outcome = validate_row(row, case, http_method, original_checks)
        if outcome == "survived":
            stats.survived += 1
        elif outcome == "killed":
            stats.killed += 1
        else:
            stats.invalid += 1

    return stats, processed_lines


def process_shared_streaming_parallel(
    shared_dir: Path,
    api_name: str,
    op_name: str,
    http_method: str,
    original_checks: Dict[str, List[str]],
    op_label: str,
) -> Tuple[MutantStats, Optional[int], int]:
    """
    Parallel shared processing (bounded inflight futures):
    - Claim shards via rename to *.inprogress
    - Submit each claimed shard to a worker process
    - Main process aggregates stats and finalizes shard files
    """
    stats = MutantStats()
    processed_total = 0
    expected_total: Optional[int] = None
    count_file = shared_dir / "mutants-count.txt"

    # Key change: bound inflight futures to avoid thousands of pending tasks
    MAX_INFLIGHT = max(1, 2 * MAX_WORKERS)

    print(
        f"[INFO] Enter shared streaming mode (parallel, workers={MAX_WORKERS}, "
        f"max_inflight={MAX_INFLIGHT}): {op_label}"
    )

    futures: Dict[Any, Path] = {}

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        while True:
            # Detect expected total once
            if expected_total is None and count_file.exists():
                expected_total = int(count_file.read_text(encoding="utf-8").strip())
                print(f"[INFO] {op_label}: detected mutants-count.txt = {expected_total}")

            # 1) If inflight is below threshold, claim & submit new shards
            if len(futures) < MAX_INFLIGHT:
                for shard in sorted(shared_dir.glob("*.jsonl.zst")):
                    if len(futures) >= MAX_INFLIGHT:
                        break

                    claimed = claim_shard(shard)
                    if claimed is None:
                        continue

                    fut = pool.submit(
                        process_one_shard_worker,
                        str(claimed),
                        api_name,
                        op_name,
                        http_method,
                        original_checks,
                    )
                    futures[fut] = claimed
                    print(f"[INFO] {op_label}: submitted {shard.name} -> {claimed.name}")

            # 2) Collect completed futures
            done = [f for f in futures if f.done()]
            for f in done:
                claimed = futures.pop(f)
                try:
                    shard_stats, shard_lines = f.result()
                except Exception:
                    print(f"[ERROR] {op_label}: shard failed: {claimed.name}")
                    raise

                # Aggregate
                stats.total += shard_stats.total
                stats.survived += shard_stats.survived
                stats.killed += shard_stats.killed
                stats.invalid += shard_stats.invalid
                processed_total += shard_lines

                # Finalize shard file in main process
                finalize_shard(claimed, shared_dir)
                print(f"[INFO] {op_label}: finished {claimed.name}, lines={shard_lines}")

            # 3) Termination condition
            if expected_total is not None:
                no_ready = not any(shared_dir.glob("*.jsonl.zst"))
                no_tmp = not any(shared_dir.glob("*.jsonl.zst.tmp"))
                no_inprogress = not any(shared_dir.glob("*.jsonl.zst.inprogress"))
                if no_ready and no_tmp and no_inprogress and not futures:
                    if ASSERT_SHARED_COUNT and processed_total != expected_total:
                        raise AssertionError(
                            f"[COUNT ASSERT FAIL] {op_label}: processed={processed_total}, expected={expected_total}"
                        )
                    print(f"[INFO] {op_label}: shared processing complete")
                    return stats, expected_total, processed_total

            # 4) Sleep strategy (avoid busy looping)
            # - If nothing is running and no work is ready: long sleep
            # - Otherwise: short sleep to keep pipeline moving
            if not futures and not any(shared_dir.glob("*.jsonl.zst")):
                time.sleep(POLL_SECONDS)
            else:
                time.sleep(1)

def process_shared_streaming(
    shared_dir: Path,
    case: st.Case,
    http_method: str,
    original_checks: Dict[str, List[str]],
    op_label: str,
) -> Tuple[MutantStats, Optional[int], int]:
    """
    Returns (stats, expected_total, processed_total)
    """
    stats = MutantStats()
    processed_total = 0
    expected_total: Optional[int] = None
    count_file = shared_dir / "mutants-count.txt"

    print(f"[INFO] Enter shared streaming mode: {op_label}")

    while True:
        if expected_total is None and count_file.exists():
            expected_total = int(count_file.read_text(encoding="utf-8").strip())
            print(f"[INFO] {op_label}: detected mutants-count.txt = {expected_total}")

        ready_shards = sorted(shared_dir.glob("*.jsonl.zst"))

        for shard in ready_shards:
            print(f"[INFO] {op_label}: processing shard {shard.name}")
            before = stats.total

            for row in iter_zst_jsonl_rows(shard):
                stats.total += 1
                processed_total += 1

                outcome = validate_row(row, case, http_method, original_checks)
                if outcome == "survived":
                    stats.survived += 1
                elif outcome == "killed":
                    stats.killed += 1
                else:
                    stats.invalid += 1

            finalize_shard(shard, shared_dir)
            print(
                f"[INFO] {op_label}: finished shard {shard.name}, "
                f"lines={stats.total - before}, post_action={SHARD_POST_ACTION}"
            )

        # Termination: count exists + no ready shards + no tmp shards
        if expected_total is not None and not list(shared_dir.glob("*.jsonl.zst")) and not list(shared_dir.glob("*.jsonl.zst.tmp")):
            if ASSERT_SHARED_COUNT and processed_total != expected_total:
                raise AssertionError(
                    f"[COUNT ASSERT FAIL] {op_label}: processed={processed_total}, expected={expected_total}"
                )
            print(f"[INFO] {op_label}: shared processing complete")
            return stats, expected_total, processed_total

        if not ready_shards:
            time.sleep(POLL_SECONDS)


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    if not MUTANTS_ROOT.exists():
        raise FileNotFoundError(MUTANTS_ROOT)

    ensure_summary_csv_header(SUMMARY_CSV)

    print(f"[INFO] Starting validation under {MUTANTS_ROOT}")
    print(f"[INFO] Summary CSV: {SUMMARY_CSV}")

    for api_dir in sorted(p for p in MUTANTS_ROOT.iterdir() if p.is_dir()):
        api_name = api_dir.name

        if api_name in ("Deutschebahn", "FDIC"):
            continue

        # if api_name != "iTunes":
        #     continue

        print(f"\n[INFO] API: {api_name}")

        for op_dir in sorted(p for p in api_dir.iterdir() if p.is_dir()):
            op_name = op_dir.name
            inputs_jsonl = op_dir / "httpmutator-inputs.jsonl"
            mutants_jsonl = op_dir / "mutants.jsonl"
            shared_dir = op_dir / "shared"

            if not inputs_jsonl.exists():
                continue

            use_shared = api_name in SHARDED_APIS and shared_dir.exists()
            if not use_shared and not mutants_jsonl.exists():
                continue

            mode = "shared" if use_shared else "plain"
            print(f"[INFO] Operation: {api_name}/{op_name} mode={mode}")

            original_checks = load_original_checks(inputs_jsonl)
            http_method, case, op_path = build_operation_case(api_name, op_name)

            expected_total: Optional[int] = None
            processed_total: Optional[int] = None

            if use_shared:
                # stats, expected_total, processed_total_int = process_shared_streaming(
                #     shared_dir, case, http_method, original_checks,
                #     f"{api_name}/{op_name}"
                # )
                stats, expected_total, processed_total_int = process_shared_streaming_parallel(
                    shared_dir=shared_dir,
                    api_name=api_name,
                    op_name=op_name,
                    http_method=http_method,
                    original_checks=original_checks,
                    op_label=f"{api_name}/{op_name}",
                )
                processed_total = processed_total_int
            else:
                stats = process_mutants_jsonl(
                    mutants_jsonl, case, http_method, original_checks
                )

            # Print summary
            print(
                f"[SUMMARY] {api_name}/{op_name}: "
                f"total={stats.total}, survived={stats.survived}, "
                f"killed={stats.killed}, invalid={stats.invalid}, "
                f"kill_rate={kill_rate(stats.killed, stats.survived):.4f}"
            )

            # Append to global CSV
            append_summary_row(
                SUMMARY_CSV,
                api=api_name,
                operation=op_name,
                mode=mode,
                http_method=http_method,
                operation_path=op_path,
                stats=stats,
                expected_total=expected_total,
                processed_total=processed_total,
            )

    print("\n[INFO] Done. Summary written to:")
    print(f"       {SUMMARY_CSV}")


if __name__ == "__main__":
    main()
