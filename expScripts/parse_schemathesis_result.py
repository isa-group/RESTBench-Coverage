#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aggregate Schemathesis + HTTPMutator mutant validation results into a single summary CSV.

Directory layout:
  schemathesis-unique-reports/<api_name>/<operation_name>/
    - httpmutator-inputs.jsonl          # collected originals (one JSON per line)
    - dumps/*-req.txt                   # schemathesis request dumps (optional)
    - reporter/stats.json               # Restats-like input coverage stats (optional)

Mutation totals (total/survived/killed/invalid/kill_rate) are read from:
  expScripts/schemathesis-unique-reports/schemathesis_mutant_validation_summary.csv

This script:
  - Reads mutation totals per (api, operation) from schemathesis_mutant_validation_summary.csv
    * If any duplicates exist for (api, operation), raises RuntimeError
  - Counts schemathesis tests from dumps/*-req.txt
  - Counts mutation tests from number of lines in httpmutator-inputs.jsonl
  - Reads coverage rates from reporter/stats.json (kept as raw floats)

Output:
  - schemathesis-unique-reports/summary.csv
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Any, Tuple

from op_configs import SCRIPT_DIR
from run_evomaster import _resolve_operation_config


# =============================================================================
# Configuration
# =============================================================================

ROOT = SCRIPT_DIR / "schemathesis-unique-reports"
SUMMARY_CSV = ROOT / "summary.csv"

MUTATION_TOTALS_CSV = (
    SCRIPT_DIR / "schemathesis-unique-reports" / "schemathesis_mutant_validation_summary.csv"
)

FORMAL_NAME_ORDER = [
    "ScoutAPI-CreateActivities",
    "ProjectSwagger-AssignTask",
    "UserOpenAPI-UpdateUser",
    "Market-RegisterUser",
    "PersonOpenAPI-CreatePerson",
    "ProxyPrint-RegisterRequest",
    "LanguageTool-CheckText",
    "CatWatch-ListProjects",
    "Gestaohospital-CreateHospital",
    "GenomeNexus-Annotate",
    "Stripe-CreateProduct",
    "Foursquare-SearchPlaces",
    "Yelp-SearchBusinesses",
    "AmadeusHotel-GetOffers",
    "YouTube-GetVideos",
    "DHL-FindByAddress",
    "FDIC-ListInstitutions",
    "Ohsome-GetElements",
    "DeutscheBahn-ListStations",
    "iTunes-Search",
]


# =============================================================================
# Helpers
# =============================================================================

def safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        s = str(x).strip()
        if s == "":
            return default
        return int(float(s))  # tolerant to "123.0"
    except Exception:
        return default


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        s = str(x).strip()
        if s == "":
            return default
        return float(s)
    except Exception:
        return default


def read_coverage_stats(op_dir: Path) -> Dict[str, float]:
    """
    Read coverage rates from reporter/stats.json.
    Keep as raw floats (no formatting).
    """
    cov = {
        "param_value_cov": 0.0,
        "param_cov": 0.0,
        "status_class_cov": 0.0,
        "status_cov": 0.0,
        "response_type_cov": 0.0,
        "request_type_cov": 0.0,
    }

    reporter_stats = op_dir / "reporter" / "stats.json"
    if not reporter_stats.exists():
        return cov

    try:
        with reporter_stats.open(encoding="utf-8") as jf:
            data = json.load(jf)

        cov["param_value_cov"] = safe_float(data.get("parameterValueCoverage", {}).get("rate", 0.0), 0.0)
        cov["param_cov"] = safe_float(data.get("parameterCoverage", {}).get("rate", 0.0), 0.0)
        cov["status_class_cov"] = safe_float(data.get("statusClassCoverage", {}).get("rate", 0.0), 0.0)
        cov["status_cov"] = safe_float(data.get("statusCoverage", {}).get("rate", 0.0), 0.0)
        cov["response_type_cov"] = safe_float(data.get("responseTypeCoverage", {}).get("rate", 0.0), 0.0)
        cov["request_type_cov"] = safe_float(data.get("requestTypeCoverage", {}).get("rate", 0.0), 0.0)
    except Exception as e:
        print(f"[WARN] Failed to read coverage from {reporter_stats}: {e}")

    return cov


def count_lines(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def load_mutation_totals(path: Path) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Load mutation totals keyed by (api, operation).

    Expected columns include (at minimum):
      api,operation,total,survived,killed,invalid,kill_rate

    If any duplicate (api, operation) rows exist, raise RuntimeError.
    """
    if not path.exists():
        raise FileNotFoundError(f"Mutation totals CSV not found: {path}")

    totals: Dict[Tuple[str, str], Dict[str, Any]] = {}

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        required = {"api", "operation", "total", "survived", "killed", "invalid", "kill_rate"}
        if not required.issubset(header):
            raise RuntimeError(
                f"Mutation totals CSV missing required columns. "
                f"required={sorted(required)}, got={sorted(header)}. "
                f"File={path}"
            )

        for i, row in enumerate(reader, start=2):  # header line is 1
            api = (row.get("api") or "").strip()
            operation = (row.get("operation") or "").strip()
            if not api or not operation:
                raise RuntimeError(f"Empty api/operation at line {i} in {path}")

            key = (api, operation)
            if key in totals:
                prev = totals[key]
                raise RuntimeError(
                    "Duplicate (api, operation) detected in mutation totals CSV: "
                    f"{key}. Previous={prev} NewRow(line {i})={row}"
                )

            totals[key] = {
                "total": safe_int(row.get("total"), 0),
                "survived": safe_int(row.get("survived"), 0),
                "killed": safe_int(row.get("killed"), 0),
                "invalid": safe_int(row.get("invalid"), 0),
                "kill_rate": safe_float(row.get("kill_rate"), 0.0),
            }

    return totals


# =============================================================================
# Preload mutation totals
# =============================================================================

mutation_totals = load_mutation_totals(MUTATION_TOTALS_CSV)
print(f"[INFO] Loaded mutation totals: {len(mutation_totals)} rows from {MUTATION_TOTALS_CSV}")


# =============================================================================
# Aggregation structure
# =============================================================================
aggregated: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# Main traversal
# =============================================================================

for api_dir in ROOT.iterdir():
    if not api_dir.is_dir():
        continue

    api_name = api_dir.name

    for op_dir in api_dir.iterdir():
        if not op_dir.is_dir():
            continue

        op_name = op_dir.name

        # Resolve formal operation name from config
        try:
            op_config = _resolve_operation_config(api_name, op_name)
            formal_name = op_config.formal_name
        except Exception as e:
            print(f"[WARN] Failed to resolve op config for {api_name}/{op_name}: {e}")
            formal_name = f"{api_name}-{op_name}"

        # --- 0) Mutants from external summary CSV (keyed by api/op dir names) ---
        mt = mutation_totals.get((api_name, op_name))
        if mt is None:
            total_mutants = 0
            survived_mutants = 0
            killed_mutants = 0
            invalid_mutants = 0
            kill_rate_external = 0.0
        else:
            total_mutants = mt["total"]
            survived_mutants = mt["survived"]
            killed_mutants = mt["killed"]
            invalid_mutants = mt["invalid"]
            kill_rate_external = mt["kill_rate"]

        # --- 1) #schemathesis tests from dumps/*-req.txt ---
        dumps_dir = op_dir / "dumps"
        tests_from_dumps = len(list(dumps_dir.glob("*-req.txt"))) if dumps_dir.is_dir() else 0

        # --- 2) coverage from reporter/stats.json (raw floats) ---
        coverage = read_coverage_stats(op_dir)

        # --- 3) #mutation tests from httpmutator-inputs.jsonl ---
        collected_path = op_dir / "httpmutator-inputs.jsonl"
        tests_from_collected = count_lines(collected_path) if collected_path.is_file() else 0

        # Store only if any signal exists
        if (
            total_mutants > 0
            or tests_from_dumps > 0
            or tests_from_collected > 0
            or any(v > 0 for v in coverage.values())
        ):
            aggregated[formal_name] = {
                "total_mutants": total_mutants,
                "survived_mutants": survived_mutants,
                "killed_mutants": killed_mutants,
                "invalid_mutants": invalid_mutants,
                "kill_rate_external": kill_rate_external,
                "tests_from_dumps": tests_from_dumps,
                "tests_from_collected": tests_from_collected,
                "coverage": coverage,
            }

            print(
                f"[INFO] {formal_name} ({api_name}/{op_name}): "
                f"mutants(total={total_mutants}, survived={survived_mutants}, "
                f"killed={killed_mutants}, invalid={invalid_mutants}, "
                f"kill_rate_external={kill_rate_external}), "
                f"dumps_tests={tests_from_dumps}, collected_tests={tests_from_collected}"
            )


# =============================================================================
# Write summary.csv
# =============================================================================

with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as out_f:
    writer = csv.writer(out_f)

    writer.writerow([
        "op_name",

        # Coverage-related
        "num_schemathesis_tests",   # dumps/*-req.txt
        "param_cov",
        "param_value_cov",
        "status_class_cov",
        "status_cov",
        "request_type_cov",
        "response_type_cov",

        # Mutation-related (tests)
        "num_mutation_tests",       # lines in httpmutator-inputs.jsonl

        # Mutation-related (mutants)
        "total_mutants",
        "valid_mutants",            # total - invalid
        "survived_mutants",
        "killed_mutants",
        "invalid_mutants",
        "kill_rate",                # from external summary CSV (fallback to computed if needed)
        "mutation_score",           # killed / valid_mutants raw float
    ])

    # op_name + 14 columns after it
    empty_cols = 14

    for formal_name in FORMAL_NAME_ORDER:
        vals = aggregated.get(formal_name)

        if vals is None:
            writer.writerow([formal_name] + [""] * empty_cols)
            continue

        total_mutants = vals["total_mutants"]
        survived_mutants = vals["survived_mutants"]
        killed_mutants = vals["killed_mutants"]
        invalid_mutants = vals["invalid_mutants"]

        valid_mutants = total_mutants - invalid_mutants
        mutation_score = (killed_mutants / valid_mutants) if valid_mutants > 0 else 0.0

        # prefer external kill_rate; fallback to computed if missing/zero but denom exists
        kill_rate = safe_float(vals.get("kill_rate_external", 0.0), 0.0)
        if kill_rate == 0.0:
            denom = survived_mutants + killed_mutants
            if denom > 0:
                kill_rate = killed_mutants / denom

        cov = vals["coverage"]

        writer.writerow([
            formal_name,

            vals["tests_from_dumps"],
            cov["param_cov"],
            cov["param_value_cov"],
            cov["status_class_cov"],
            cov["status_cov"],
            cov["request_type_cov"],
            cov["response_type_cov"],

            vals["tests_from_collected"],

            total_mutants,
            valid_mutants,
            survived_mutants,
            killed_mutants,
            invalid_mutants,
            kill_rate,
            mutation_score,
        ])

print(f"[DONE] Summary written to: {SUMMARY_CSV.resolve()}")
