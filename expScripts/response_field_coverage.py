#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Response Field Coverage (OAS vs. observed JSON responses, JSONL input)

- Expects the OAS path EXACTLY as in the spec (no regex/basepath matching).
- Reads a JSONL/NDJSON file where each line is either a raw JSON node or {"body": ...}.
- Computes documented-vs-actual response field coverage aggregated over all lines.

Changes in this version:
- No --media-type argument. The script auto-selects a JSON-like response media type from the OAS
  for the given status (prefers application/json, then application/problem+json, then */*+json).

Outputs:
- Markdown summary to stdout
- coverage_report.csv
- undocumented_fields.csv
- missed_fields.csv
"""

import argparse
import csv
import json
from typing import Dict, List, Optional, Set, Any, Tuple

import yaml
import jsonref
from pathlib import Path

METHODS = {"GET","POST","PUT","DELETE","PATCH","HEAD","OPTIONS","TRACE"}

def normalize_media_type(ct: str) -> str:
    if not ct:
        return ""
    return ct.split(";")[0].strip().lower()

def is_json_media_type(ct: str) -> bool:
    ct = normalize_media_type(ct)
    return ct in ("application/json", "application/problem+json") or ct.endswith("+json")

# ---------------------------
# OpenAPI loader (supports Swagger 2.0 and OpenAPI 3.x)
# ---------------------------

class OpenApi:
    def __init__(self, spec_path: str):
        with open(spec_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        base_uri = "file://" + spec_path
        self.doc = jsonref.replace_refs(raw, base_uri=base_uri)
        self.paths: Dict[str, dict] = self.doc.get("paths", {}) or {}

        # version detection
        self.is_v2 = bool(self.doc.get("swagger") == "2.0")
        # swagger 2.0: global produces/consumes
        self.global_produces = self.doc.get("produces") if self.is_v2 else None
        self.global_consumes = self.doc.get("consumes") if self.is_v2 else None

    def get_operation_by_exact_path(self, path: str, method: str) -> Optional[dict]:
        p = self.paths.get(path)
        if not p:
            return None
        return p.get(method.lower())

    def get_operation_id(self, op: dict, method: str, path: str) -> str:
        return op.get("operationId") or f"{method.upper()} {path}"

    # ---- helpers (v2) ----
    def _response_obj(self, op: dict, status: int) -> Optional[dict]:
        if not op: return None
        responses = op.get("responses") or {}
        return responses.get(str(status)) or responses.get("default")

    def _op_produces(self, op: dict) -> List[str]:
        # Swagger 2.0: produces can be on op or global
        prods = op.get("produces") if isinstance(op, dict) else None
        if not prods:
            prods = self.global_produces or []
        return [normalize_media_type(x) for x in prods if isinstance(x, str)]

    # ---- unified finder for v2 and v3 ----
    def find_json_response_schema_and_type(self, op: dict, status: int) -> Tuple[Optional[dict], Optional[str]]:
        """
        Returns (schema, chosen_media_type) for a JSON-like response of the given status.
        Supports:
          - OpenAPI 3.x: responses[status].content[mediaType].schema
          - Swagger 2.0: responses[status].schema + produces (op/global)
        """
        if self.is_v2:
            r = self._response_obj(op, status)
            if not r:
                return None, None
            schema = r.get("schema")
            if schema is None:
                return None, None

            # choose JSON-like media type from produces (or assume application/json if unspecified)
            prods = self._op_produces(op)
            chosen = None
            # preference: application/json -> application/problem+json -> *+json
            if "application/json" in prods:
                chosen = "application/json"
            elif "application/problem+json" in prods:
                chosen = "application/problem+json"
            else:
                chosen = next((p for p in prods if p.endswith("+json")), None)

            # If produces is missing or empty, many Swagger 2.0 specs still imply JSON
            if not chosen:
                chosen = "application/json"

            # sanity: ensure chosen is JSON-like
            if not is_json_media_type(chosen):
                return None, None

            return schema, chosen

        # OpenAPI 3.x path
        r = self._response_obj(op, status)
        if not r:
            return None, None
        content = (r.get("content") or {})
        if not isinstance(content, dict) or not content:
            return None, None

        # normalize keys once
        keys = {normalize_media_type(k): k for k in content.keys()}

        # preference order
        if "application/json" in keys:
            k = keys["application/json"]
            return content[k].get("schema"), "application/json"
        if "application/problem+json" in keys:
            k = keys["application/problem+json"]
            return content[k].get("schema"), "application/problem+json"
        for norm, original in keys.items():
            if norm.endswith("+json"):
                return content[original].get("schema"), norm

        return None, None

# ---------------------------
# Schema -> documented props
# ---------------------------

def collect_doc_props(schema: dict, base: str, out: Set[str], seen_ids: Set[int]):
    """
    Record documented property paths:
      - objects: add '/prop' and recurse
      - arrays: append '[]' and recurse into items
      - allOf/oneOf/anyOf: union of branches
      - ignore additionalProperties; skip writeOnly:true
    """
    if schema is None:
        return
    sid = id(schema)
    if sid in seen_ids:
        return
    seen_ids.add(sid)

    for sub in schema.get("allOf", []) or []:
        collect_doc_props(sub, base, out, seen_ids)

    for kw in ("oneOf", "anyOf"):
        if isinstance(schema.get(kw), list):
            for sub in schema[kw]:
                collect_doc_props(sub, base, out, seen_ids)

    stype = schema.get("type")
    if not stype:
        if "properties" in schema: stype = "object"
        elif "items" in schema:   stype = "array"

    if stype == "object":
        for name, sub in (schema.get("properties") or {}).items():
            if isinstance(sub, dict) and sub.get("writeOnly") is True:
                continue
            nxt = f"{base}/{name}"
            out.add(nxt)
            collect_doc_props(sub, nxt, out, seen_ids)
    elif stype == "array":
        nxt = f"{base}[]"
        collect_doc_props(schema.get("items"), nxt, out, seen_ids)

# ---------------------------
# Actual JSON -> observed props
# ---------------------------

def collect_actual_props(node: Any, base: str, out: Set[str]):
    """
    Collect actual observed properties.
    A property is considered 'covered' only if its value is not null/empty.
    """
    if node is None:
        return

    if isinstance(node, dict):
        for k, v in node.items():
            nxt = f"{base}/{k}"
            if v not in (None, "", [], {}):
                out.add(nxt)
            collect_actual_props(v, nxt, out)

    elif isinstance(node, list):
        nxt = f"{base}[]"
        for elem in node:
            collect_actual_props(elem, nxt, out)

    else:
        if node not in (None, ""):
            out.add(base)


# ---------------------------
# Aggregation bucket
# ---------------------------

class Bucket:
    __slots__ = ("op_id","status","media_type","all_props","covered_props","undoc_props")
    def __init__(self, op_id: str, status: int, media_type: str):
        self.op_id = op_id
        self.status = status
        self.media_type = media_type
        self.all_props: Set[str] = set()
        self.covered_props: Set[str] = set()
        self.undoc_props: Set[str] = set()

    def coverage(self) -> float:
        return 1.0 if not self.all_props else len(self.covered_props) / len(self.all_props)

# ---------------------------
# JSONL reader
# ---------------------------

def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                raise SystemExit(f"Invalid JSON at line {line_no}: {e}")
            yield obj

def extract_body(obj: Any) -> Any:
    # Accept raw node or {"body": ...}
    if isinstance(obj, dict) and "Body" in obj:
        return obj["Body"]
    return obj

# ---------------------------
# Main
# ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Compute response-field coverage from JSONL bodies vs OpenAPI (auto JSON media type)")
    ap.add_argument("--oas", required=True, help="OpenAPI YAML/JSON file")
    ap.add_argument("--jsonl", required=True, help="NDJSON file; each line is a body node or {'body': ...}")
    ap.add_argument("--method", required=True, help="HTTP method, e.g., GET")
    ap.add_argument("--path", required=True, help="Exact OAS path key, e.g., /v1/items/{id}")
    ap.add_argument("--status", required=True, type=int, help="HTTP status, e.g., 200")
    args = ap.parse_args()

    method = (args.method or "").upper()
    if method not in METHODS:
        raise SystemExit(f"Unsupported method: {args.method}")

    api = OpenApi(args.oas)
    op = api.get_operation_by_exact_path(args.path, method)
    if not op:
        raise SystemExit(f"No OAS operation for {method} {args.path}")
    op_id = api.get_operation_id(op, method, args.path)

    # Auto-pick JSON-like response schema and the chosen media type
    schema, chosen_media_type = api.find_json_response_schema_and_type(op, args.status)
    if not schema or not chosen_media_type:
        raise SystemExit(f"No JSON-like response schema for status={args.status} under {op_id}")

    # Collect documented properties once
    doc_props: Set[str] = set()
    collect_doc_props(schema, "", doc_props, set())

    # Aggregate across all bodies in JSONL
    actual_all: Set[str] = set()
    undoc_all: Set[str]  = set()
    count = 0

    for obj in iter_jsonl(args.jsonl):
        if obj["Status Code"] // 100 != 2:
            continue
        body = extract_body(obj)
        actual_props: Set[str] = set()
        collect_actual_props(body, "", actual_props)
        actual_all |= actual_props
        undoc_all  |= (actual_props - doc_props)
        count += 1

    b = Bucket(op_id, args.status, chosen_media_type)
    b.all_props.update(doc_props)
    b.covered_props.update(actual_all & doc_props)
    b.undoc_props.update(undoc_all)

    # ---- Output ----
    print("| Operation | Status | MediaType | Samples | Covered/Total | Coverage |")
    print("|---|---:|---|---:|---:|---:|")
    cov = f"{len(b.covered_props)}/{len(b.all_props)}"
    pct = f"{b.coverage()*100:.1f}%"
    print(f"| {b.op_id} | {b.status} | {b.media_type} | {count} | {cov} | {pct} |")

    # Output Path
    out_dir = Path(args.jsonl).parent / "resp_prop_coverage"
    if not out_dir.exists():
        out_dir.mkdir()
    cov_rep_file = out_dir / "coverage_report.csv"
    undoc_prop_file = out_dir / "undocumented_properties.csv"
    missed_prop_file = out_dir / "missed_properties.csv"

    # CSVs
    with open(cov_rep_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["operationId","status","mediaType","samples","covered","total","coverage"])
        w.writerow([b.op_id, b.status, b.media_type, count, len(b.covered_props), len(b.all_props), f"{b.coverage():.4f}"])

    with open(undoc_prop_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["operationId","status","mediaType","field"])
        for fld in sorted(b.undoc_props):
            w.writerow([b.op_id, b.status, b.media_type, fld])

    with open(missed_prop_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["operationId","status","mediaType","field"])
        for fld in sorted(b.all_props - b.covered_props):
            w.writerow([b.op_id, b.status, b.media_type, fld])

    print("\nGenerated: coverage_report.csv, undocumented_fields.csv, missed_fields.csv")

if __name__ == "__main__":
    main()
