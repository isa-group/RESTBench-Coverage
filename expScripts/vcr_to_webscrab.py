#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert all VCR-style YAML recordings into per-request WebScrab-style files,
and create a restats-config.json for each operation directory.

For each operation directory:
    dumps/<index>-req.txt  → raw HTTP request
    dumps/<index>-res.txt  → raw HTTP response
    restats-config.json    → configuration for RESTats pipeline

Properties:
    • No filtering (all interactions are converted)
    • Every interaction produces two files (request & response)
    • Numbering starts from 1 in each operation directory
    • Directory structure assumed:
        ./schemathesis-unique-reports/<API>/<Operation>/vcr*.yml
"""

import sys
import json
from pathlib import Path
from urllib.parse import urlparse, unquote

import yaml

from run_evomaster import _resolve_operation_config


BASE_DIR = Path(__file__).parent / "schemathesis-unique-reports"


# --------------------------------------------------------------
# Utility: extract raw text body from VCR body structure
# --------------------------------------------------------------
def get_body_text_from_vcr_body(body):
    """
    VCR bodies follow:
        {"string": "..."} or {"string": b"..."}
    This function extracts and safely decodes the stored text.
    """
    if body is None:
        return ""

    if isinstance(body, dict):
        s = body.get("string", "")
    else:
        s = body

    if isinstance(s, bytes):
        try:
            return s.decode("utf-8", errors="replace")
        except Exception:
            return s.decode("latin-1", errors="replace")

    return s or ""


# --------------------------------------------------------------
# Utility: flatten VCR headers into dict[str, str]
# --------------------------------------------------------------
def flatten_headers(raw_headers):
    """
    Convert VCR header formats into a simple mapping:
        {"Header": ["v1","v2"]}       → "Header": "v1, v2"
        [("Header","v")]              → "Header": "v"
        [{"name":..., "value":...}]   → same
    """
    headers_out = {}

    if isinstance(raw_headers, dict):
        for name, value in raw_headers.items():
            if name == "content-type":
                name = "Content-Type"
            if isinstance(value, list):
                headers_out[name] = ", ".join(str(v) for v in value)
            else:
                headers_out[name] = str(value)

    elif isinstance(raw_headers, list):
        for h in raw_headers:
            if isinstance(h, (list, tuple)) and len(h) == 2:
                headers_out[str(h[0])] = str(h[1])
            elif isinstance(h, dict):
                name = h.get("name")
                value = h.get("value")
                if name is not None:
                    headers_out[str(name)] = str(value)

    return headers_out


# --------------------------------------------------------------
# Convert VCR request → raw HTTP request text
# --------------------------------------------------------------
def vcr_request_to_text(req):
    """
    Produce raw HTTP request text:

        METHOD /path?query HTTP/1.1
        Host: example.com
        Header1: value
        ...

        <body>
    """
    method = (req.get("method") or "GET").upper()
    uri = req.get("uri") or "/"

    parsed = urlparse(uri)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    request_line = f"{method} {path} HTTP/1.1"

    # Flatten headers
    raw_headers = req.get("headers") or {}
    headers = flatten_headers(raw_headers)

    # Add Host header if missing
    host = parsed.netloc
    if host and "host" not in {k.lower() for k in headers.keys()}:
        headers["Host"] = host

    # Body
    body_struct = req.get("body")
    body_text = get_body_text_from_vcr_body(body_struct)
    body_text = unquote(body_text)

    lines = [request_line]

    for name, value in headers.items():
        lines.append(f"{name}: {value}")

    lines.append("\r")

    if body_text:
        lines.append(body_text)

    lines.append("")  # end with newline
    return "\n".join(lines)


# --------------------------------------------------------------
# Convert VCR response → raw HTTP response text
# --------------------------------------------------------------
def vcr_response_to_text(resp):
    """
    Produce raw HTTP response text:

        HTTP/1.1 200 OK
        Header1: value
        ...

        <body>
    """
    status = resp.get("status") or {}
    code = status.get("code")
    message = status.get("message") or ""

    try:
        code_str = str(int(code))
    except Exception:
        code_str = str(code)

    status_line = f"HTTP/1.1 {code_str} {message}"

    raw_headers = resp.get("headers") or {}
    headers = flatten_headers(raw_headers)

    body_struct = resp.get("body")
    body_text = get_body_text_from_vcr_body(body_struct)
    body_text = unquote(body_text)

    lines = [status_line]

    for name, value in headers.items():
        lines.append(f"{name}: {value}")

    lines.append("\r")

    if body_text:
        lines.append(body_text)

    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------
# Process a single vcr*.yml file
# --------------------------------------------------------------
def process_vcr_file(vcr_file: Path, dumps_dir: Path, start_index: int) -> int:
    """
    Convert all http_interactions in one VCR file into:
        dumps/<index>-req.txt
        dumps/<index>-res.txt

    Returns the next available index.
    """
    with vcr_file.open("r", encoding="utf-8") as f:
        vcr_data = yaml.safe_load(f) or {}

    interactions = vcr_data.get("http_interactions", [])
    idx = start_index

    for interaction in interactions:
        req = interaction.get("request") or {}
        resp = interaction.get("response") or {}

        req_text = vcr_request_to_text(req)
        res_text = vcr_response_to_text(resp)

        (dumps_dir / f"{idx}-req.txt").write_text(req_text, encoding="utf-8")
        (dumps_dir / f"{idx}-res.txt").write_text(res_text, encoding="utf-8")

        idx += 1

    return idx


# --------------------------------------------------------------
# Create restats-config.json for a given operation directory
# --------------------------------------------------------------
def create_restats_config(api_name: str, op_name: str, op_dir: Path, dumps_dir: Path):
    """
    Build and write restats-config.json in op_dir with the structure:

    {
        "modules": "all",
        "specification": <from op_config.resloved_oas()>,
        "dumpsDir": <absolute path to dumps_dir>,
        "reportsDir": <absolute path to reports_dir>,
        "dbPath": <absolute path to database.sqlite>
    }
    """
    op_config = _resolve_operation_config(api_name, op_name)

    specification_path = op_config.resolved_oas()

    # Paths inside this operation directory
    dumps_abs = str(dumps_dir.resolve())
    reports_dir = op_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    reports_abs = str(reports_dir.resolve())
    db_path = op_dir / "database.sqlite"
    db_abs = str(db_path.resolve())

    cfg = {
        "modules": "all",
        "specification": specification_path,
        "dumpsDir": dumps_abs,
        "reportsDir": reports_abs,
        "dbPath": db_abs,
    }

    config_file = op_dir / "restats-config.json"
    with config_file.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)
    print(f"  Created restats-config.json at {config_file}")


# --------------------------------------------------------------
# Main traversal logic
# --------------------------------------------------------------
def main():
    if not BASE_DIR.exists():
        print(f"[ERROR] Base directory does not exist: {BASE_DIR}")
        sys.exit(1)

    print(f"Scanning base directory: {BASE_DIR}")

    total_pairs = 0

    for api_dir in sorted(BASE_DIR.iterdir()):
        if not api_dir.is_dir():
            continue

        api_name = api_dir.name

        for op_dir in sorted(api_dir.iterdir()):
            if not op_dir.is_dir():
                continue

            op_name = op_dir.name

            vcr_files = sorted(
                [p for p in op_dir.iterdir()
                 if p.is_file() and p.name.startswith("vcr")]
            )

            if not vcr_files:
                print(f"[INFO] No VCR files in {op_dir}")
                continue

            # Create dumps/ folder inside op_dir
            dumps_dir = op_dir / "dumps"
            dumps_dir.mkdir(exist_ok=True)

            print(f"Processing: API={api_name}, OP={op_name}")
            idx = 1  # numbering starts at 1

            for vcr_file in vcr_files:
                print(f"  VCR: {vcr_file.name}")
                idx = process_vcr_file(vcr_file, dumps_dir, idx)

            generated = idx - 1
            total_pairs += generated
            print(f"  Generated {generated} request/response pairs into {dumps_dir}")

            # Create restats-config.json for this operation
            # create_restats_config(api_name, op_name, op_dir, dumps_dir)

    print(f"\nDone. Total pairs generated: {total_pairs}")


if __name__ == "__main__":
    main()