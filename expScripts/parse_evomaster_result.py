#!/usr/bin/env python3
"""
RQ3 (EvoMaster) Aggregation Script — Raw Metrics Version
========================================================

This script aggregates per-operation EvoMaster results under two configurations:

- EMON  : EvoMaster with basic assertions
- EMOFF : EvoMaster without basic assertions

IMPORTANT:
- This script intentionally DOES NOT format numeric values.
- All mutation scores and coverage rates are written as raw floats.
- The resulting CSV files are intermediate artifacts intended for
  further computation and formatting in downstream Jupyter notebooks.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from collections import defaultdict

from run_evomaster import _resolve_operation_config
from op_configs import SCRIPT_DIR


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DEFAULT_RESOURCES_ROOT = (
    SCRIPT_DIR.parent / "httpmutator-rq3" / "src" / "test" / "resources"
)

FORMAL_OPERATION_ORDER: List[str] = [
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

# Folder name -> logical config label
CONFIG_DIR_TO_LABEL = {
    "withBasicAssertions": "EMON",
    "withoutBasicAssertions": "EMOFF",
}

REQUEST_GROUPS = ("successes", "faults", "others")


# ---------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------

@dataclass
class GroupSummary:
    test_case_count: int = 0
    total_mutants: int = 0
    killed_mutants: int = 0
    mutation_score: float = 0.0


@dataclass
class CoverageMetrics:
    parameter_value_coverage: Optional[float] = None
    parameter_coverage: Optional[float] = None
    status_class_coverage: Optional[float] = None
    status_coverage: Optional[float] = None
    responseTypeCoverage: Optional[float] = None
    requestTypeCoverage: Optional[float] = None


@dataclass
class OperationConfigStats:
    successes: GroupSummary = field(default_factory=GroupSummary)
    faults: GroupSummary = field(default_factory=GroupSummary)
    others: GroupSummary = field(default_factory=GroupSummary)
    coverage: CoverageMetrics = field(default_factory=CoverageMetrics)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def safe_int(v, default=0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


# ---------------------------------------------------------------------
# Parsing logic
# ---------------------------------------------------------------------

def parse_assert_summary(csv_path: Path) -> Optional[GroupSummary]:
    if not csv_path.exists():
        return None

    with csv_path.open(newline="") as f:
        rows = [
            r for r in csv.DictReader(f)
            if r.get("status") != "DISCARDED_NO_ASSERTIONS"
        ]

    if not rows:
        return None

    tc = sum(1 for r in rows if r.get("label") not in (None, "SUMMARY"))

    summary = next((r for r in rows if r.get("label") == "SUMMARY"), None)
    if summary is None:
        return GroupSummary(test_case_count=tc)

    total = safe_int(summary.get("totalMutants"))
    killed = safe_int(summary.get("killedMutants"))

    ms_raw = summary.get("overallMutationScore")
    score = safe_float(ms_raw) if ms_raw else (
        killed / total if total > 0 else 0.0
    )

    return GroupSummary(
        test_case_count=tc,
        total_mutants=total,
        killed_mutants=killed,
        mutation_score=score,
    )


def parse_coverage(stats_json: Path) -> Optional[CoverageMetrics]:
    if not stats_json.exists():
        return None

    with stats_json.open() as f:
        d = json.load(f)

    return CoverageMetrics(
        parameter_value_coverage=d.get("parameterValueCoverage", {}).get("rate"),
        parameter_coverage=d.get("parameterCoverage", {}).get("rate"),
        status_class_coverage=d.get("statusClassCoverage", {}).get("rate"),
        status_coverage=d.get("statusCoverage", {}).get("rate"),
        responseTypeCoverage=d.get("responseTypeCoverage", {}).get("rate"),
        requestTypeCoverage=d.get("requestTypeCoverage", {}).get("rate")
    )


# ---------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------

def collect_stats(root: Path) -> Dict[Tuple[str, str], OperationConfigStats]:
    stats = defaultdict(OperationConfigStats)

    for op_dir in root.iterdir():
        if not op_dir.is_dir():
            continue

        try:
            api, op = op_dir.name.split("-")
        except ValueError:
            continue

        try:
            formal = _resolve_operation_config(api, op).formal_name
        except Exception:
            formal = op_dir.name

        for cfg_dir, cfg_label in CONFIG_DIR_TO_LABEL.items():
            entry = stats[(formal, cfg_label)]

            for group in REQUEST_GROUPS:
                parsed = parse_assert_summary(
                    op_dir / cfg_dir / f"{group}-assert-summary.csv"
                )
                if parsed:
                    setattr(entry, group, parsed)

            cov = parse_coverage(op_dir / cfg_dir / "reporter" / "stats.json")
            if cov:
                entry.coverage = cov

    return stats


# ---------------------------------------------------------------------
# CSV writers (RAW numeric values)
# ---------------------------------------------------------------------

def write_aggregated_csv(root: Path, stats: Dict[Tuple[str, str], OperationConfigStats]) -> None:
    out = root / "rq3-assert-summary-aggregated.csv"

    fields = [
        "operation",
        "config",
        "successes_tc",
        "successes_total_mutants",
        "successes_killed_mutants",
        "successes_mutation_score",
        "faults_tc",
        "faults_total_mutants",
        "faults_killed_mutants",
        "faults_mutation_score",
        "others_tc",
        "others_total_mutants",
        "others_killed_mutants",
        "others_mutation_score",
        "overall_total_mutants",
        "overall_killed_mutants",
        "overall_mutation_score",
        "param_cov",
        "param_value_cov",
        "status_class_cov",
        "status_cov",
        "request_type_cov",
        "response_type_cov"
    ]

    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()

        for (op, cfg), e in stats.items():
            total = e.successes.total_mutants + e.faults.total_mutants + e.others.total_mutants
            killed = e.successes.killed_mutants + e.faults.killed_mutants + e.others.killed_mutants
            score = killed / total if total > 0 else 0.0

            w.writerow({
                "operation": op,
                "config": cfg,
                "successes_tc": e.successes.test_case_count,
                "successes_total_mutants": e.successes.total_mutants,
                "successes_killed_mutants": e.successes.killed_mutants,
                "successes_mutation_score": e.successes.mutation_score,
                "faults_tc": e.faults.test_case_count,
                "faults_total_mutants": e.faults.total_mutants,
                "faults_killed_mutants": e.faults.killed_mutants,
                "faults_mutation_score": e.faults.mutation_score,
                "others_tc": e.others.test_case_count,
                "others_total_mutants": e.others.total_mutants,
                "others_killed_mutants": e.others.killed_mutants,
                "others_mutation_score": e.others.mutation_score,
                "overall_total_mutants": total,
                "overall_killed_mutants": killed,
                "overall_mutation_score": score,
                "param_cov": e.coverage.parameter_coverage,
                "param_value_cov": e.coverage.parameter_value_coverage,
                "status_class_cov": e.coverage.status_class_coverage,
                "status_cov": e.coverage.status_coverage,
                "request_type_cov": e.coverage.requestTypeCoverage,
                "response_type_cov": e.coverage.responseTypeCoverage
            })

    print(f"[OK] Raw aggregated CSV written to {out}")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    if not DEFAULT_RESOURCES_ROOT.exists():
        raise FileNotFoundError(
            f"Resources root does not exist: {DEFAULT_RESOURCES_ROOT}"
        )

    stats = collect_stats(DEFAULT_RESOURCES_ROOT)
    write_aggregated_csv(DEFAULT_RESOURCES_ROOT, stats)


if __name__ == "__main__":
    main()
