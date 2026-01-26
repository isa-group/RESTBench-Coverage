#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collect BLACK-mode metrics:

Layout per strength:
  {root}/{one-way|one-way-reduced|two-way}/BLACK/httpMutatorInput.jsonl
  {root}/{...}/BLACK/{OAS,REG,INV,5xx}/metrics/
      ├─ assertionResults.csv
      └─ mutation-summary-statistics.csv

Output:
  root_path/excripts/results/{api_name}/{op_id}/summary.csv
  root_path/excripts/results/{api_name}/{op_id}/operators.csv
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

SCRIPT_DIR = Path(__file__).parent.resolve()


# ───────────────────────────────
# Parse: JSONL (count as one line if json.loads succeeds)
# ───────────────────────────────
def count_jsonl_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    cnt = 0
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                # Blank line: parse failed -> don't count
                continue
            try:
                json.loads(s)
                cnt += 1
            except Exception:
                # Parse failed -> don't count
                continue
    return cnt


_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def first_number(text: str) -> Optional[float]:
    if text is None:
        return None
    m = _NUM_RE.search(text)
    return float(m.group(0)) if m else None


def parse_assertion_results_strict(path: Path) -> Tuple[int, int, Optional[float], Optional[float]]:
    """
    Parse assertionResults.csv strictly and enforce record-count == Summary.Total.

    Returns: (total, passed, killrate_pct, timecost_sec)

    Rules (matching the provided Java writer):
      - First row is header.
      - Then N record rows (each written via csv.printRecord).
      - Then a blank line (csv.println()).
      - Last row is: Summary,Total=...,Passed=...,KillRate=...%,TimeCost=... s|min .. s
      - record_count = number of rows with len(row)>0 between header and Summary.
      - If record_count != Total, raise ValueError.
    """
    if not path.is_file():
        raise FileNotFoundError(f"assertionResults.csv not found: {path}")

    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        rows = [row for row in csv.reader(f)]

    if not rows:
        raise ValueError(f"Empty assertionResults.csv: {path}")

    # Locate the last Summary line
    summary_idx = None
    for i in range(len(rows) - 1, -1, -1):
        row = rows[i]
        if len(row) == 0:
            continue
        head = (row[0] or "").lstrip("\ufeff").strip().lower()
        if head == "summary":
            summary_idx = i
            break
    if summary_idx is None:
        raise ValueError(f"Missing Summary line in: {path}")

    # Count records between header (idx 0) and Summary (exclusive), ignoring blank rows (len==0)
    # Header is at idx 0 -> records are rows[1:summary_idx] with len(row)>0
    record_count = sum(1 for r in rows[1:summary_idx] if len(r) > 0)

    # Parse Summary
    total = passed = 0
    killrate = None
    timecost_sec = None
    summary = rows[summary_idx]
    for cell in summary[1:]:
        cell = (cell or "").strip()
        if "=" not in cell:
            continue
        k, v = cell.split("=", 1)
        k = (k or "").strip().lower()
        v = (v or "").strip()
        if k == "total":
            n = first_number(v)
            total = int(n if n is not None else 0)
        elif k == "passed":
            n = first_number(v)
            passed = int(n if n is not None else 0)
        elif k == "killrate":
            killrate = first_number(v)  # percent value, e.g., 0.7
        elif k == "timecost":
            # support "X.XX s" or "M min S.SS s"
            n = first_number(v)
            if n is not None:
                if "min" in v.lower():
                    # when "M min S.SS s", first number is minutes -> convert to seconds using both numbers if present
                    # Try to capture two numbers: minutes and seconds
                    nums = [float(x) for x in _NUM_RE.findall(v)]
                    if len(nums) >= 2:
                        timecost_sec = nums[0] * 60.0 + nums[1]
                    else:
                        timecost_sec = n * 60.0
                else:
                    timecost_sec = n

    if record_count != total:
        raise ValueError(
            f"[COUNT MISMATCH] {path}\n"
            f" - records(parsed) = {record_count}\n"
            f" - Summary.Total   = {total}\n"
            f" - Summary.Passed  = {passed}\n"
        )

    return total, passed, killrate, timecost_sec


def parse_operator_counts(path: Path) -> Tuple[Dict[str, dict], int]:
    """
    Strictly parse mutation-summary-statistics.csv.

    Returns:
        counts: nested dict {mutatorName -> {operatorName -> count}}
        grand_total: sum of all counts

    Raises:
        FileNotFoundError if file is missing
        ValueError on any format/consistency error
    """
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    compat_mode: bool = False  # for compatibility with old code
    counts: Dict[str, dict] = defaultdict(dict)
    grand_total = 0
    seen_pairs: set[Tuple[str, str]] = set()
    int_re = re.compile(r"^\d+$")

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"Empty CSV: {path}")
        expected_header = ["mutatorName", "operatorName", "count"]
        if header != expected_header:
            raise ValueError(f"Invalid header in {path}. Expected {expected_header}, got {header}")

        for idx, row in enumerate(reader, start=2):
            if not row:
                raise ValueError(f"Empty row at line {idx} in {path}")
            if len(row) != 3:
                raise ValueError(f"Row {idx} must have exactly 3 columns, got {len(row)}: {row}")

            mutator = row[0].strip()
            operator = row[1].strip()
            count_str = row[2].strip()

            if not mutator:
                raise ValueError(f"Empty mutatorName at line {idx} in {path}")
            if not operator:
                raise ValueError(f"Empty operatorName at line {idx} in {path}")
            if not int_re.match(count_str):
                raise ValueError(f"Invalid count at line {idx} in {path}: '{count_str}'")
            if mutator == "HeaderMutator":
                compat_mode = True

            c = int(count_str)
            pair = (mutator, operator)
            if pair in seen_pairs:
                raise ValueError(f"Duplicate (mutatorName, operatorName) at line {idx}: {pair}")
            seen_pairs.add(pair)

            counts[mutator][operator] = c
            grand_total += c

    nested_sum = sum(v for sub in counts.values() for v in sub.values())
    if nested_sum != grand_total:
        raise ValueError(
            f"Inconsistent totals in {path}: sum(counts)={nested_sum} != grand_total={grand_total}"
        )

    if compat_mode:
        mutants_jsonl = path.parent / "mutants.jsonl"
        if not mutants_jsonl.exists():
            raise ValueError(f"in compat mode, but {mutants_jsonl.absolute()} is not found")
        classify_header_mutator(counts, mutants_jsonl)

    return counts, grand_total


def classify_header_mutator(counts: dict[str, dict], jsonl_path: Path) -> dict[str, dict]:
    """
    Convert 'HeaderMutator' into finer-grained categories based on jsonl_path.
    """
    if "CharsetReplacementOperator" in counts["HeaderMutator"]:
        counts["CharsetMutator"]["CharsetReplacementOperator"] = counts["HeaderMutator"]["CharsetReplacementOperator"]
        del counts["HeaderMutator"]["CharsetReplacementOperator"]

    if "LocationMutationOperator" in counts["HeaderMutator"]:
        counts["LocationMutator"]["LocationMutationOperator"] = counts["HeaderMutator"]["LocationMutationOperator"]
        del counts["HeaderMutator"]["LocationMutationOperator"]

    if "MediaTypeReplacementOperator" in counts["HeaderMutator"]:
        counts["MediaTypeMutator"]["MediaTypeReplacementOperator"] = counts["HeaderMutator"]["MediaTypeReplacementOperator"]
        del counts["HeaderMutator"]["MediaTypeReplacementOperator"]

    if "NullOperator" not in counts["HeaderMutator"]:
        return counts

    header_null_count = counts["HeaderMutator"]["NullOperator"]
    del counts["HeaderMutator"]["NullOperator"]

    media_acc = 0
    location_acc = 0
    charset_acc = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            j = json.loads(line)
            json_node_path: str = j["nodePath"]
            if not json_node_path.startswith("Headers/"):
                continue
            c = 0
            for m in j["mutations"]:
                if m["operator"] == "NullOperator":
                    if json_node_path.endswith("location"): location_acc += 1
                    elif json_node_path.endswith("mediaType"): media_acc += 1
                    elif json_node_path.endswith("charset"): charset_acc += 1

    if location_acc:
        counts["LocationMutator"]["NullOperator"] = location_acc
    if media_acc:
        counts["MediaTypeMutator"]["NullOperator"] = media_acc
    if charset_acc:
        counts["CharsetMutator"]["NullOperator"] = charset_acc

    assert location_acc + media_acc + charset_acc == header_null_count, f"Split mismatch: {location_acc}+{media_acc}+{charset_acc} != {header_null_count}"
    return counts

def write_csv(path: Path, rows: List[dict], header: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _flatten_operator_counts(nested: Dict[str, Dict[str, int]]) -> List[dict]:
    """
    Flatten nested counts {mutatorName: {operatorName: count}} to rows with
    header: mutatorName, operatorName, count
    """
    rows: List[dict] = []
    for mutator in sorted(nested.keys()):
        for operator in sorted(nested[mutator].keys()):
            rows.append({
                "mutatorName": mutator,
                "operatorName": operator,
                "count": nested[mutator][operator],
            })
    return rows


def write_operator_wide_csv(path: Path, nested: Dict[str, Dict[str, int]]) -> None:
    """
    Write operators as a single wide row:
      - Header columns are "mutatorName:operatorName"
      - Row values are the integer counts
    Columns are sorted by mutatorName, then operatorName for determinism.
    """
    # Build deterministic headers
    headers: List[str] = []
    for mutator in sorted(nested.keys()):
        for operator in sorted(nested[mutator].keys()):
            headers.append(f"{mutator}:{operator}")

    # Single row with counts; empty dict => write only header
    row: Dict[str, int] = {}
    for mutator in sorted(nested.keys()):
        for operator in sorted(nested[mutator].keys()):
            key = f"{mutator}:{operator}"
            row[key] = nested[mutator][operator]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        if headers:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerow(row)
        else:
            # No operators found: still create an empty file with no columns
            f.write("")  # intentionally empty

def _count_json_nodes(x: Any) -> int:
    """
    Recursively count nodes in a JSON-like structure:
      - Scalars (str, int, float, bool, None) count as 1
      - Dict (object) counts as 1 + sum of its values
      - List (array) counts as 1 + sum of its elements
    """
    if isinstance(x, dict):
        return 1 + sum(_count_json_nodes(v) for v in x.values())
    if isinstance(x, (list, tuple)):
        return 1 + sum(_count_json_nodes(v) for v in x)
    return 1  # scalar


def tally_response_complexity(jsonl_path: Path) -> List[int]:
    """
    Read a JSONL file, where each line is an HTTP response.
    For each record, compute:
      - body_count: number of JSON nodes in Body
      - status_bonus: +1 if "Status Code" is present
      - headers_bonus: +1 if 'content-type' present, +1 if 'location' present
      - total: sum of the above
    Returns:
      List of dicts with detailed counts per record.
    """
    results: List[int] = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec: Dict[str, Any] = json.loads(line)
            rid = str(rec.get("id", ""))

            # Body count
            body_val = rec.get("Body", None)
            if body_val is None:
                body_count = 0
            else:
                body_count = _count_json_nodes(body_val)

            # Status Code bonus
            status_bonus = 1 if "Status Code" in rec else 0

            # Headers bonus
            headers = rec.get("Headers", {}) or {}
            hkeys = {str(k).lower() for k in headers.keys()} if isinstance(headers, dict) else set()
            headers_bonus = 0
            if "content-type" in hkeys:
                headers_bonus += 1
            if "location" in hkeys:
                headers_bonus += 1

            # Total score
            results.append(body_count + status_bonus + headers_bonus)
    return results


def _collect_for_root(result_dir: Path, metric_dir_name: str, out_root_dir: Path) -> None:
    """
    Core collection logic for a given input/output root.

    Input directory structure (same for black and black_random):
        {metrics_root_dir}/{op}/{strength}/{level}/metrics/{assertionResults.csv, mutation-summary-statistics.csv}
        {metrics_root_dir}/{op}/{strength}/httpMutatorInput.jsonl

    Output directory structure:
        {out_root_dir}/{op}/metrics-{level}-{strength}.csv
        {out_root_dir}/{op}/operators-{strength}.csv
    """
    levels = ["5xx", "OAS", "INV", "REG"]
    strengths = ["one-way", "one-way-reduced", "two-way"]

    if not result_dir.exists():
        return

    out_root_dir.mkdir(parents=True, exist_ok=True)

    for op_dir in result_dir.iterdir():
        if not op_dir.is_dir():
            continue

        op_name = op_dir.name.lower()
        op_out_dir = out_root_dir / op_name
        op_out_dir.mkdir(parents=True, exist_ok=True)

        for s in strengths:
            hm_jsonl_file = op_dir / s / "httpMutatorInput.jsonl"
            tc_count = count_jsonl_lines(hm_jsonl_file)
            resp_fields_count = sum(tally_response_complexity(hm_jsonl_file))

            baseline_ops: Optional[Dict[str, Dict[str, int]]] = None

            for l in levels:
                metrics_dir = op_dir / s / l / metric_dir_name
                if not metrics_dir.exists():
                    continue

                assertions_file = metrics_dir / "assertionResults.csv"
                m_summary_file = metrics_dir / "mutation-summary-statistics.csv"

                if assertions_file.is_file():
                    try:
                        total, passed, kill_rate, time_cost = parse_assertion_results_strict(assertions_file)
                    except Exception as e:
                        print(f"[ERROR] Failed to parse {assertions_file}: {e}")
                        continue
                    metrics_csv = op_out_dir / f"metrics-{l}-{s}.csv"
                    write_csv(
                        metrics_csv,
                        rows=[{
                            "tc_count": tc_count,
                            "resp_fields_count": resp_fields_count,
                            "total": total,
                            "passed": passed,
                            "kill_rate": kill_rate,
                            "time_cost": time_cost,
                        }],
                        header=["tc_count", "resp_fields_count", "total", "passed", "kill_rate", "time_cost"],
                    )

                if m_summary_file.is_file():
                    operator_counts, _ = parse_operator_counts(m_summary_file)
                    if baseline_ops is None:
                        baseline_ops = operator_counts
                    else:
                        # if operator_counts != baseline_ops:
                        #     raise ValueError(
                        #         f"[operator_counts mismatch] API={api.module_name}, op={op_name}, strength={s}\n"
                        #         f"- baseline level: {baseline_level}\n"
                        #         f"- mismatched level: {l}\n"
                        #     )
                        pass

            if baseline_ops is not None:
                operators_csv = op_out_dir / f"operators-{s}.csv"
                write_operator_wide_csv(operators_csv, baseline_ops)


def collect_for_api(api: ApiConfig) -> None:
    """
    Run collection for both black and black_random modes.
    Both share the same directory structure but are written to different output roots.

    black:
        input: {api.mt_abs_path()}/httpmutator
        output: SCRIPT_DIR/black_metrics/{api}
    black_random:
        input: {api.mt_abs_path()}/httpmutator
        output: SCRIPT_DIR/black_random_metrics/{api}
    """
    root_dir = api.mt_abs_path() / "httpmutator"

    api_black_out_dir = SCRIPT_DIR / "black_metrics" / api.module_name
    api_black_random_out_dir = SCRIPT_DIR / "black_random_metrics" / api.module_name

    _collect_for_root(root_dir, "metrics", api_black_out_dir)
    _collect_for_root(root_dir, "metrics_random", api_black_random_out_dir)


if __name__ == "__main__":
    from op_configs import OPS_MAP

    for _api in OPS_MAP.keys():
        collect_for_api(_api)
